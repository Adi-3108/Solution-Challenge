from __future__ import annotations

import asyncio
import hashlib
import shutil
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.models.audit import AuditRun
from app.models.dataset import Dataset
from app.models.enums import AuditRunStatus, ReportFormat, UserRole
from app.models.project import Project
from app.models.user import User
from app.services.audit.service import execute_audit_run
from app.services.bias_engine.schemas import BiasThresholdConfig
from app.services.reports.service import generate_report

configure_logging()
logger = get_logger(__name__)

FIXTURE_PATH = Path(__file__).resolve().parent / "tests" / "fixtures" / "adult_census_biased.csv"


async def main() -> None:
    from app.core.database import SessionLocal
    from app.core.config import settings

    settings.file_storage_path.mkdir(parents=True, exist_ok=True)
    settings.pdf_report_path.mkdir(parents=True, exist_ok=True)

    async with SessionLocal() as session:
        admin = await _ensure_user(session, "admin@fairsight.demo", UserRole.ADMIN)
        analyst = await _ensure_user(session, "analyst@fairsight.demo", UserRole.ANALYST)
        await _ensure_user(session, "viewer@fairsight.demo", UserRole.VIEWER)
        project = await _ensure_project(session, analyst.id)
        dataset = await _ensure_dataset(session, project.id)

        existing_run = await session.execute(
            select(AuditRun).where(
                AuditRun.project_id == project.id,
                AuditRun.dataset_id == dataset.id,
                AuditRun.status == AuditRunStatus.COMPLETED,
            )
        )
        run = existing_run.scalar_one_or_none()
        if run is None:
            run = AuditRun(
                project_id=project.id,
                dataset_id=dataset.id,
                model_id=None,
                status=AuditRunStatus.QUEUED,
                started_at=datetime.now(UTC),
                stage_label="Analyzing distributions...",
                thresholds_json=BiasThresholdConfig().model_dump(mode="json"),
            )
            session.add(run)
            await session.commit()
            await session.refresh(run)

    await execute_audit_run(run.id, "seed-script")

    from app.core.database import SessionLocal

    async with SessionLocal() as session:
        await generate_report(session, run.id, ReportFormat.PDF)
        await generate_report(session, run.id, ReportFormat.JSON)
        logger.info("seed_complete", admin_id=admin.id, analyst_id=analyst.id, run_id=run.id)


async def _ensure_user(session: AsyncSession, email: str, role: UserRole) -> User:
    existing = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        return existing
    user = User(email=email, hashed_password=hash_password("Demo1234!"), role=role)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def _ensure_project(session: AsyncSession, user_id: str) -> Project:
    existing = (
        await session.execute(
            select(Project).where(Project.user_id == user_id, Project.name == "ACME Corp Hiring Model")
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    project = Project(
        user_id=user_id,
        name="ACME Corp Hiring Model",
        description="Demo project seeded from the biased adult census fixture to showcase mixed fairness outcomes.",
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def _ensure_dataset(session: AsyncSession, project_id: str) -> Dataset:
    existing = (
        await session.execute(
            select(Dataset).where(Dataset.project_id == project_id, Dataset.filename == FIXTURE_PATH.name)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    from app.core.config import settings

    content = FIXTURE_PATH.read_bytes()
    destination = settings.file_storage_path / "datasets" / f"{uuid4()}.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(FIXTURE_PATH, destination)
    dataframe = pd.read_csv(FIXTURE_PATH)
    dataset = Dataset(
        project_id=project_id,
        filename=FIXTURE_PATH.name,
        file_path=str(destination),
        file_hash=hashlib.sha256(content).hexdigest(),
        row_count=int(len(dataframe.index)),
        col_count=int(len(dataframe.columns)),
        target_column="hired",
        protected_columns=["gender", "race"],
        positive_label="1",
        uploaded_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=30),
        column_types={column: str(dtype) for column, dtype in dataframe.dtypes.items()},
        prediction_column="predicted_hired",
        score_column="score",
    )
    session.add(dataset)
    await session.commit()
    await session.refresh(dataset)
    return dataset


if __name__ == "__main__":
    asyncio.run(main())
