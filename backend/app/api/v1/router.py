from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import admin, auth, datasets, models, notifications, projects, runs

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(datasets.router, tags=["datasets"])
api_router.include_router(models.router, tags=["models"])
api_router.include_router(runs.router, tags=["runs"])
api_router.include_router(notifications.router, tags=["notifications"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

