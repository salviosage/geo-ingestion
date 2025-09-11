from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid


def _as_uuid(value: str | uuid.UUID) -> uuid.UUID:
    return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))


def create_feature(db: Session, name: str, lat: float, lon: float) -> uuid.UUID:
    fid = uuid.uuid4()
    sql = text("""
        INSERT INTO features (id, name, location)
        VALUES (
            :id,
            :name,
            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
        )
    """)
    db.execute(sql, {"id": str(fid), "name": name,
               "lat": float(lat), "lon": float(lon)})
    db.commit()
    return fid


def process_feature(db: Session, feature_id: str, buffer_m: int = 500) -> bool:
    fid = _as_uuid(feature_id)
    sql = text("""
        WITH src AS (
            SELECT id, location
            FROM features
            WHERE id = :fid
        ),
        buff AS (
            SELECT
                id,
                ST_Buffer(location, CAST(:buffer_m AS double precision))::geography AS poly
            FROM src
        ),
        upsert_fp AS (
            INSERT INTO footprints (feature_id, area, created_at, updated_at)
            SELECT id, poly, timezone('utc', now()), timezone('utc', now())
            FROM buff
            ON CONFLICT (feature_id)
            DO UPDATE SET
                area = EXCLUDED.area,
                updated_at = timezone('utc', now())
            RETURNING feature_id
        )
        UPDATE features f
        SET status = 'done', updated_at = timezone('utc', now())
        WHERE f.id IN (SELECT feature_id FROM upsert_fp)
        RETURNING f.id
    """)
    row = db.execute(
        sql, {"fid": str(fid), "buffer_m": int(buffer_m)}).fetchone()
    db.commit()
    return bool(row)


def get_feature(db: Session, feature_id: str):
    fid = _as_uuid(feature_id)
    sql = text("""
        SELECT
            f.id::text  AS id,
            f.name      AS name,
            f.status    AS status,
            CASE WHEN fp.area IS NOT NULL
                 THEN ST_Area(fp.area)::float
                 ELSE NULL
            END AS buffer_area_m2
        FROM features f
        LEFT JOIN footprints fp ON fp.feature_id = f.id
        WHERE f.id = :fid
    """)
    row = db.execute(sql, {"fid": str(fid)}).mappings().first()
    return dict(row) if row else None


def features_near(db: Session, lat: float, lon: float, radius_m: int):
    sql = text("""
        WITH ref AS (
            SELECT ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography AS g
        )
        SELECT
            f.id::text AS id,
            f.name     AS name,
            f.status   AS status,
            ST_Distance(f.location, r.g)::float AS distance_m
        FROM features f
        CROSS JOIN ref r
        WHERE ST_DWithin(f.location, r.g, CAST(:radius_m AS double precision))
        ORDER BY distance_m ASC
    """)
    rows = db.execute(
        sql,
        {"lat": float(lat), "lon": float(lon), "radius_m": int(radius_m)}
    ).mappings().all()
    return [dict(r) for r in rows]
