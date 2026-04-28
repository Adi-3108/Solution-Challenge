"""Initial FairSight schema."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260428_0001"
down_revision = None
branch_labels = None
depends_on = None


user_role = postgresql.ENUM("admin", "analyst", "viewer", name="user_role", create_type=False)
audit_run_status = postgresql.ENUM("queued", "running", "completed", "failed", name="audit_run_status", create_type=False)
severity_level = postgresql.ENUM("green", "amber", "red", name="severity_level", create_type=False)
report_format = postgresql.ENUM("pdf", "json", name="report_format", create_type=False)
notification_type = postgresql.ENUM("email", "webhook", name="notification_type", create_type=False)
model_type = postgresql.ENUM("pkl", "joblib", "onnx", name="model_type", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    audit_run_status.create(bind, checkfirst=True)
    severity_level.create(bind, checkfirst=True)
    report_format.create(bind, checkfirst=True)
    notification_type.create(bind, checkfirst=True)
    model_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "projects",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "datasets",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("col_count", sa.Integer(), nullable=False),
        sa.Column("target_column", sa.String(length=255), nullable=False),
        sa.Column("protected_columns", sa.JSON(), nullable=False),
        sa.Column("positive_label", sa.String(length=255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("column_types", sa.JSON(), nullable=False),
        sa.Column("prediction_column", sa.String(length=255), nullable=True),
        sa.Column("score_column", sa.String(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_datasets_file_hash"), "datasets", ["file_hash"], unique=False)

    op.create_table(
        "model_artifacts",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("model_type", model_type, nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_model_artifacts_file_hash"), "model_artifacts", ["file_hash"], unique=False)

    op.create_table(
        "audit_runs",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("model_id", sa.Uuid(), nullable=True),
        sa.Column("status", audit_run_status, nullable=False),
        sa.Column("bias_risk_score", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("stage_label", sa.String(length=255), nullable=False),
        sa.Column("thresholds_json", sa.JSON(), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("shap_json", sa.JSON(), nullable=False),
        sa.Column("proxy_matrix_json", sa.JSON(), nullable=False),
        sa.Column("distributions_json", sa.JSON(), nullable=False),
        sa.Column("remediation_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["model_id"], ["model_artifacts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_results",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("group_name", sa.String(length=255), nullable=False),
        sa.Column("intersectional_groups", sa.JSON(), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("severity", severity_level, nullable=False),
        sa.Column("threshold_used", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["audit_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "reports",
        sa.Column("run_id", sa.Uuid(), nullable=False),
        sa.Column("format", report_format, nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["audit_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("action", sa.String(length=255), nullable=False),
        sa.Column("resource_type", sa.String(length=255), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notifications",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("type", notification_type, nullable=False),
        sa.Column("destination", sa.String(length=500), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("reports")
    op.drop_table("audit_results")
    op.drop_table("audit_runs")
    op.drop_index(op.f("ix_model_artifacts_file_hash"), table_name="model_artifacts")
    op.drop_table("model_artifacts")
    op.drop_index(op.f("ix_datasets_file_hash"), table_name="datasets")
    op.drop_table("datasets")
    op.drop_table("projects")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    model_type.drop(bind, checkfirst=True)
    notification_type.drop(bind, checkfirst=True)
    report_format.drop(bind, checkfirst=True)
    severity_level.drop(bind, checkfirst=True)
    audit_run_status.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
