set -euo pipefail

echo "Waiting for database..."
python -m app.check_db

echo "Running Alembic migrations..."
alembic -c /app/app/alembic.ini upgrade head

echo "Starting FastAPI..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info
