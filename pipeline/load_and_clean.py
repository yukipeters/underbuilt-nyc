"""
Load and clean the raw PLUTO CSV.

Key quirks in this dataset:
- BBL is an integer, converted to string here
- lotarea is a comma-formatted string (e.g. "2,660"), needs parsing
"""
import pandas as pd
from pathlib import Path

COLUMNS = [
    "BBL",
    "address",
    "borough",
    "lotarea",
    "builtfar",
    "residfar",
    "zonedist1",
    "unitsres",
    "landuse",
    "numbldgs",
    "bldgclass",
    "yearbuilt",
    "latitude",
    "longitude",
]


def load_and_clean(pluto_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(pluto_path, usecols=COLUMNS, low_memory=False)

    # Normalize column names
    df = df.rename(columns={
        "BBL": "bbl",
        "lotarea": "lot_area",
        "builtfar": "built_far",
        "residfar": "allowed_far",
        "zonedist1": "zoning_district",
        "unitsres": "residential_units",
        "landuse": "land_use",
        "numbldgs": "num_bldgs",
        "bldgclass": "bldg_class",
        "yearbuilt": "year_built",
    })

    df["bbl"] = df["bbl"].astype(str)
    df["lot_area"] = pd.to_numeric(df["lot_area"].astype(str).str.replace(",", ""), errors="coerce")
    df["num_bldgs"] = pd.to_numeric(df["num_bldgs"].astype(str).str.replace(",", ""), errors="coerce").fillna(0).astype(int)

    # Drop rows missing anything we need for the core calculation
    df = df.dropna(subset=["lot_area", "built_far", "allowed_far", "zoning_district"])
    df = df[df["lot_area"] > 0]

    return df.reset_index(drop=True)
