"""Add google_id to users and make hashed_password nullable for Google OAuth support.

Revision ID: 20260429_0002
Revises: 20260428_0001
Create Date: 2026-04-29
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260429_0002"
down_revision = "20260428_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make hashed_password nullable so Google-only accounts can exist without a password.
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(length=255),
        nullable=True,
    )
    # Add google_id column: stable, unique Google account identifier ("sub" claim).
    op.add_column(
        "users",
        sa.Column("google_id", sa.String(length=128), nullable=True),
    )
    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_google_id"), table_name="users")
    op.drop_column("users", "google_id")
    # Revert hashed_password to NOT NULL.
    # NOTE: rows with NULL hashed_password (Google-only users) must be removed
    # or assigned a placeholder before running downgrade.
    op.alter_column(
        "users",
        "hashed_password",
        existing_type=sa.String(length=255),
        nullable=False,
    )
