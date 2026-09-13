.PHONY: setup start test test-web lint fmt migrate revision db-check

setup:
	./setup.sh

start:
	./start.sh

# Frontend tests (Vitest + React Testing Library)
test-web:
	cd frontend && npm test

# Database preflight: reachable? schema current? (auto-creates/upgrades). Same
# check start.sh runs before launching the app.
db-check:
	cd backend && .venv/bin/python -m app.db.doctor

# Database migrations (Alembic). `make revision m="add X"` autogenerates one.
migrate:
	cd backend && .venv/bin/alembic upgrade head

revision:
	cd backend && .venv/bin/alembic revision --autogenerate -m "$(m)"

# Backend quality gates (run inside the venv created by setup.sh).
test:
	cd backend && .venv/bin/python -m pytest

lint:
	cd backend && .venv/bin/ruff check app tests

fmt:
	cd backend && .venv/bin/ruff check --fix app tests
