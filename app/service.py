# IMPLEMENT HERE — use PostGIS via raw SQL (see SERVICE_TODO.md)
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid

def create_feature(db: Session, name: str, lat: float, lon: float) -> uuid.UUID:
    # TODO: insert point into features table
    raise NotImplementedError

def process_feature(db: Session, feature_id: str, buffer_m: int = 500) -> bool:
    # TODO: buffer point, compute area, insert polygon into footprints table, update feature status
    raise NotImplementedError

def get_feature(db: Session, feature_id: str):
    # TODO: select feature and its polygon from features and footprints tables
    raise NotImplementedError

def features_near(db: Session, lat: float, lon: float, radius_m: int):
    # TODO: select features within radius from features and footprints tables
    raise NotImplementedError
