"""
underbuilt-nyc FastAPI backend.

Loads data/underbuilt.parquet at startup and serves it read-only.

Run with:
    uvicorn backend.main:app --reload
"""
from pathlib import Path

import pandas as pd
from fastapi import FastAPI

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
    return {"status": "ok", "rows": len(get_df())}


@app.get("/api/stats")
def stats() -> dict:
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
