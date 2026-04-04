"""
Run the full underbuilt pipeline.

Usage:
    python -m pipeline.run
    python -m pipeline.run --pluto data/pluto_nyc_raw.csv --output data/underbuilt.parquet
"""
import argparse
from pathlib import Path

from pipeline.load_and_clean import load_and_clean
from pipeline.compute_underbuilt import compute_underbuilt, write_output

DEFAULT_PLUTO = Path("data/pluto_nyc_raw.csv")
DEFAULT_OUTPUT = Path("data/underbuilt.parquet")


def run(pluto_path: Path, output_path: Path) -> None:
    print(f"Loading {pluto_path} ...")
    df = load_and_clean(pluto_path)
    print(f"  Loaded {len(df):,} lots after initial cleaning")

    print("Computing underbuilt metrics ...")
    result = compute_underbuilt(df)
    print(f"  {len(result):,} underbuilt lots found")

    write_output(result, output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the underbuilt-nyc pipeline")
    parser.add_argument("--pluto", type=Path, default=DEFAULT_PLUTO)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    run(args.pluto, args.output)
