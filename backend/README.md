# FairSight Backend

FastAPI application, Celery worker, bias engine, and persistence layer.

## What lives here

- API routes and application startup in `app/`
- Alembic migrations in `alembic/`
- Background jobs in `app/tasks/`
- Backend tests in `tests/`

## Runtime requirements

- Python 3.11+
- PostgreSQL connection string in `DATABASE_URL`
- Redis connection string in `REDIS_URL`
- Secret key in `SECRET_KEY`

## Local run

From the backend directory:

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Render deployment notes

- Use `backend/Dockerfile`
- Set the build context to `backend`
- Keep `DATABASE_URL`, `ALEMBIC_DATABASE_URL`, and `REDIS_URL` pointed at Render internal service URLs
- Let `backend/start.sh` handle migrations before Uvicorn starts


