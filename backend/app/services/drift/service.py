from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditRun
from app.models.enums import AuditRunStatus, SeverityLevel
from app.services.bias_engine.constants import DISPLAY_NAMES
from app.services.bias_engine.schemas import (
    DriftAlert,
    DriftMetricChange,
    DriftModelVersionSummary,
    DriftPeriodSummary,
    DriftRiskPoint,
    DriftSummary,
)

SEVERITY_ORDER = {
    SeverityLevel.GREEN: 0,
    SeverityLevel.AMBER: 1,
    SeverityLevel.RED: 2,
}


async def build_run_drift_summary(session: AsyncSession, run_id: str) -> DriftSummary:
    query = (
        select(AuditRun)
        .options(
            selectinload(AuditRun.results),
            selectinload(AuditRun.model),
            selectinload(AuditRun.dataset),
        )
        .where(AuditRun.id == run_id)
    )
    current_run = (await session.execute(query)).scalar_one()

    history_query = (
        select(AuditRun)
        .options(
            selectinload(AuditRun.results),
            selectinload(AuditRun.model),
            selectinload(AuditRun.dataset),
        )
        .where(
            AuditRun.project_id == current_run.project_id,
            AuditRun.status == AuditRunStatus.COMPLETED,
            AuditRun.bias_risk_score.is_not(None),
        )
        .order_by(AuditRun.completed_at.asc(), AuditRun.started_at.asc(), AuditRun.id.asc())
    )
    completed_runs = list((await session.execute(history_query)).scalars().all())
    history = [_risk_point(item, index) for index, item in enumerate(completed_runs)]
    previous_run = _previous_run(completed_runs, current_run.id)
    risk_delta = (
        round((current_run.bias_risk_score or 0.0) - (previous_run.bias_risk_score or 0.0), 2)
        if previous_run and current_run.bias_risk_score is not None and previous_run.bias_risk_score is not None
        else None
    )
    metric_drift = _metric_drift(current_run, previous_run)
    alerts = _build_alerts(current_run, previous_run, risk_delta, metric_drift)
    return DriftSummary(
        trend_status=_trend_status(risk_delta),
        risk_delta=risk_delta,
        compared_run_id=str(previous_run.id) if previous_run else None,
        compared_completed_at=previous_run.completed_at.isoformat() if previous_run and previous_run.completed_at else None,
        risk_history=history,
        period_summary=_period_summary(history),
        model_versions=_model_version_summary(completed_runs),
        metric_drift=metric_drift[:8],
        alerts=alerts,
    )


def _risk_point(run: AuditRun, index: int) -> DriftRiskPoint:
    completed_at = run.completed_at or run.started_at
    label = f"Run {index + 1}"
    if completed_at:
        label = completed_at.strftime("%b %d")
    return DriftRiskPoint(
        run_id=str(run.id),
        label=label,
        completed_at=completed_at.isoformat() if completed_at else "",
        bias_risk_score=round(run.bias_risk_score or 0.0, 2),
        model_label=run.model.filename if run.model else "Dataset-only audit",
        period_label=completed_at.strftime("%Y-%m-%d") if completed_at else "Unknown",
    )


def _previous_run(completed_runs: list[AuditRun], current_run_id: str) -> AuditRun | None:
    for index, run in enumerate(completed_runs):
        if str(run.id) != current_run_id:
            continue
        return completed_runs[index - 1] if index > 0 else None
    return None


def _metric_drift(current_run: AuditRun, previous_run: AuditRun | None) -> list[DriftMetricChange]:
    if previous_run is None:
        return []

    previous_metrics = {
        _metric_key(metric.metric_name, metric.group_name, metric.intersectional_groups): metric
        for metric in previous_run.results
    }
    drift: list[DriftMetricChange] = []
    for metric in current_run.results:
        key = _metric_key(metric.metric_name, metric.group_name, metric.intersectional_groups)
        previous_metric = previous_metrics.get(key)
        if previous_metric is None:
            continue
        delta = round(metric.value - previous_metric.value, 4)
        current_severity = metric.severity
        previous_severity = previous_metric.severity
        direction = "stable"
        current_distance = _fairness_distance(metric.metric_name, metric.value)
        previous_distance = _fairness_distance(previous_metric.metric_name, previous_metric.value)
        if SEVERITY_ORDER[current_severity] > SEVERITY_ORDER[previous_severity] or current_distance > previous_distance + 0.01:
            direction = "regressing"
        elif SEVERITY_ORDER[current_severity] < SEVERITY_ORDER[previous_severity] or current_distance < previous_distance - 0.01:
            direction = "improving"
        drift.append(
            DriftMetricChange(
                metric_name=metric.metric_name,
                display_name=DISPLAY_NAMES.get(metric.metric_name, metric.metric_name),
                group_name=metric.group_name,
                intersectional_groups=metric.intersectional_groups,
                current_value=round(metric.value, 4),
                previous_value=round(previous_metric.value, 4),
                delta=delta,
                current_severity=current_severity,
                previous_severity=previous_severity,
                direction=direction,
            )
        )
    drift.sort(
        key=lambda item: (
            1 if item.direction == "regressing" else 0,
            SEVERITY_ORDER[item.current_severity],
            abs(item.delta),
        ),
        reverse=True,
    )
    return drift


def _metric_key(metric_name: str, group_name: str, intersectional_groups: dict[str, str]) -> str:
    intersections = "|".join(
        f"{attribute}:{value}" for attribute, value in sorted(intersectional_groups.items())
    )
    return f"{metric_name}:{group_name}:{intersections}"


def _fairness_distance(metric_name: str, value: float) -> float:
    if metric_name.endswith("_ratio") or metric_name.endswith("_score"):
        return abs(1 - value)
    return abs(value)


def _period_summary(history: list[DriftRiskPoint]) -> list[DriftPeriodSummary]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for point in history:
        grouped[point.period_label].append(point.bias_risk_score)
    return [
        DriftPeriodSummary(
            period=period,
            average_risk_score=round(sum(scores) / len(scores), 2),
            runs=len(scores),
        )
        for period, scores in sorted(grouped.items())
    ]


def _model_version_summary(completed_runs: list[AuditRun]) -> list[DriftModelVersionSummary]:
    grouped: dict[str, list[AuditRun]] = defaultdict(list)
    for run in completed_runs:
        grouped[str(run.model_id or "dataset-only")].append(run)

    summaries: list[DriftModelVersionSummary] = []
    for model_key, runs in grouped.items():
        latest = runs[-1]
        scores = [run.bias_risk_score or 0.0 for run in runs]
        summaries.append(
            DriftModelVersionSummary(
                model_id=None if model_key == "dataset-only" else model_key,
                model_label=latest.model.filename if latest.model else "Dataset-only audit",
                average_risk_score=round(sum(scores) / len(scores), 2),
                latest_risk_score=round(latest.bias_risk_score or 0.0, 2),
                latest_completed_at=latest.completed_at.isoformat() if latest.completed_at else None,
                runs=len(runs),
            )
        )
    summaries.sort(key=lambda item: (item.latest_risk_score, item.runs), reverse=True)
    return summaries


def _trend_status(risk_delta: float | None) -> str:
    if risk_delta is None:
        return "insufficient_history"
    if risk_delta >= 5:
        return "regressing"
    if risk_delta <= -5:
        return "improving"
    return "stable"


def _build_alerts(
    current_run: AuditRun,
    previous_run: AuditRun | None,
    risk_delta: float | None,
    metric_drift: list[DriftMetricChange],
) -> list[DriftAlert]:
    alerts: list[DriftAlert] = []
    if previous_run is None:
        return alerts

    if risk_delta is not None and risk_delta >= 5:
        alerts.append(
            DriftAlert(
                title="Bias risk increased",
                body=(
                    f"Bias risk score rose by {risk_delta:.1f} points compared with the previous completed audit."
                ),
                severity=SeverityLevel.RED if risk_delta >= 10 else SeverityLevel.AMBER,
            )
        )

    worsening_metrics = [item for item in metric_drift if item.direction == "regressing"]
    if worsening_metrics:
        top = worsening_metrics[0]
        alerts.append(
            DriftAlert(
                title="Fairness metric worsened",
                body=(
                    f"{top.display_name} for {top.group_name} moved from {top.previous_value:.3f} "
                    f"to {top.current_value:.3f}."
                ),
                severity=top.current_severity,
            )
        )

    if not alerts and metric_drift:
        improving = [item for item in metric_drift if item.direction == "improving"]
        if improving:
            top = improving[0]
            alerts.append(
                DriftAlert(
                    title="Fairness improved",
                    body=(
                        f"{top.display_name} for {top.group_name} improved from {top.previous_value:.3f} "
                        f"to {top.current_value:.3f}."
                    ),
                    severity=SeverityLevel.GREEN,
                )
            )
    return alerts
