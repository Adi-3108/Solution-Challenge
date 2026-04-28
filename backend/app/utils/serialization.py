from __future__ import annotations

from sqlalchemy import inspect

from app.models.audit import AuditRun
from app.models.dataset import Dataset, ModelArtifact
from app.models.project import Project


def dataset_to_dict(dataset: Dataset) -> dict[str, object]:
    return {
        "id": dataset.id,
        "filename": dataset.filename,
        "file_hash": dataset.file_hash,
        "row_count": dataset.row_count,
        "col_count": dataset.col_count,
        "target_column": dataset.target_column,
        "protected_columns": dataset.protected_columns,
        "positive_label": dataset.positive_label,
        "prediction_column": dataset.prediction_column,
        "score_column": dataset.score_column,
        "uploaded_at": dataset.uploaded_at.isoformat(),
        "expires_at": dataset.expires_at.isoformat(),
        "column_types": dataset.column_types,
    }


def model_to_dict(model: ModelArtifact) -> dict[str, object]:
    return {
        "id": model.id,
        "filename": model.filename,
        "file_hash": model.file_hash,
        "model_type": model.model_type.value,
        "uploaded_at": model.uploaded_at.isoformat(),
    }


def run_to_dict(run: AuditRun) -> dict[str, object]:
    return {
        "id": run.id,
        "project_id": run.project_id,
        "dataset_id": run.dataset_id,
        "model_id": run.model_id,
        "status": run.status.value,
        "bias_risk_score": run.bias_risk_score,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error_message": run.error_message,
        "stage_label": run.stage_label,
        "summary": run.summary_json,
    }


def project_to_dict(project: Project) -> dict[str, object]:
    state = inspect(project)
    loaded_runs = [] if "audit_runs" in state.unloaded else list(project.audit_runs)
    runs = sorted(
        loaded_runs,
        key=lambda item: item.started_at or item.completed_at or project.created_at,
        reverse=True,
    )
    latest_run = runs[0] if runs else None
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "archived_at": project.archived_at.isoformat() if project.archived_at else None,
        "last_run_date": (
            (latest_run.completed_at or latest_run.started_at).isoformat()
            if latest_run and (latest_run.completed_at or latest_run.started_at)
            else None
        ),
        "last_run_status": latest_run.status.value if latest_run else None,
        "risk_score": latest_run.bias_risk_score if latest_run else None,
        "run_count": len(loaded_runs),
    }
