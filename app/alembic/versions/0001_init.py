"""initial schema: features + footprints, postgis

Revision ID: 0001_init
Revises:
Create Date: 2025-09-10
"""
from __future__ import annotations
from alembic import op
import sqlalchemy as sa

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

UTC_NOW = sa.text("timezone('utc', now())")


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # features table
    op.create_table(
        "features",
        sa.Column("id", sa.dialects.postgresql.UUID(
            as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False,
                  server_default=sa.text("'queued'")),
        sa.Column("attempts", sa.Integer(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=True, server_default=UTC_NOW),
    )
    op.create_index("ix_features_name", "features", ["name"])

    # add geography(Point,4326) column + GIST index
    op.execute("ALTER TABLE features ADD COLUMN location geography(Point,4326);")
    op.execute(
        "CREATE INDEX idx_features_location_gist ON features USING GIST (location);")

    # footprints table (one-to-one via PK = feature_id)
    op.create_table(
        "footprints",
        sa.Column("feature_id", sa.dialects.postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  nullable=False, server_default=UTC_NOW),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  nullable=True, server_default=UTC_NOW),
        sa.ForeignKeyConstraint(
            ["feature_id"], ["features.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("feature_id"),
    )

    # add geography(Polygon,4326) column + GIST index
    op.execute("ALTER TABLE footprints ADD COLUMN area geography(Polygon,4326);")
    op.execute(
        "CREATE INDEX idx_footprints_area_gist ON footprints USING GIST (area);")


def downgrade():
    # drop in reverse order
    op.execute("DROP INDEX IF EXISTS idx_footprints_area_gist;")
    op.execute("ALTER TABLE footprints DROP COLUMN IF EXISTS area;")
    op.drop_table("footprints")

    op.execute("DROP INDEX IF EXISTS idx_features_location_gist;")
    op.execute("ALTER TABLE features DROP COLUMN IF EXISTS location;")
    op.drop_index("ix_features_name", table_name="features")
    op.drop_table("features")

    # op.execute("DROP EXTENSION IF EXISTS postgis;")
