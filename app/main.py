from fastapi import FastAPI
from app.api import router as api_router

app = FastAPI(title="Geo Ingestion Starter")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    return {"status": "ready"}

app.include_router(api_router)
