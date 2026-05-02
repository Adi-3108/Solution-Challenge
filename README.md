# FairSight

FairSight is an AI bias detection and remediation platform for auditing datasets and machine-learning outputs before deployment.

It includes:
- a FastAPI backend for auth, project management, dataset uploads, audits, and reporting
- a React + Vite frontend for dashboards, uploads, and audit results
- a Celery worker for background audit jobs and report generation
- PostgreSQL and Redis for persistence and task coordination
- Docker and Render deployment support

Tagline: `See the bias before it sees you`

## Features

- User authentication and role-based access
- Dataset upload and validation
- Bias audit execution with scorecards and remediation guidance
- Report generation in PDF and JSON formats
- Historical comparisons, drift panels, and accessible visualizations

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, Alembic, Celery
- **Frontend:** React 18, Vite, TailwindCSS, React Query, Zustand
- **Data/ML:** Pandas, NumPy, scikit-learn, SHAP, Fairlearn, AIF360
- **Infrastructure:** Docker, Nginx, PostgreSQL, Redis

## Repository Layout

- `backend/` — FastAPI app, migrations, Celery worker, and backend tests
- `frontend/` — React app, UI components, unit tests, and Playwright tests
- `render.yaml` — Render blueprint for backend, worker, Postgres, and Redis
- `nginx.conf` — local reverse-proxy config for the Docker stack

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose

### Run with Docker Compose

1. Start the stack:
  ```bash
  docker-compose up --build
  ```
2. Seed demo data if needed:
  ```bash
  docker exec fairsight-backend python seed.py
  ```

### Local URLs

- App: `http://localhost`
- API docs: `http://localhost/docs`
- Backend health: `http://localhost:8000/health`
- Nginx health: `http://localhost/health`

## Environment Variables

The backend reads configuration from environment variables.

Required values:

- `SECRET_KEY`
- `DATABASE_URL`
- `ALEMBIC_DATABASE_URL`
- `REDIS_URL`

Recommended values:

- `FRONTEND_ORIGIN`
- `CORS_ORIGINS`
- `ENVIRONMENT=production` for Render
- `LOG_LEVEL=INFO`

Optional storage settings:

- `FILE_STORAGE_PATH`
- `PDF_REPORT_PATH`

## Testing

### Backend

```bash
docker exec fairsight-backend pytest
```

### Frontend unit tests

```bash
docker exec fairsight-frontend npm test
```

### Frontend end-to-end tests

```bash
docker exec fairsight-frontend npx playwright test
```

## Deployment on Render

Use `render.yaml` for a blueprint deploy, or follow the manual steps in `docs/render-deployment.md`.

## Demo Credentials

- Admin: `admin@fairsight.demo / Demo1234!`
- Analyst: `analyst@fairsight.demo / Demo1234!`
- Viewer: `viewer@fairsight.demo / Demo1234!`

## Architecture

- Reverse proxy: `nginx`
- API + worker: FastAPI and Celery
- Data store: PostgreSQL
- Cache / broker: Redis
- UI: React, Vite, TailwindCSS

Architecture diagram: [`fairsight_system_architecture.svg`](./fairsight_system_architecture.svg)

