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
