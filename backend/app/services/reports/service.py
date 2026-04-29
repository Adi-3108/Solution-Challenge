from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

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
from app.services.llm.gemini import enrich_audit_payload


async def generate_report(session: AsyncSession, run_id: str, report_format: ReportFormat) -> Report:
    run = await _load_run(session, run_id)
    existing = await session.execute(
        select(Report).where(Report.run_id == run_id, Report.format == report_format)
    )
    report = existing.scalar_one_or_none()
    drift_summary = await build_run_drift_summary(session, run_id)
    payload = _build_report_payload(run, drift_summary.model_dump(mode="json"))
    enriched_payload = await enrich_audit_payload(payload)
    payload = enriched_payload or payload
    if report_format == ReportFormat.JSON:
        path = _write_json_report(run.id, payload)
    else:
        path = _write_pdf_report(run.id, payload)
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    generated_at = datetime.now(UTC)
    if report:
        report.file_path = str(path)
        report.file_hash = file_hash
        report.generated_at = generated_at
    else:
        report = Report(
            run_id=run.id,
            format=report_format,
            file_path=str(path),
            file_hash=file_hash,
            generated_at=generated_at,
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
        "analysis": run.distributions_json,
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
    width, _ = A4
    margin_x = 50
    top_margin = 800
    bottom_margin = 70
    line_height = 15
    y_position = top_margin

    def _new_page() -> None:
        nonlocal y_position
        pdf.showPage()
        y_position = top_margin
        pdf.setFont("Helvetica", 10)

    def _write_line(text: str, font: str = "Helvetica", size: int = 10) -> None:
        nonlocal y_position
        for chunk in _wrap_text(text, max_chars=115):
            if y_position < bottom_margin:
                _new_page()
            pdf.setFont(font, size)
            pdf.drawString(margin_x, y_position, chunk)
            y_position -= line_height

    def _write_blank(lines: int = 1) -> None:
        nonlocal y_position
        y_position -= line_height * lines
        if y_position < bottom_margin:
            _new_page()

    _write_line("FairSight Bias Audit Report", font="Helvetica-Bold", size=14)
    _write_blank()
    _write_line(f"Run ID: {run_id}")
    _write_line(f"Project: {payload['project_name']}")
    _write_line(f"Bias Risk Score: {payload['bias_risk_score']}")
    _write_line(f"Status: {payload.get('status')}")
    _write_line(f"Started: {payload.get('started_at')}")
    _write_line(f"Completed: {payload.get('completed_at')}")
    _write_blank()

    _write_line("Executive summary", font="Helvetica-Bold", size=12)
    for sentence in payload.get("executive_summary", []):
        _write_line(f"- {sentence}")
    _write_blank()

    _write_line("Flagged issues", font="Helvetica-Bold", size=12)
    flagged_issues = payload.get("flagged_issues", [])
    if not flagged_issues:
        _write_line("- No flagged issues.")
    for issue in flagged_issues:
        _write_line(
            f"- {issue['metric_name']} ({issue['group_name']}): {issue['severity']} at {issue['value']}"
        )
        if issue.get("explanation"):
            _write_line(f"  Why this matters: {issue['explanation']}")
    _write_blank()

    metrics = payload.get("metrics", [])
    if metrics:
        _write_line("All fairness metrics", font="Helvetica-Bold", size=12)
        for metric in metrics:
            _write_line(
                f"- {metric['metric_name']} ({metric['group_name']}): value {metric['value']}, "
                f"severity {metric['severity']}, threshold {metric['threshold']}"
            )
        _write_blank()

    analysis = payload.get("analysis", {})
    _write_analysis_section(_write_line, _write_blank, analysis)

    counterfactual = payload.get("counterfactual", [])
    if counterfactual:
        _write_line("Counterfactual fairness", font="Helvetica-Bold", size=12)
        for assessment in counterfactual:
            _write_line(
                f"- {assessment['protected_attribute']}: flip rate {assessment['flip_rate']:.3f}, "
                f"affected {assessment.get('affected_records', 0)}/{assessment.get('tested_pairs', 0)}, "
                f"source {assessment['source']}"
            )
            transitions = assessment.get("transition_summary", [])
            for transition in transitions:
                _write_line(
                    "  Transition "
                    f"{transition['from_group']} -> {transition['to_group']}: "
                    f"{transition['flipped']}/{transition['tested']} flipped ({transition['flip_rate']:.3f})"
                )
        _write_blank()

    recommendations = payload.get("recommendations", [])
    if recommendations:
        _write_line("Recommendations", font="Helvetica-Bold", size=12)
        for recommendation in recommendations:
            _write_line(
                f"- {recommendation['title']}: {recommendation['strategy']} "
                f"({recommendation['metric_name']} for {recommendation['affected_group']})"
            )
            _write_line(
                f"  Expected movement: {recommendation['before_value']} -> {recommendation['after_value']}"
            )
        _write_blank()

    drift = payload.get("drift", {})
    _write_line("Drift summary", font="Helvetica-Bold", size=12)
    _write_line(
        f"- Trend: {drift.get('trend_status')} | Risk delta: {drift.get('risk_delta')} | "
        f"Compared run: {drift.get('compared_run_id')}"
    )
    for item in drift.get("metric_drift", [])[:12]:
        _write_line(
            f"- {item['display_name']} ({item['group_name']}): {item['previous_value']} -> "
            f"{item['current_value']} ({item['direction']})"
        )
    alerts = drift.get("alerts", [])
    if alerts:
        _write_line("Drift alerts:")
        for alert in alerts:
            _write_line(f"- {alert['title']}: {alert['body']}")
    pdf.save()
    return destination


def _write_analysis_section(
    write_line: Callable[..., None], write_blank: Callable[..., None], analysis: dict[str, object]
) -> None:
    if not isinstance(analysis, dict):
        return
    distributions = analysis.get("distributions", [])
    intersectionality = analysis.get("intersectionality", [])
    calibration_curves = analysis.get("calibration_curves", {})
    roc_curves = analysis.get("roc_curves", {})
    if not any([distributions, intersectionality, calibration_curves, roc_curves]):
        return

    write_line("Analysis groups and diagnostics", font="Helvetica-Bold", size=12)

    if isinstance(distributions, list) and distributions:
        write_line("Group distributions:")
        for dist in distributions:
            attribute = dist.get("protected_attribute")
            groups = dist.get("groups", [])
            write_line(f"- {attribute}:")
            for group in groups:
                write_line(
                    f"  {group.get('group')}: count {group.get('count')}, "
                    f"positive_rate {group.get('positive_rate')}"
                )
        write_blank()

    if isinstance(intersectionality, list) and intersectionality:
        write_line("Intersectional analysis:")
        for item in intersectionality:
            intersections = item.get("intersectional_groups", {})
            if intersections:
                labels = ", ".join(f"{key}={value}" for key, value in intersections.items())
            else:
                labels = item.get("group_name")
            write_line(
                f"- {item.get('metric_name')} [{labels}]: value {item.get('value')}, "
                f"severity {item.get('severity')}"
            )
        write_blank()

    if isinstance(calibration_curves, dict) and calibration_curves:
        write_line("Calibration curves by group:")
        for group_name, points in _iter_curve_summary(calibration_curves):
            write_line(f"- {group_name}: {points}")
        write_blank()

    if isinstance(roc_curves, dict) and roc_curves:
        write_line("ROC curves by group:")
        for group_name, points in _iter_curve_summary(roc_curves):
            write_line(f"- {group_name}: {points}")
        write_blank()


def _iter_curve_summary(curve_data: dict[str, object]) -> Iterable[tuple[str, str]]:
    for group_name, points in curve_data.items():
        if isinstance(points, list):
            yield str(group_name), f"{len(points)} points"
        else:
            yield str(group_name), "not available"


def _wrap_text(text: str, max_chars: int) -> list[str]:
    words = str(text).split()
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        if len(f"{current} {word}") <= max_chars:
            current = f"{current} {word}"
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _report_destination(filename: str) -> Path:
    settings.pdf_report_path.mkdir(parents=True, exist_ok=True)
    return settings.pdf_report_path / filename
