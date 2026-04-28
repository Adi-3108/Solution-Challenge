from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.audit import AuditRun, Notification
from app.models.enums import NotificationType, SeverityLevel
from app.models.project import Project

logger = get_logger(__name__)


async def send_password_reset_email(destination: str, token: str) -> None:
    subject = "FairSight password reset"
    body = (
        "A password reset was requested for your FairSight account.\n\n"
        f"Use this token to complete the reset: {token}\n"
    )
    await _send_email(destination, subject, body)


async def notify_run_completion(session: AsyncSession, project_id: str, run: AuditRun) -> None:
    query = select(Notification).where(Notification.project_id == project_id, Notification.enabled.is_(True))
    notifications = (await session.execute(query)).scalars().all()
    red_issues = int(run.summary_json.get("red_issues", 0))
    tasks = []
    for notification in notifications:
        if notification.type == NotificationType.EMAIL and red_issues > 0:
            tasks.append(
                _send_email(
                    notification.destination,
                    "FairSight alert: bias detected",
                    _email_summary(project_id, run, red_issues),
                )
            )
        if notification.type == NotificationType.WEBHOOK:
            tasks.append(_send_webhook(notification.destination, project_id, run, red_issues))
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def _send_email(destination: str, subject: str, body: str) -> None:
    def send() -> None:
        message = EmailMessage()
        message["From"] = settings.smtp_from
        message["To"] = destination
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            if settings.smtp_user and settings.smtp_pass:
                smtp.starttls()
                smtp.login(settings.smtp_user, settings.smtp_pass)
            smtp.send_message(message)

    try:
        await asyncio.to_thread(send)
    except Exception:
        logger.warning("email_send_failed", destination_masked=True)


async def _send_webhook(destination: str, project_id: str, run: AuditRun, red_issues: int) -> None:
    payload = {
        "project_id": project_id,
        "run_id": run.id,
        "status": run.status.value,
        "bias_risk_score": run.bias_risk_score,
        "red_issues": red_issues,
    }
    try:
        async with httpx.AsyncClient(timeout=settings.webhook_timeout_seconds) as client:
            await client.post(destination, json=payload)
    except Exception:
        logger.warning("webhook_send_failed", destination_masked=True)


def _email_summary(project_id: str, run: AuditRun, red_issues: int) -> str:
    return (
        f"FairSight completed audit run {run.id} for project {project_id}.\n\n"
        f"Bias risk score: {run.bias_risk_score}\n"
        f"Red issues detected: {red_issues}\n"
        f"Stage: {run.stage_label}\n"
    )

