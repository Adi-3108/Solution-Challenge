from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.errors import AppError
from app.models.audit import AuditRun
from app.models.enums import ReportFormat
from app.models.report import Report
from app.services.drift.service import build_run_drift_summary


async def generate_report(session: AsyncSession, run_id: str, report_format: ReportFormat) -> Report:
    run = await _load_run(session, run_id)
    existing = await session.execute(
        select(Report).where(Report.run_id == run_id, Report.format == report_format)
    )
    report = existing.scalar_one_or_none()
    if report:
        return report
    drift_summary = await build_run_drift_summary(session, run_id)
    payload = _build_report_payload(run, drift_summary.model_dump(mode="json"))
    if report_format == ReportFormat.JSON:
        path = _write_json_report(run.id, payload)
    else:
        path = _write_pdf_report(run.id, payload)
    report = Report(
        run_id=run.id,
        format=report_format,
        file_path=str(path),
        file_hash=hashlib.sha256(path.read_bytes()).hexdigest(),
        generated_at=datetime.now(UTC),
    )
    session.add(report)
    await session.commit()
    await session.refresh(report)
    return report


async def _load_run(session: AsyncSession, run_id: str) -> AuditRun:
    query = (
        select(AuditRun)
        .options(
            selectinload(AuditRun.dataset),
            selectinload(AuditRun.model),
            selectinload(AuditRun.results),
            selectinload(AuditRun.project),
        )
        .where(AuditRun.id == run_id)
    )
    run = (await session.execute(query)).scalar_one_or_none()
    if run is None:
        raise AppError(code="run_not_found", message="Audit run not found.", status_code=404)
    return run


def _build_report_payload(run: AuditRun, drift_summary: dict[str, object]) -> dict[str, object]:
    flagged = [
        {
            "metric_name": result.metric_name,
            "group_name": result.group_name,
            "value": result.value,
            "severity": result.severity.value,
            "explanation": result.explanation,
        }
        for result in run.results
        if result.severity.value != "green"
    ]
    counterfactual = run.distributions_json.get("counterfactual", [])
    return {
        "executive_summary": [
            "FairSight reviewed this dataset and any associated predictions for differences in outcomes across protected groups. The bias risk score summarizes how many fairness checks failed and how severe the gaps appear to be.",
            "The findings below highlight which groups are affected, why the issue matters, and which remediation steps can reduce risk before deployment or policy use.",
        ],
        "run_id": run.id,
        "project_name": run.project.name,
        "bias_risk_score": run.bias_risk_score,
        "status": run.status.value,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "dataset_hash": run.dataset.file_hash,
        "model_hash": run.model.file_hash if run.model else None,
        "flagged_issues": flagged,
        "counterfactual": counterfactual,
        "drift": drift_summary,
        "metrics": [
            {
                "metric_name": result.metric_name,
                "group_name": result.group_name,
                "value": result.value,
                "severity": result.severity.value,
                "threshold": result.threshold_used,
            }
            for result in run.results
        ],
        "recommendations": run.remediation_json,
        "summary": run.summary_json,
    }


def _write_json_report(run_id: str, payload: dict[str, object]) -> Path:
    destination = _report_destination(f"{run_id}.json")
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def _write_pdf_report(run_id: str, payload: dict[str, object]) -> Path:
    destination = _report_destination(f"{run_id}.pdf")
    pdf = canvas.Canvas(str(destination), pagesize=A4)
    y_position = 800
    lines = [
        "FairSight Bias Audit Report",
        f"Run ID: {run_id}",
        f"Project: {payload['project_name']}",
        f"Bias Risk Score: {payload['bias_risk_score']}",
        "",
        "Executive summary:",
        *payload["executive_summary"],
        "",
        "Flagged issues:",
    ]
    for issue in payload["flagged_issues"][:12]:
        lines.append(
            f"- {issue['metric_name']} ({issue['group_name']}): {issue['severity']} at {issue['value']}"
        )
    counterfactual = payload.get("counterfactual", [])
    if counterfactual:
        lines.extend(
            [
                "",
                "Counterfactual fairness:",
            ]
        )
        for assessment in counterfactual[:4]:
            lines.append(
                f"- {assessment['protected_attribute']}: flip rate {assessment['flip_rate']:.3f}, source {assessment['source']}"
            )
    drift = payload.get("drift", {})
    alerts = drift.get("alerts", [])
    if alerts:
        lines.extend(["", "Drift alerts:"])
        for alert in alerts[:4]:
            lines.append(f"- {alert['title']}: {alert['body']}")
    for line in lines:
        pdf.drawString(50, y_position, line[:110])
        y_position -= 18
        if y_position < 80:
            pdf.showPage()
            y_position = 800
    pdf.save()
    return destination


def _report_destination(filename: str) -> Path:
    settings.pdf_report_path.mkdir(parents=True, exist_ok=True)
    return settings.pdf_report_path / filename
