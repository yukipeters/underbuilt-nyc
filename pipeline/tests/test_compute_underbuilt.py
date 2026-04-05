import pandas as pd
import pytest

from pipeline.compute_underbuilt import (
    AVG_UNIT_SIZE_SQFT,
    MAX_LOT_AREA,
    MAX_NUMBLDGS,
    MIN_EST_UNITS,
    MIN_UNUSED_SQFT,
    compute_underbuilt,
)


def make_lot(**overrides) -> dict:
    """Return a valid underbuilt lot dict, with optional overrides."""
    base = {
        "bbl": "1000010001",
        "address": "123 MAIN ST",
        "borough": "MN",
        "lot_area": 5000,
        "built_far": 1.0,
        "allowed_far": 6.0,
        "zoning_district": "R7-2",
        "residential_units": 4,
        "land_use": 1,
        "num_bldgs": 1,
        "bldg_class": "A5",
        "year_built": 1920,
        "owner_type": None,
        "latitude": 40.7,
        "longitude": -74.0,
    }
    base.update(overrides)
    return base


def make_df(lots: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(lots)


# --- Metric calculations ---


def test_unused_far_calculated():
    df = make_df([make_lot(built_far=2.0, allowed_far=6.0)])
    result = compute_underbuilt(df)
    assert result.iloc[0]["unused_far"] == 4.0


def test_unused_far_clipped_to_zero():
    """Overbuilt lots (built > allowed) should get unused_far=0, then be filtered out."""
    df = make_df([make_lot(built_far=8.0, allowed_far=6.0)])
    result = compute_underbuilt(df)
    assert len(result) == 0


def test_unused_sqft():
    df = make_df([make_lot(built_far=1.0, allowed_far=3.0, lot_area=1000)])
    result = compute_underbuilt(df)
    assert result.iloc[0]["unused_sqft"] == 2000.0


def test_est_add_units_truncates():
    """est_add_units should truncate (floor), not round."""
    # unused_far=2.0, lot_area=1000 => unused_sqft=2000 => 2000/700=2.857 => 2
    df = make_df([make_lot(built_far=1.0, allowed_far=3.0, lot_area=1000)])
    result = compute_underbuilt(df)
    assert result.iloc[0]["est_add_units"] == 2


def test_sorted_by_est_add_units_desc():
    lots = [
        make_lot(bbl="1", lot_area=2000, allowed_far=6.0),
        make_lot(bbl="2", lot_area=10000, allowed_far=6.0),
        make_lot(bbl="3", lot_area=5000, allowed_far=6.0),
    ]
    result = compute_underbuilt(make_df(lots))
    assert list(result["bbl"]) == ["2", "3", "1"]


# --- Filters ---


def test_excludes_non_residential_land_use():
    df = make_df([make_lot(land_use=5)])  # 5 = hotel
    assert len(compute_underbuilt(df)) == 0


def test_includes_all_residential_land_uses():
    lots = [make_lot(bbl=str(lu), land_use=lu) for lu in [1, 2, 3, 4]]
    result = compute_underbuilt(make_df(lots))
    assert len(result) == 4


def test_excludes_condo_bldg_class():
    df = make_df([make_lot(bldg_class="R4")])
    assert len(compute_underbuilt(df)) == 0


def test_excludes_null_bldg_class():
    df = make_df([make_lot(bldg_class=None)])
    assert len(compute_underbuilt(df)) == 0


def test_excludes_multi_building_lots():
    df = make_df([make_lot(num_bldgs=MAX_NUMBLDGS + 1)])
    assert len(compute_underbuilt(df)) == 0


def test_excludes_superblock_lots():
    df = make_df([make_lot(lot_area=MAX_LOT_AREA + 1)])
    assert len(compute_underbuilt(df)) == 0


def test_excludes_below_min_unused_sqft():
    # allowed_far=1.1, built_far=1.0 => unused_far=0.1, lot_area=1000 => unused_sqft=100 < 500
    df = make_df([make_lot(allowed_far=1.1, built_far=1.0, lot_area=1000)])
    assert len(compute_underbuilt(df)) == 0


def test_excludes_below_min_est_units():
    # unused_sqft just above MIN_UNUSED_SQFT but est_add_units < 1 after truncation
    # unused_far=0.2, lot_area=3000 => unused_sqft=600 => 600/700=0.857 => 0 units
    df = make_df([make_lot(allowed_far=1.2, built_far=1.0, lot_area=3000)])
    assert len(compute_underbuilt(df)) == 0


def test_valid_lot_passes_all_filters():
    df = make_df([make_lot()])
    result = compute_underbuilt(df)
    assert len(result) == 1


def test_does_not_mutate_input():
    df = make_df([make_lot()])
    original_cols = set(df.columns)
    compute_underbuilt(df)
    assert set(df.columns) == original_cols
    assert "unused_far" not in df.columns
