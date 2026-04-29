#!/bin/sh
set -e

cd /app

python -m alembic -c /app/alembic.ini upgrade head
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"