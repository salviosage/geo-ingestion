import os, uuid, time, httpx, pytest

API = os.getenv("API_URL", "http://localhost:8000")

@pytest.mark.order(1)
def test_health():
    r = httpx.get(f"{API}/healthz", timeout=10)
    assert r.status_code == 200

@pytest.mark.order(2)
def test_flow():
    # create
    r = httpx.post(f"{API}/features", json={"name":"Site A","lat":45.5017,"lon":-73.5673}, timeout=20)
    assert r.status_code == 200
    fid = r.json()["id"]; uuid.UUID(fid)
    # process
    r = httpx.post(f"{API}/features/{fid}/process", timeout=30); assert r.status_code == 200
    # get
    r = httpx.get(f"{API}/features/{fid}", timeout=20); assert r.status_code == 200
    data = r.json(); assert data.get("status") == "done" and data.get("buffer_area_m2", 0) > 700000
    # near
    r = httpx.get(f"{API}/features/near", params={"lat":45.5017,"lon":-73.5673,"radius_m":1000}, timeout=20)
    assert r.status_code == 200
    assert any(item["id"] == fid for item in r.json())
