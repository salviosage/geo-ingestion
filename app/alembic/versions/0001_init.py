"""TODO migration — enable PostGIS and create geography columns

Revision ID: 0001_init
Revises:
Create Date: 2025-09-04
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # TODO: op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    # TODO: create features table and geography(Point,4326) column + GIST index
    # TODO: create footprints table and geography(Polygon,4326) column + GIST index
    pass

def downgrade():
    # TODO: drop in reverse order and extension
    pass
