"""ensure_bigint_ids

Revision ID: e1a2b3c4d5e6
Revises: fd40c080f91a
Create Date: 2026-04-17 02:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "fd40c080f91a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure USERS table uses BigInteger for telegram_id
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "telegram_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )

    # Ensure ADMINS table uses BigInteger for telegram_id and chat_id
    with op.batch_alter_table("admins", schema=None) as batch_op:
        batch_op.alter_column(
            "telegram_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )

    # Ensure CHANNEL_SETTINGS table uses BigInteger for channel_id
    with op.batch_alter_table("channel_settings", schema=None) as batch_op:
        batch_op.alter_column(
            "channel_id",
            existing_type=sa.Integer(),
            type_=sa.BigInteger(),
            existing_nullable=False,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("channel_settings", schema=None) as batch_op:
        batch_op.alter_column(
            "channel_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("admins", schema=None) as batch_op:
        batch_op.alter_column(
            "chat_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "telegram_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.alter_column(
            "telegram_id",
            existing_type=sa.BigInteger(),
            type_=sa.Integer(),
            existing_nullable=False,
        )
