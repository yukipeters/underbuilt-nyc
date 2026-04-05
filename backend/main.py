"""
underbuilt-nyc FastAPI backend.

Loads data/underbuilt.parquet at startup and serves it read-only.

Run with:
    uvicorn backend.main:app --reload
"""
from pathlib import Path

import pandas as pd
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from typing import Literal

PARQUET_PATH = Path("data/underbuilt.parquet")

_df: pd.DataFrame | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _df
    _df = pd.read_parquet(PARQUET_PATH)
    yield


app = FastAPI(title="underbuilt-nyc", lifespan=lifespan)


def get_df() -> pd.DataFrame:
    if _df is None:
        raise RuntimeError("Data not loaded")
    return _df


@app.get("/api/health")
def health() -> dict:
    """Liveness check. Returns row count of the loaded dataset."""
    return {"status": "ok", "rows": len(get_df())}


@app.get("/api/stats")
def stats() -> dict:
    """Aggregate stats: total lots, total estimated additional units, and a per-borough breakdown."""
    df = get_df()
    by_borough = (
        df.groupby("borough")
        .agg(lots=("bbl", "count"), est_add_units=("est_add_units", "sum"))
        .reset_index()
        .to_dict(orient="records")
    )
    return {
        "total_lots": len(df),
        "total_est_add_units": int(df["est_add_units"].sum()),
        "by_borough": by_borough,
    }


SORTABLE_COLUMNS = {
    "address", "borough", "zoning_district", "owner_type",
    "built_far", "allowed_far", "unused_far", "lot_area",
    "est_add_units", "year_built",
}


@app.get("/api/lots")
def lots(
    borough: str | None = None,
    min_unused_far: float | None = None,
    min_est_units: int | None = None,
    q: str | None = None,
    sort_by: str = "est_add_units",
    sort_dir: Literal["asc", "desc"] = "desc",
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
) -> dict:
    """
    List underbuilt lots.

    - **borough**: filter by borough code (BK, BX, MN, QN, SI)
    - **min_unused_far**: minimum unused FAR
    - **min_est_units**: minimum estimated additional units
    - **q**: case-insensitive substring match on address
    - **sort_by**: column to sort by (default: est_add_units)
    - **sort_dir**: asc or desc (default: desc)
    - **limit**: max results to return (default 100, max 1000)
    - **offset**: pagination offset
    """
    if sort_by not in SORTABLE_COLUMNS:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by column: {sort_by}")

    df = get_df()

    if borough:
        df = df[df["borough"].str.upper() == borough.upper()]
    if min_unused_far is not None:
        df = df[df["unused_far"] >= min_unused_far]
    if min_est_units is not None:
        df = df[df["est_add_units"] >= min_est_units]
    if q:
        # PLUTO addresses are all-caps; q.upper() normalizes user input to match.
        # If the pipeline ever lowercases addresses, also add .str.upper() on the column side.
        df = df[df["address"].str.contains(q.upper(), na=False, regex=False)]

    df = df.sort_values(sort_by, ascending=(sort_dir == "asc"), na_position="last")

    total = len(df)
    page = df.iloc[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "lots": page.to_dict(orient="records"),
    }


@app.get("/api/lots/{bbl}")
def lot_by_bbl(bbl: str) -> dict:
    """Return a single lot by BBL (Borough-Block-Lot identifier)."""
    df = get_df()
    row = df[df["bbl"] == bbl]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"BBL {bbl} not found")
    return row.iloc[0].to_dict()
