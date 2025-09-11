import os
import uuid
import httpx
import pytest

API = os.getenv("API_URL", "http://localhost:8000")


def _create(name: str, lat: float, lon: float) -> str:
    r = httpx.post(f"{API}/features",
                   json={"name": name, "lat": lat, "lon": lon},
                   timeout=20)
    assert r.status_code == 200, r.text
    fid = r.json()["id"]
    uuid.UUID(fid)
    return fid


def _process(fid: str, expect_status=200):
    r = httpx.post(f"{API}/features/{fid}/process", timeout=30)
    assert r.status_code == expect_status, r.text
    return r.json() if r.headers.get("content-type", "").startswith("application/json") else None


def _get(fid: str):
    r = httpx.get(f"{API}/features/{fid}", timeout=20)
    return r


def _near(lat: float, lon: float, radius_m: int):
    r = httpx.get(f"{API}/features/near",
                  params={"lat": lat, "lon": lon, "radius_m": radius_m},
                  timeout=20)
    return r

# tests


def test_create_then_get_before_processing_has_null_area():
    fid = _create("BeforeProc", 45.5017, -73.5673)
    r = _get(fid)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] in ("queued", "done")  # default 'queued'
    assert data.get("buffer_area_m2") in (None, 0)  # not processed yet -> None


def test_process_is_idempotent_returns_ok_twice():
    fid = _create("Idempotent", 45.5017, -73.5673)
    first = _process(fid)                    # creates footprint
    assert first["processed"] is True
    second = _process(fid)                   # updates footprint
    assert second["processed"] is True
    r = _get(fid)
    assert r.status_code == 200
    area = r.json().get("buffer_area_m2")
    assert area and area > 700_000  # ~ pi*500^2


def test_process_nonexistent_returns_404():
    bogus = str(uuid.uuid4())
    r = httpx.post(f"{API}/features/{bogus}/process", timeout=20)
    assert r.status_code == 404


def test_validation_rejects_bad_input():
    # bad latitude
    r = httpx.post(f"{API}/features", json={"name": "BadLat",
                   "lat": 123.0, "lon": 0.0}, timeout=10)
    assert r.status_code == 422
    # bad longitude
    r = httpx.post(f"{API}/features", json={"name": "BadLon",
                   "lat": 0.0, "lon": 181.0}, timeout=10)
    assert r.status_code == 422
    # bad radius
    r = httpx.get(f"{API}/features/near", params={"lat": 0,
                  "lon": 0, "radius_m": -1}, timeout=10)
    assert r.status_code == 422


def test_near_distance_filter_and_ordering():
    # Base point (Old Port, Montréal-ish)
    base_lat, base_lon = 45.5017, -73.5673
    # Roughly ~236m east and ~708m east at this latitude (Δlon ≈ 0.003 ≈ 236m)
    fid_a = _create("Near-A", base_lat, base_lon)              # distance ~0m
    fid_b = _create("Near-B", base_lat, base_lon + 0.003)      # ~236m
    fid_c = _create("Near-C", base_lat, base_lon + 0.009)      # ~708m

    # Small radius (100m): only A
    r = _near(base_lat, base_lon, 100)
    assert r.status_code == 200, r.text
    got = [row["id"] for row in r.json()]
    assert fid_a in got and fid_b not in got and fid_c not in got

    # Medium radius (300m): A and B, A first
    r = _near(base_lat, base_lon, 300)
    assert r.status_code == 200, r.text
    got = [row["id"] for row in r.json()]
    assert fid_a in got and fid_b in got and fid_c not in got
    assert got.index(fid_a) < got.index(fid_b)  # sorted by distance

    # Large radius (1000m): all three, sorted by distance A < B < C
    r = _near(base_lat, base_lon, 1000)
    assert r.status_code == 200, r.text
    got = [row["id"] for row in r.json()]
    assert fid_a in got and fid_b in got and fid_c in got
    assert got.index(fid_a) < got.index(fid_b) < got.index(fid_c)


def test_get_unknown_returns_404():
    bogus = str(uuid.uuid4())
    r = _get(bogus)
    assert r.status_code == 404
