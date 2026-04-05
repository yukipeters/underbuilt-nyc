# underbuilt-nyc

A public-facing advocacy and research tool that identifies NYC tax lots that appear underbuilt relative to their zoning. Built to support housing advocates, planners, researchers, and anyone interested in expanding NYC's housing supply. It is an approximate signal detector, not a legal buildability engine. Results are candidates for further review, not confirmed development opportunities.

## How it works

1. **Pipeline** reads NYC's PLUTO dataset, computes unused floor area for each residential lot, and writes a Parquet file.
2. **Backend** loads the Parquet file at startup and serves it via a read-only REST API.
3. **Frontend** provides address search, filters, and a sortable table with ZoLa links.

### Methodology

```
allowed_far   = residfar from PLUTO (allowed residential FAR)
unused_far    = max(allowed_far - built_far, 0)
unused_sqft   = unused_far × lot_area
est_add_units = floor(unused_sqft / 700)
```

Lots are excluded if they are:
- Non-residential land use (parks, parking, utilities, etc.)
- Condo lots (bldgclass prefix `R`) — tax lot boundaries often include parking/open space, deflating apparent FAR
- Multi-building lots (`numbldgs > 1`) — large cooperatives recorded as a single tax lot have artificially low built FAR
- Superblock-scale parcels (`lotarea > 100,000 sqft`) — FAR math breaks down at campus scale
- Negligible capacity (`unused_sqft < 500` or `est_add_units < 1`)

> **Caveats:** Estimates only, not legal advice. Zoning is simplified — special districts, overlays, bonuses, and lot-specific constraints are not modeled. Results are candidates for further review.

## Setup

Requires Python 3.12+.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data

Download the PLUTO CSV from the [NYC Department of City Planning](https://www.nyc.gov/site/planning/data-maps/open-data/dwn-pluto-mappluto.page) and place it at `data/pluto_nyc_raw.csv`. The file is large (~100MB) and is excluded from git.

## Pipeline

```sh
python -m pipeline.run
# or with explicit paths:
python -m pipeline.run --pluto data/pluto_nyc_raw.csv --output data/underbuilt.parquet
```

Outputs `data/underbuilt.parquet` — the full filtered dataset consumed by the backend.

## Backend

```sh
uvicorn backend.main:app --reload
```

Swagger UI available at `http://localhost:8000/docs`.

### API endpoints

| Endpoint | Description |
|---|---|
| `GET /api/health` | Liveness check, returns row count |
| `GET /api/stats` | Total lots, total est. additional units, per-borough breakdown |
| `GET /api/lots` | Filterable, sortable, paginated lot list |
| `GET /api/lots/{bbl}` | Single lot by BBL, 404 if not found |

**`GET /api/lots` parameters:**

| Parameter | Type | Description |
|---|---|---|
| `borough` | string | Filter by borough code: `BK`, `BX`, `MN`, `QN`, `SI` |
| `min_unused_far` | float | Minimum unused FAR |
| `min_est_units` | int | Minimum estimated additional units |
| `q` | string | Case-insensitive substring match on address |
| `sort_by` | string | Column to sort by (default: `est_add_units`) |
| `sort_dir` | `asc`\|`desc` | Sort direction (default: `desc`) |
| `limit` | int | Max results, up to 1000 (default: 100) |
| `offset` | int | Pagination offset |

## Frontend

```sh
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:3000`. Proxies `/api/*` to the backend — set `BACKEND_URL` to point at a non-local backend (default: `http://localhost:8000`).

## Architecture

```
/pipeline   Python/Pandas ETL
/backend    FastAPI, loads Parquet at startup, no database
/frontend   Next.js
/data       Raw PLUTO CSV (gitignored) and pipeline outputs
```
