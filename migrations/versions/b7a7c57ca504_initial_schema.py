"""initial_schema

Revision ID: b7a7c57ca504
Revises:
Create Date: 2026-04-15 17:40:26.548741

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7a7c57ca504"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=True),
        sa.Column("language_code", sa.String(length=10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_telegram_id"), "users", ["telegram_id"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(op.f("ix_users_telegram_id"), table_name="users")
    op.drop_table("users")
