.PHONY: help dev upgrade downgrade revision

help:                ## Show this help
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

dev:                 ## Run the API with auto-reload (http://localhost:8000)
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

upgrade:             ## Apply all database migrations
	uv run alembic upgrade head

downgrade:           ## Roll back the last migration
	uv run alembic downgrade -1

revision:            ## Create a migration: make revision name="what changed"
	uv run alembic revision --autogenerate -m "$(name)"
