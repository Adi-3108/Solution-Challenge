#!/bin/sh
set -e

cd /app

ALEMBIC_CONFIG_PATH="/app/alembic.ini"
# Render's Docker build context can shift where `alembic.ini` ends up.
# Support both `/app/alembic.ini` and `/app/backend/alembic.ini`.
if [ ! -f "$ALEMBIC_CONFIG_PATH" ]; then
  if [ -f "/app/backend/alembic.ini" ]; then
    ALEMBIC_CONFIG_PATH="/app/backend/alembic.ini"
  else
    echo "alembic.ini not found in /app or /app/backend" >&2
    exit 1
  fi
fi

python -m alembic -c "$ALEMBIC_CONFIG_PATH" upgrade head
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"