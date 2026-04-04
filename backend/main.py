"""
underbuilt-nyc FastAPI backend.

Loads data/underbuilt.parquet at startup and serves it read-only.

Run with:
    uvicorn backend.main:app --reload
"""
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Query

PARQUET_PATH = Path("data/underbuilt.parquet")

app = FastAPI(title="underbuilt-nyc")

_df: pd.DataFrame | None = None


@app.on_event("startup")
def load_data() -> None:
    global _df
    _df = pd.read_parquet(PARQUET_PATH)


def get_df() -> pd.DataFrame:
    assert _df is not None, "Data not loaded"
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


@app.get("/api/lots")
def lots(
    borough: str | None = None,
    min_unused_far: float | None = None,
    min_est_units: int | None = None,
    q: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
) -> dict:
    """
    List underbuilt lots, sorted by estimated additional units descending.

    - **borough**: filter by borough code (BK, BX, MN, QN, SI)
    - **min_unused_far**: minimum unused FAR
    - **min_est_units**: minimum estimated additional units
    - **q**: case-insensitive substring match on address
    - **limit**: max results to return (default 100, max 1000)
    - **offset**: pagination offset
    """
    df = get_df()

    if borough:
        df = df[df["borough"].str.upper() == borough.upper()]
    if min_unused_far is not None:
        df = df[df["unused_far"] >= min_unused_far]
    if min_est_units is not None:
        df = df[df["est_add_units"] >= min_est_units]
    if q:
        df = df[df["address"].str.contains(q.upper(), na=False)]

    total = len(df)
    page = df.iloc[offset : offset + limit]

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "lots": page.to_dict(orient="records"),
    }
