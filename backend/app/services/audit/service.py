from __future__ import annotations

import asyncio
from datetime import UTC, datetime
import math
from pathlib import Path

import orjson
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppError
from app.core.logging import get_logger
from app.core.redis import get_redis_client
from app.models.audit import AuditResult, AuditRun
from app.models.dataset import Dataset, ModelArtifact
from app.models.enums import AuditRunStatus, SeverityLevel
from app.models.project import Project
from app.services.bias_engine.orchestrator import BiasAuditEngine
from app.services.bias_engine.schemas import AuditInput, BiasThresholdConfig
from app.services.llm.gemini import enrich_audit_payload
from app.services.notifications.service import notify_run_completion
from app.services.storage.service import LocalStorageService

logger = get_logger(__name__)
storage_service = LocalStorageService()


def _sanitize_json_value(value: object) -> object:
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, dict):
        return {key: _sanitize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_json_value(item) for item in value]
    return value


async def create_audit_run(
    session: AsyncSession,
    project: Project,
    dataset: Dataset,
    model: ModelArtifact | None,
    thresholds: BiasThresholdConfig,
    request_id: str,
) -> AuditRun:
    from app.tasks.celery_app import celery_app
    from app.tasks.run_audit import run_audit_task

    run = AuditRun(
        project_id=project.id,
        dataset_id=dataset.id,
        model_id=model.id if model else None,
        status=AuditRunStatus.QUEUED,
        stage_label="Analyzing distributions...",
        started_at=datetime.now(UTC),
        thresholds_json=thresholds.model_dump(mode="json"),
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    if celery_app.conf.task_always_eager:
        await execute_audit_run(str(run.id), request_id)
    else:
        run_audit_task.delay(str(run.id), request_id)
    return run


async def execute_audit_run(run_id: str, request_id: str) -> None:
    from app.core.database import SessionLocal

    async with SessionLocal() as session:
        run = await _load_run(session, run_id)
        try:
            await _mark_running(session, run)
            result = await _compute_run(session, run)
            await _persist_result(session, run, result)
            await notify_run_completion(session, run.project_id, run)
            cache_payload = _sanitize_json_value(
                {
                    "metrics": [item.model_dump(mode="json") for item in result.metrics],
                    "shap": result.shap_payload,
                    "proxy": {
                        "matrix": result.proxy_matrix,
                        "findings": [item.model_dump(mode="json") for item in result.proxy_findings],
                    },
                    "distributions": {
                        "distributions": [item.model_dump(mode="json") for item in result.distributions],
                        "missing_data_rates": result.missing_data_rates,
                        "confusion_matrices": result.confusion_matrices,
                        "calibration_curves": result.calibration_curves,
                        "roc_curves": result.roc_curves,
                        "intersectionality": [
                            item.model_dump(mode="json") for item in result.intersectionality
                        ],
                    },
                    "counterfactual": [
                        item.model_dump(mode="json") for item in result.counterfactual
                    ],
                    "recommendations": [item.model_dump(mode="json") for item in result.recommendations],
                    "summary": result.summary,
                }
            )
            enriched_payload = await enrich_audit_payload(cache_payload)
            await _cache_run_result(run.id, enriched_payload or cache_payload)
        except Exception as exc:
            await session.rollback()
            run = await _load_run(session, run_id)
            run.status = AuditRunStatus.FAILED
            run.stage_label = "Audit failed"
            run.error_message = str(exc)
            run.completed_at = datetime.now(UTC)
            await session.commit()
            logger.exception("audit_run_failed", run_id=run_id, request_id=request_id)


async def get_cached_run_results(run_id: str) -> dict[str, object] | None:
    cached = await get_redis_client().get(f"audit-result:{run_id}")
    return orjson.loads(cached) if cached else None


async def _load_run(session: AsyncSession, run_id: str) -> AuditRun:
    query = (
        select(AuditRun)
        .options(
            selectinload(AuditRun.dataset),
            selectinload(AuditRun.model),
            selectinload(AuditRun.project),
            selectinload(AuditRun.results),
        )
        .where(AuditRun.id == run_id)
    )
    run = (await session.execute(query)).scalar_one_or_none()
    if run is None:
        raise AppError(code="run_not_found", message="Audit run not found.", status_code=404)
    return run


async def _mark_running(session: AsyncSession, run: AuditRun) -> None:
    run.status = AuditRunStatus.RUNNING
    run.stage_label = "Computing fairness metrics..."
    run.error_message = None
    await session.commit()


async def _compute_run(session: AsyncSession, run: AuditRun):
    dataframe = storage_service.load_dataframe(Path(run.dataset.file_path), run.dataset.filename)
    loaded_model = None
    if run.model:
        loaded_model = storage_service.load_model(Path(run.model.file_path), run.model.model_type)
    engine = BiasAuditEngine()
    audit_input = AuditInput(
        dataframe=dataframe.reset_index(drop=True),
        target_column=run.dataset.target_column,
        protected_columns=run.dataset.protected_columns,
        positive_label=run.dataset.positive_label,
        prediction_column=run.dataset.prediction_column,
        score_column=run.dataset.score_column,
        thresholds=BiasThresholdConfig.model_validate(run.thresholds_json),
        loaded_model=loaded_model,
    )
    return engine.run(audit_input)


async def _persist_result(session: AsyncSession, run: AuditRun, result) -> None:
    await session.execute(delete(AuditResult).where(AuditResult.run_id == run.id))
    for metric in [*result.metrics, *result.intersectionality]:
        session.add(
            AuditResult(
                run_id=run.id,
                metric_name=metric.metric_name,
                group_name=metric.group_name,
                intersectional_groups=metric.intersectional_groups,
                value=metric.value,
                severity=metric.severity,
                threshold_used=metric.threshold_used,
                explanation=metric.explanation,
                details_json=_sanitize_json_value(metric.details),
            )
        )
    summary_json = _sanitize_json_value(result.summary)
    shap_json = _sanitize_json_value(result.shap_payload)
    proxy_matrix_json = _sanitize_json_value(
        {
            "matrix": result.proxy_matrix,
            "findings": [item.model_dump(mode="json") for item in result.proxy_findings],
        }
    )
    distributions_json = _sanitize_json_value(
        {
            "distributions": [item.model_dump(mode="json") for item in result.distributions],
            "missing_data_rates": result.missing_data_rates,
            "confusion_matrices": result.confusion_matrices,
            "calibration_curves": result.calibration_curves,
            "roc_curves": result.roc_curves,
            "intersectionality": [item.model_dump(mode="json") for item in result.intersectionality],
            "counterfactual": [item.model_dump(mode="json") for item in result.counterfactual],
        }
    )
    remediation_json = _sanitize_json_value([item.model_dump(mode="json") for item in result.recommendations])
    run.status = AuditRunStatus.COMPLETED
    run.stage_label = "Completed"
    run.bias_risk_score = result.bias_risk_score
    run.completed_at = datetime.now(UTC)
    run.summary_json = summary_json
    run.shap_json = shap_json
    run.proxy_matrix_json = proxy_matrix_json
    run.distributions_json = distributions_json
    run.remediation_json = remediation_json
    await session.commit()
    await session.refresh(run)


async def _cache_run_result(run_id: str, payload: dict[str, object]) -> None:
    await get_redis_client().setex(
        f"audit-result:{run_id}",
        60 * 60 * 24,
        orjson.dumps(_sanitize_json_value(payload)).decode("utf-8"),
    )
