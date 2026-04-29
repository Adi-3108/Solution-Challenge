#!/bin/sh
set -e

cd /app

ALEMBIC_CONFIG_PATH=""

if [ -f "/app/alembic.ini" ]; then
  ALEMBIC_CONFIG_PATH="/app/alembic.ini"
elif [ -f "/app/backend/alembic.ini" ]; then
  ALEMBIC_CONFIG_PATH="/app/backend/alembic.ini"
else
  # Last resort: find it anywhere under /app (build context can vary on Render).
  ALEMBIC_CONFIG_PATH="$(find /app -maxdepth 5 -type f -name alembic.ini 2>/dev/null | head -n 1 || true)"
fi

if [ -z "$ALEMBIC_CONFIG_PATH" ] || [ ! -f "$ALEMBIC_CONFIG_PATH" ]; then
  echo "alembic.ini not found inside the image" >&2
  exit 1
fi

MIGRATION_WORKDIR="$(dirname "$ALEMBIC_CONFIG_PATH")"
echo "Running migrations using: $ALEMBIC_CONFIG_PATH"
cd "$MIGRATION_WORKDIR"
python -m alembic -c "$ALEMBIC_CONFIG_PATH" upgrade head

cd /app
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"