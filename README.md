# FastAPI + PostGIS + Alembic (Docker)

A minimal, production-leaning FastAPI service that stores point “features”, buffers them into polygons (“footprints”) with **PostGIS**, and queries nearby features. Migrations run automatically at container start (dev convenience) and tests verify the full flow.

---

## Contents

- [Architecture](#architecture)
- [Prereqs](#prereqs)
- [Project structure](#project-structure)
- [Environment (.env)](#environment-env)
- [Running (Docker)](#running-docker)
- [Database & migrations](#database--migrations)
- [API](#api)
- [Service logic](#service-logic)
- [Testing](#testing)
- [Verifying tables](#verifying-tables)
- [Troubleshooting](#troubleshooting)
- [Local dev (without Docker)](#local-dev-without-docker)
- [Production notes](#production-notes)
- [Future extensions](#future-extensions)

---

## Architecture

- **FastAPI** app (`app/main.py`, `app/api.py`)  
- **SQLAlchemy** session (`app/db.py`)  
- **Alembic** migrations (`app/alembic/…`)  
- **PostGIS** (geography) for distance/buffer:  
  - `features.location` = `geography(Point,4326)`  
  - `footprints.area` = `geography(Polygon,4326)`  
- **Raw SQL** via `sqlalchemy.text()` in `app/service.py` to use PostGIS (`ST_SetSRID`, `ST_Buffer`, `ST_DWithin`, `ST_Distance`, `ST_Area`).  
- **Docker Compose**: a PostGIS DB and the API container.  
- **On-start migrations** (dev): `start.sh` → wait for DB → `alembic upgrade head` → start Uvicorn.

---

## Prereqs

- Docker & Docker Compose
- `curl` (and optionally `jq`) for manual tests

---

## Project structure

```
root/
├─ .env
├─ .env.example
├─ docker-compose.yml
├─ requirements.txt
└─ app/
   ├─ Dockerfile
   ├─ start.sh
   ├─ check_db.py
   ├─ __init__.py
   ├─ main.py
   ├─ api.py
   ├─ db.py
   ├─ models.py
   ├─ service.py
   ├─ alembic.ini             # script_location = app/alembic
   └─ alembic/
      ├─ env.py
      └─ versions/
         └─ 0001_init.py      # features + footprints + PostGIS bits
```

---

## Environment (.env)

Create `root/.env`:

```env
# Postgres (db container)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=appdb

# App/SQLAlchemy connection (api container)
DATABASE_URL=postgresql://postgres:postgres@db:5432/appdb

# Optional for tests that use httpx outside docker
API_URL=http://localhost:8000
```

> Keep secrets out of git. Commit `.env.example`, not `.env`.

---

## Running (Docker)

```bash
docker compose up --build
```

When ready:
- API: http://localhost:8000  
- OpenAPI/Swagger: http://localhost:8000/docs

> On start, the API container waits for DB, runs `alembic upgrade head`, then launches Uvicorn.

---

## Database & migrations

Initial migration (`0001_init.py`) creates:

- **features**
  - `id UUID PK`
  - `name TEXT`
  - `status TEXT` (defaults to `queued`, set to `done` after processing)
  - `attempts INT` (reserved for retries)
  - `created_at TIMESTAMPTZ`, `updated_at TIMESTAMPTZ`
  - `location geography(Point,4326)` + GIST index

- **footprints**
  - `feature_id UUID PK` (FK → features.id, cascade delete)
  - `area geography(Polygon,4326)` + GIST index
  - `created_at`, `updated_at`

PostGIS is enabled by `CREATE EXTENSION IF NOT EXISTS postgis;` in the migration (DB image is `postgis/postgis`).

---

## API

Base URL: `http://localhost:8000`

### Health
- `GET /health` → `{"status":"ok"}`  
  *If your external tests call `/healthz`, either adjust them or add a small alias route.*

### Create feature
- `POST /features`  
  Body:
  ```json
  {"name": "Site A", "lat": 45.5017, "lon": -73.5673}
  ```
  Returns:
  ```json
  {"id": "<uuid>"}
  ```

### Process feature
- `POST /features/{feature_id}/process`  
  Buffers the point by 500m (default) into a polygon, upserts into `footprints`, marks feature `done`.  
  Returns:
  ```json
  {"processed": true}
  ```
  or `404` if the feature is missing.

### Get feature
- `GET /features/{feature_id}`  
  Returns:
  ```json
  {"id": "...", "name": "...", "status": "done", "buffer_area_m2": 785000.0}
  ```
  `buffer_area_m2` is `null` until processed (then ~ `π * 500^2 ≈ 785,398 m²`).

### Nearby
- `GET /features/near?lat=…&lon=…&radius_m=…`  
  Returns a list of:
  ```json
  [{"id":"...","name":"...","status":"...","distance_m": 12.34}, …]
  ```
  All features within `radius_m`, **sorted by distance ASC**.

> **Route order note:** In `api.py`, `/features/near` is declared **before** `/features/{feature_id}` to avoid path conflicts.

---

## Service logic

`app/service.py` (raw SQL with bind params):

- `create_feature(db, name, lat, lon)`  
  Inserts a new row with `location = ST_SetSRID(ST_MakePoint(lon,lat), 4326)::geography`.

- `process_feature(db, feature_id, buffer_m=500)`  
  `ST_Buffer(location, buffer_m)::geography` → upsert into `footprints` → set `status='done'`.  
  Idempotent: re-running updates the polygon and timestamps.

- `get_feature(db, feature_id)`  
  Returns basic fields and `ST_Area(fp.area)` in m² (float).

- `features_near(db, lat, lon, radius_m)`  
  Uses `ST_DWithin` for filtering and `ST_Distance` for ordering.

All queries use parameterization via SQLAlchemy `text()`.

---

## Testing

### Quick curl smoke

```bash
# health
curl -s http://localhost:8000/health

# create
FID=$(curl -s -X POST http://localhost:8000/features \
  -H 'content-type: application/json' \
  -d '{"name":"Site A","lat":45.5017,"lon":-73.5673}' | jq -r .id)

# process
curl -s -X POST http://localhost:8000/features/$FID/process

# get
curl -s http://localhost:8000/features/$FID

# nearby
curl -s "http://localhost:8000/features/near?lat=45.5017&lon=-73.5673&radius_m=300"
```

### Pytest (smoke + extras)

Inside the API container:

```bash
docker compose exec api pip install -q pytest httpx
docker compose exec api pytest -q
```

Suggested tests (examples):
- Health endpoint
- Create → Process → Get (area sanity check)
- Nearby filtering & ordering at 100m/300m/1000m
- Idempotent processing
- Validation errors (bad lat/lon/radius)
- 404s for unknown IDs

---

## Verifying tables

```bash
# list tables
docker compose exec db psql -U postgres -d appdb -c "\dt"

# inspect schema
docker compose exec db psql -U postgres -d appdb -c "\d+ features"
docker compose exec db psql -U postgres -d appdb -c "\d+ footprints"

# migration version
docker compose exec db psql -U postgres -d appdb -c "SELECT * FROM alembic_version;"

# confirm PostGIS
docker compose exec db psql -U postgres -d appdb -c "\dx postgis"
```

---

## Troubleshooting

**`./app/start.sh: Permission denied`**  
Ensure exec bit & LF endings in Dockerfile:  
```dockerfile
RUN chmod +x app/start.sh && sed -i 's/\r$//' app/start.sh
```

**`FAILED: Path doesn't exist: '/app/alembic'`**  
Set `app/alembic.ini` → `[alembic] script_location = app/alembic`, and run with `alembic -c /app/app/alembic.ini upgrade head`.

**`psycopg2.ProgrammingError: invalid dsn ... "+psycopg2"`**  
Use plain `postgresql://…` in `.env` (`DATABASE_URL`), or normalize before connecting.

**Syntax error at `:` (bind casts)**  
Don’t write `:param::type`. Use `CAST(:param AS type)` (fixed in `service.py`).

**`/features/near` acting as `{feature_id}`**  
Declare `/features/near` **before** `/features/{feature_id}` in `api.py`.

**Migrations racing in prod**  
In production, run Alembic as a **separate, one-off step** before starting app replicas.

---

## Local dev (without Docker)

1) Start a local Postgres with PostGIS (or use a cloud DB).  
2) Set `.env` with `DATABASE_URL=postgresql://.../appdb`.  
3) Create venv & install deps:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
4) Run migrations:
   ```bash
   alembic -c app/alembic.ini upgrade head
   ```
5) Start API:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## Production notes

- **Do NOT** run migrations inside app startup in production.  
  Recommended: CI/CD step, separate container/Job (e.g., k8s Job) that runs `alembic upgrade head`; start app **after** it succeeds.
- Keep migrations **backward-compatible** for rolling updates (expand → backfill → flip → contract).
- Back up DB before destructive migrations.
- Add proper logging, metrics, and tracing as needed.
- Consider rate-limits and auth for public endpoints.

---

## Future extensions

- Return geometry as **GeoJSON** (e.g., `ST_AsGeoJSON(fp.area)` in `GET /features/{id}`).  
- Custom buffer distance per request (`/process?buffer_m=750`).  
- Replace raw SQL with GeoAlchemy2 models if you prefer ORM types.  
- Pagination/sorting/filters for `/features/near`.  
- Background jobs for re-processing or area analytics.

