# Makefile
.PHONY: help build up down test clean migrate logs shell

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start services"
	@echo "  make down     - Stop services"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Clean up containers and volumes"
	@echo "  make migrate  - Run database migrations"
	@echo "  make logs     - View logs"
	@echo "  make shell    - Open shell in API container"

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

test:
	docker compose exec api pytest -v

test-unit:
	docker compose exec api pytest test_unit.py -v

test-smoke:
	docker compose exec api pytest test_smoke.py -v

clean:
	docker compose down -v
	docker system prune -f

migrate:
	docker compose exec api alembic upgrade head

logs:
	docker compose logs -f

shell:
	docker compose exec api /bin/bash

# Development database commands
db-shell:
	docker compose exec db psql -U postgres -d appdb

db-reset:
	docker compose exec api alembic downgrade base
	docker compose exec api alembic upgrade head

# API testing commands
create-feature:
	@echo "Creating test feature..."
	@curl -s -X POST localhost:8000/features \
		-H "content-type: application/json" \
		-d '{"name":"Test Site","lat":45.5017,"lon":-73.5673}' | python -m json.tool

health:
	@curl -s localhost:8000/healthz | python -m json.tool

# Format and lint
format:
	docker compose exec api black .
	docker compose exec api isort .

lint:
	docker compose exec api flake8 .
	docker compose exec api mypy .