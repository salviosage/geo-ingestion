# SERVICE_TODO — PostGIS cheat‑sheet

Enable PostGIS:
  CREATE EXTENSION IF NOT EXISTS postgis;

Create point from lon/lat in meters-ready type:
  ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography

Nearby (within radius meters):
  ST_DWithin(f.geom, ref.g, :radius_m)

Buffer + area:
  ST_Buffer(geom, :buffer_m)
  ST_Area(geom)
