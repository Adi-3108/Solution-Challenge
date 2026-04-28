from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.api.v1.route_helpers import (
    apply_cursor,
    get_dataset_for_user,
    get_model_for_user,
    get_project_for_user,
    get_run_for_user,
    next_cursor,
)
from app.core.database import get_db_session
from app.core.errors import AppError
from app.core.rate_limit import enforce_user_rate_limit
from app.models.audit import AuditRun
from app.models.enums import ReportFormat, UserRole
from app.models.user import User
from app.schemas.audit import ReportCreateRequest, RunCreateRequest
from app.services.audit.service import create_audit_run, get_cached_run_results
from app.services.bias_engine.constants import DISPLAY_NAMES
from app.services.drift.service import build_run_drift_summary
from app.services.reports.service import generate_report
from app.utils.audit_log import create_audit_log
from app.utils.response import envelope
from app.utils.serialization import run_to_dict

router = APIRouter()


@router.post("/projects/{project_id}/runs")
async def create_run(
    project_id: str,
    payload: RunCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot trigger audit runs.", status_code=403)
    await enforce_user_rate_limit(request, "audit_runs")
    project = await get_project_for_user(session, project_id, current_user)
    dataset = await get_dataset_for_user(session, payload.dataset_id, current_user)
    model = await get_model_for_user(session, payload.model_id, current_user) if payload.model_id else None
    run = await create_audit_run(session, project, dataset, model, payload.thresholds, request.state.request_id)
    await create_audit_log(session, current_user.id, "create_run", "run", run.id, {"project_id": project.id})
    await session.commit()
    return envelope(request, run_to_dict(run))


@router.get("/projects/{project_id}/runs")
async def list_runs(
    project_id: str,
    request: Request,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, le=50),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_for_user(session, project_id, current_user)
    query = select(AuditRun).where(AuditRun.project_id == project.id).order_by(desc(AuditRun.started_at), desc(AuditRun.id))
    query = apply_cursor(query, AuditRun, "started_at", cursor).limit(limit + 1)
    runs = list((await session.execute(query)).scalars().all())
    has_more = len(runs) > limit
    items = runs[:limit]
    return envelope(
        request,
        [run_to_dict(item) for item in items],
        next_cursor(items, "started_at") if has_more else None,
    )


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    run = await get_run_for_user(session, run_id, current_user)
    return envelope(request, run_to_dict(run))


@router.get("/runs/{run_id}/results")
async def get_run_results(
    run_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    run = await get_run_for_user(session, run_id, current_user)
    drift = await build_run_drift_summary(session, run_id)
    cached = await get_cached_run_results(run_id)
    if cached is not None:
        return envelope(request, {"run": run_to_dict(run), **cached, "drift": drift.model_dump(mode="json")})
    run = await get_run_for_user(session, run_id, current_user, with_results=True)
    payload = {
        "run": run_to_dict(run),
        "metrics": [
            {
                "id": result.id,
                "metric_name": result.metric_name,
                "display_name": DISPLAY_NAMES.get(result.metric_name, result.metric_name),
                "group_name": result.group_name,
                "intersectional_groups": result.intersectional_groups,
                "value": result.value,
                "severity": result.severity.value,
                "threshold_used": result.threshold_used,
                "explanation": result.explanation,
                "details": result.details_json,
            }
            for result in run.results
        ],
        "shap": run.shap_json,
        "proxy": run.proxy_matrix_json,
        "distributions": run.distributions_json,
        "counterfactual": run.distributions_json.get("counterfactual", []),
        "recommendations": run.remediation_json,
        "summary": run.summary_json,
        "drift": drift.model_dump(mode="json"),
    }
    return envelope(request, payload)


@router.get("/runs/{run_id}/shap")
async def get_run_shap(
    run_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    run = await get_run_for_user(session, run_id, current_user)
    return envelope(request, run.shap_json)


@router.post("/runs/{run_id}/report")
async def create_report(
    run_id: str,
    payload: ReportCreateRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.VIEWER:
        raise AppError(code="forbidden", message="Viewers cannot generate reports.", status_code=403)
    report = await generate_report(session, run_id, ReportFormat(payload.format))
    await create_audit_log(session, current_user.id, "generate_report", "report", report.id, {"run_id": run_id})
    await session.commit()
    return envelope(
        request,
        {
            "id": report.id,
            "run_id": report.run_id,
            "format": report.format.value,
            "file_hash": report.file_hash,
            "generated_at": report.generated_at.isoformat(),
        },
    )


@router.get("/runs/{run_id}/report/{report_format}")
async def download_report(
    run_id: str,
    report_format: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    run = await get_run_for_user(session, run_id, current_user, with_results=True)
    try:
        requested_format = ReportFormat(report_format)
    except ValueError as exc:
        raise AppError(code="invalid_format", message="Unsupported report format.", status_code=400) from exc
    report = next((item for item in run.reports if item.format == requested_format), None)
    if report is None:
        report = await generate_report(session, run_id, requested_format)
    path = Path(report.file_path)
    media_type = "application/pdf" if requested_format == ReportFormat.PDF else "application/json"
    return FileResponse(path, filename=path.name, media_type=media_type)
