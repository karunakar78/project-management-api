"""add created_at to projects

Revision ID: fc79218ffde3
Revises: 5cfa0f320742
Create Date: 2026-10-13 21:38:16.537934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc79218ffde3'
down_revision: Union[str, Sequence[str], None] = '5cfa0f320742'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add the column as nullable first.
    op.add_column(
        "projects",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True
        )
    )

    # 2. Give existing projects a timestamp.
    op.execute(
        "UPDATE projects "
        "SET created_at = CURRENT_TIMESTAMP "
        "WHERE created_at IS NULL"
    )

    # 3. Enforce the final schema.
    # Batch mode safely rebuilds the table for SQLite.
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column(
            "created_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP")
        )


def downgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_column("created_at")
