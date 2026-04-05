# underbuilt-nyc

## What this is

A public civic web app that identifies NYC tax lots that appear underbuilt relative to their zoning. It is an approximate signal detector, not a legal buildability engine. Results should be treated as candidate opportunities for further review, not legal advice.

## Architecture

- **Pipeline** (`/pipeline`): Python/Pandas ETL. Reads raw PLUTO CSV, computes underbuilt metrics, writes a Parquet dataset.
- **Backend** (`/backend`): FastAPI. Loads Parquet at startup, serves read-only API. No database.
- **Frontend** (`/frontend`): Next.js. Table + search + filter UI. No map in v1.
- **Data** (`/data`): Raw PLUTO CSV lives here. Ignored by git (too large).

## Environment

- Python venv at `.venv/`. Activate with `source .venv/bin/activate`.
- Dependencies: `pandas`, `pyarrow`, `fastapi`, `uvicorn` (see `requirements.txt`).

## Pipeline

### Core methodology

```
allowed_far   = residfar from PLUTO (allowed residential FAR — used directly, not a hardcoded lookup)
unused_far    = max(allowed_far - built_far, 0)
unused_sqft   = unused_far * lot_area
est_add_units = unused_sqft / AVG_UNIT_SIZE_SQFT (default 700 sqft)
```

### Key constants (pipeline/compute_underbuilt.py)

| Constant | Value | Reason |
|---|---|---|
| `AVG_UNIT_SIZE_SQFT` | 700 | Assumed average unit size |
| `MIN_UNUSED_SQFT` | 500 | Filter out negligible capacity |
| `MIN_EST_UNITS` | 1 | Filter out sub-unit remainder |
| `MAX_NUMBLDGS` | 1 | Exclude multi-building campuses (Breezy Point, Rochdale Village, etc.) |
| `MAX_LOT_AREA` | 100,000 sqft | Exclude superblock-scale lots where FAR math breaks down |
| `EXCLUDE_BLDGCLASS_PREFIXES` | `{"R"}` | Exclude condo lots — unreliable builtfar in PLUTO |
| `RESIDENTIAL_LAND_USES` | `{1, 2, 3, 4}` | 1=1-2fam, 2=MF walkup, 3=MF elevator, 4=mixed res/commercial |

### Why these filters exist

- **`MAX_NUMBLDGS > 1`**: Large cooperatives and housing projects (e.g. Breezy Point Cooperative with 1,863 buildings, Rochdale Village with 28 buildings) are recorded as a single tax lot. Their built_far is artificially low relative to lot_area.
- **`MAX_LOT_AREA`**: Same problem at the parcel scale — campus-sized lots make FAR math unreliable.
- **R-prefix bldgclass**: Condo tax lot boundaries often include parking and open space, deflating apparent FAR. 300 Cathedral Parkway (342-unit high-rise) showed built_far=2.62 in a FAR-10 zone due to this.
- **K-class (retail) lots are intentionally kept**: K4 (drive-in retail/strip malls) on land_use=4 (mixed res/commercial) are genuine underbuilt candidates — low-slung retail in high-FAR zones.

### PLUTO column mapping

| Raw PLUTO | Pipeline name |
|---|---|
| BBL | bbl |
| lotarea | lot_area |
| builtfar | built_far |
| residfar | allowed_far |
| zonedist1 | zoning_district |
| unitsres | residential_units |
| landuse | land_use |
| numbldgs | num_bldgs |
| bldgclass | bldg_class |
| yearbuilt | year_built |
| ownertype | owner_type |

### Output

- `data/underbuilt.parquet` — full filtered dataset for backend consumption
- `data/top100.csv` — top 100 by est_add_units for manual spot-checking

## Backend API

Run with `uvicorn backend.main:app --reload`. Swagger UI at `/docs`.

- `GET /api/health` — liveness check, returns row count
- `GET /api/stats` — total lots, total est_add_units, per-borough breakdown
- `GET /api/lots` — filterable by `borough`, `min_unused_far`, `min_est_units`, `q` (address search); paginated via `limit`/`offset`
- `GET /api/lots/{bbl}` — single lot by BBL, 404 if not found

## Planned frontend (not yet built)

- Title + methodology/caveat text
- Address search box
- Filters: borough, min unused FAR, min est. additional units
- Sortable table: address, borough, zoning district, built FAR, allowed FAR, unused FAR, lot area, est. add units, BBL
- Link out to ZoLa for each lot

## Caveats (must appear in UI and README)

- Estimates only, not legal advice
- Zoning is simplified — special districts, overlays, bonuses, lot-specific constraints are not modeled
- Uses residfar from PLUTO directly as allowed FAR proxy
- Results are candidates for further review, not confirmed development opportunities
