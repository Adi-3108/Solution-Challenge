# FairSight

FairSight is an AI bias detection and remediation platform for auditing datasets and machine-learning outputs before deployment. It combines a FastAPI backend, a React data-rich frontend, background audit jobs with Celery, and PDF/JSON reporting for compliance workflows.

Tagline: `See the bias before it sees you`

## Prerequisites

- Docker 24+
- Docker Compose

## Setup

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Start the full stack:
   ```bash
   docker-compose up --build
   ```
3. Seed the demo:
   ```bash
   docker exec fairsight-backend python seed.py
   ```

## Demo Credentials

- Admin: `admin@fairsight.demo / Demo1234!`
- Analyst: `analyst@fairsight.demo / Demo1234!`
- Viewer: `viewer@fairsight.demo / Demo1234!`

## Running Tests

- Backend:
  ```bash
  docker exec fairsight-backend pytest
  ```
- Frontend:
  ```bash
  docker exec fairsight-frontend npm test
  ```
- Playwright:
  ```bash
  docker exec fairsight-frontend npx playwright test
  ```

## Architecture

- Reverse proxy: `nginx`
- API + worker: FastAPI, Celery, Redis, PostgreSQL
- UI: React 18, Vite, TailwindCSS, Recharts
- Bias engine: Pandas, NumPy, scikit-learn, SHAP, AIF360, Fairlearn

Architecture diagram: [fairsight_system_architecture.svg](./fairsight_system_architecture.svg)

## Local URLs

- App: `http://localhost`
- API docs: `http://localhost/docs`
- Backend health: `http://localhost:8000/health`
- Nginx health: `http://localhost/health`

