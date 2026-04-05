"""
Compute underbuilt metrics and write final dataset.

Methodology:
  allowed_far     = residfar from PLUTO (allowed residential FAR)
  unused_far      = max(allowed_far - built_far, 0)
  unused_sqft     = unused_far * lot_area
  est_add_units   = unused_sqft / AVG_UNIT_SIZE_SQFT

Lots are excluded if:
  - unused_sqft < MIN_UNUSED_SQFT
  - est_add_units < MIN_EST_UNITS
  - land_use not in RESIDENTIAL_LAND_USES
"""
import pandas as pd
from pathlib import Path

AVG_UNIT_SIZE_SQFT = 700
MIN_UNUSED_SQFT = 500
MIN_EST_UNITS = 1

# Condo lots (bldgclass prefix "R") have unreliable builtfar in PLUTO — the tax lot
# boundary often includes parking and open space, deflating the apparent FAR.
EXCLUDE_BLDGCLASS_PREFIXES = {"R"}

# Lots with multiple buildings are large cooperative/condo campuses recorded as a single
# tax lot (e.g. Breezy Point, Rochdale Village, Parkchester). Their built_far is
# artificially low relative to lot_area, making them appear underbuilt. Exclude them.
MAX_NUMBLDGS = 1

# Lots above this area (sq ft) are superblock-scale parcels where FAR math is unreliable.
# 100,000 sq ft ≈ 2.3 acres — a reasonable ceiling for an individual infill lot.
MAX_LOT_AREA = 100_000

# PLUTO land use codes to include. Others (parks, parking, utilities, etc.) are excluded.
# 1 = 1-2 family residential
# 2 = multi-family walkup
# 3 = multi-family elevator
# 4 = mixed residential/commercial
RESIDENTIAL_LAND_USES = {1, 2, 3, 4}


def compute_underbuilt(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["unused_far"] = (df["allowed_far"] - df["built_far"]).clip(lower=0)
    df["unused_sqft"] = df["unused_far"] * df["lot_area"]
    df["est_add_units"] = (df["unused_sqft"] / AVG_UNIT_SIZE_SQFT).astype(int)  # truncates (intentional: conservative estimate)

    df = df[df["land_use"].isin(RESIDENTIAL_LAND_USES)]
    df = df[df["bldg_class"].notna() & ~df["bldg_class"].str[0].isin(EXCLUDE_BLDGCLASS_PREFIXES)]
    df = df[df["num_bldgs"] <= MAX_NUMBLDGS]
    df = df[df["lot_area"] <= MAX_LOT_AREA]
    df = df[df["unused_sqft"] >= MIN_UNUSED_SQFT]
    df = df[df["est_add_units"] >= MIN_EST_UNITS]

    df = df.sort_values("est_add_units", ascending=False).reset_index(drop=True)

    return df


def write_output(df: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    df.to_parquet(output_path, index=False)
    print(f"Wrote {len(df):,} rows to {output_path}")
