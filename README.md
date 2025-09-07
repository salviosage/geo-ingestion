# Geo Ingestion Starter (FastAPI + PostGIS) — Candidate Task

Implement the missing pieces (marked **TODO**) so the tests pass.

## Build this
- `POST /features` — store a named point (`name`, `lat`, `lon`) in PostGIS (`geography(Point,4326)`), set `status=queued`.
- **Dev-only** `POST /features/{id}/process` — buffer 500 m (`ST_Buffer`), compute area m² (`ST_Area`), upsert polygon, set `status=done`.
- `GET /features/{id}` — return status + `buffer_area_m2`.
- `GET /features/near?lat&lon&radius_m` — nearby features via `ST_DWithin`.

## Run
```bash
docker compose up --build
# Create feature
curl -s -X POST localhost:8000/features -H "content-type: application/json" -d '{ "name":"Site A","lat":45.5017,"lon":-73.5673 }'
# Process (dev-only)
curl -s -X POST localhost:8000/features/<id>/process
# Get
curl -s localhost:8000/features/<id>
# Nearby
curl -s "localhost:8000/features/near?lat=45.5017&lon=-73.5673&radius_m=1000"
```

## You must implement
- Alembic migration enabling **PostGIS** and creating tables with **geography** columns + GIST indexes.
- SQL in `service.py` for point insert, buffer/area, and nearby query.
- Route handlers already call your functions.

## Tests
Run `pytest` inside the `api` container (or locally with `DATABASE_URL`). They fail until you implement the TODOs.

See **SERVICE_TODO.md** for a PostGIS cheat‑sheet.
