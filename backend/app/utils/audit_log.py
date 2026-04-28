from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def create_audit_log(
    session: AsyncSession,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    metadata: dict[str, object] | None = None,
) -> None:
    session.add(
        AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata or {},
            created_at=datetime.now(UTC),
        )
    )

