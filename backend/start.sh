#!/bin/sh
set -e

cd /app

ALEMBIC_CONFIG_PATH=""

if [ -f "/app/alembic.ini" ]; then
  ALEMBIC_CONFIG_PATH="/app/alembic.ini"
elif [ -f "/app/backend/alembic.ini" ]; then
  ALEMBIC_CONFIG_PATH="/app/backend/alembic.ini"
else
  # Render's Docker build context/root can shift which files land in the image.
  # Generate a valid alembic.ini based on where the migrations folder exists.
  if [ -d "/app/alembic" ]; then
    ALEMBIC_CONFIG_PATH="/app/alembic.ini"
    cat > "$ALEMBIC_CONFIG_PATH" <<'EOF'
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+psycopg://fairsight:fairsight@db:5432/fairsight

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
EOF
  elif [ -d "/app/backend/alembic" ]; then
    ALEMBIC_CONFIG_PATH="/app/backend/alembic.ini"
    cat > "$ALEMBIC_CONFIG_PATH" <<'EOF'
[alembic]
script_location = alembic
sqlalchemy.url = postgresql+psycopg://fairsight:fairsight@db:5432/fairsight

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
EOF
  else
    echo "Could not find migrations folder (/app/alembic or /app/backend/alembic) inside the image" >&2
    exit 1
  fi
fi

if [ ! -f "$ALEMBIC_CONFIG_PATH" ]; then
  echo "alembic.ini missing even after generation" >&2
  exit 1
fi

MIGRATION_WORKDIR="$(dirname "$ALEMBIC_CONFIG_PATH")"
echo "Running migrations using: $ALEMBIC_CONFIG_PATH"
cd "$MIGRATION_WORKDIR"
python -m alembic -c "$ALEMBIC_CONFIG_PATH" upgrade head

cd /app
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"