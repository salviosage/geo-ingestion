from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from db import get_db
import service

router = APIRouter()

class CreateFeatureIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

@router.post("/features", response_model=dict)
def create_feature(payload: CreateFeatureIn, db: Session = Depends(get_db)):
    fid = service.create_feature(db, name=payload.name, lat=payload.lat, lon=payload.lon)
    return {"id": str(fid)}

@router.post("/features/{feature_id}/process", response_model=dict)
def process_feature(feature_id: str, db: Session = Depends(get_db)):
    ok = service.process_feature(db, feature_id)
    if not ok:
        raise HTTPException(404, "Not found")
    return {"processed": True}

@router.get("/features/{feature_id}", response_model=dict)
def get_feature(feature_id: str, db: Session = Depends(get_db)):
    row = service.get_feature(db, feature_id)
    if not row:
        raise HTTPException(404, "Not found")
    return row

@router.get("/features/near", response_model=list[dict])
def features_near(lat: float = Query(..., ge=-90, le=90),
                  lon: float = Query(..., ge=-180, le=180),
                  radius_m: int = Query(1000, gt=0),
                  db: Session = Depends(get_db)):
    return service.features_near(db, lat, lon, radius_m)
