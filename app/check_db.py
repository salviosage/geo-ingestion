from __future__ import annotations
import os
import time
from dotenv import load_dotenv
from tenacity import retry, stop_after_delay, wait_fixed
import psycopg2

load_dotenv()

RAW = os.environ.get("DATABASE_URL")
if not RAW:
    raise SystemExit("DATABASE_URL is not set")

DSN = RAW


@retry(wait=wait_fixed(2), stop=stop_after_delay(90), reraise=True)
def _wait_once():
    conn = psycopg2.connect(DSN, connect_timeout=5)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()
    finally:
        conn.close()


if __name__ == "__main__":
    t0 = time.time()
    _wait_once()
    print(f"DB ready after {time.time() - t0:.1f}s")
