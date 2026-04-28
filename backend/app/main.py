from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.middleware.request_context import RequestContextMiddleware
from app.services.health import health_status
from app.utils.response import error_response


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.file_storage_path.mkdir(parents=True, exist_ok=True)
    settings.pdf_report_path.mkdir(parents=True, exist_ok=True)
    yield


configure_logging()
app = FastAPI(title="FairSight API", version="0.1.0", lifespan=lifespan)
local_development_origin_regex = (
    r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?$" if settings.environment == "development" else None
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=local_development_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health() -> JSONResponse:
    payload = await health_status()
    payload["service"] = "backend"
    return JSONResponse(status_code=200 if payload["status"] == "ok" else 503, content=payload)



@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.code, exc.message, exc.details | {"request_id": request.state.request_id}),
    )


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content=error_response(
            "validation_error",
            "One or more fields failed validation.",
            {
                "issues": jsonable_encoder(
                    exc.errors(),
                    custom_encoder={BaseException: lambda error: str(error)},
                ),
                "request_id": request.state.request_id,
            },
        ),
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, _: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content=error_response(
            "internal_server_error",
            "An unexpected error occurred.",
            {"request_id": request.state.request_id},
        ),
    )
