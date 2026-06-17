FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=src \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv

# Install dependencies first so this layer stays cached until the lockfile
# changes. --no-install-project: we run the app from PYTHONPATH=src, so the
# package itself never needs to be built/installed.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Application source (the .dockerignore keeps the host .venv/.env out).
COPY . .

# Run migrations, then serve. `exec` makes uvicorn PID 1 so it receives
# SIGTERM for a clean shutdown. WEB_CONCURRENCY is overridable via env.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY:-2}"]
