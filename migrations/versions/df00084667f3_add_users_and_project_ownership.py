"""add users and project ownership

Revision ID: df00084667f3
Revises: fc79218ffde3
Create Date: 2026-10-20 16:13:27.798648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df00084667f3'
down_revision: Union[str, Sequence[str], None] = 'fc79218ffde3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create the users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    # 2. Add owner_id as nullable temporarily
    op.add_column(
        "projects",
        sa.Column("owner_id", sa.Integer(), nullable=True),
    )

    # 3. Rebuild projects to add a named foreign key
    with op.batch_alter_table("projects") as batch_op:
        batch_op.create_foreign_key(
            "fk_projects_owner_id_users",
            "users",
            ["owner_id"],
            ["id"],
        )

    # 4. Existing projects have no owner yet.
    # We will assign them a real user during migration.
        # 5. Create a placeholder owner for legacy projects
    connection = op.get_bind()

    result = connection.execute(
        sa.text(
            """
            INSERT INTO users (email, hashed_password)
            VALUES (:email, :hashed_password)
            """
        ),
        {
            "email": "legacy-owner@migration.invalid",
            "hashed_password": "!disabled-migration-account!",
        },
    )

    legacy_owner_id = result.lastrowid

    # 6. Assign existing projects to that owner
    connection.execute(
        sa.text(
            """
            UPDATE projects
            SET owner_id = :owner_id
            WHERE owner_id IS NULL
            """
        ),
        {"owner_id": legacy_owner_id},
    )

    # 7. Make ownership mandatory
    with op.batch_alter_table("projects") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.create_foreign_key(
            "fk_projects_owner_id_users",
            "users",
            ["owner_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("projects") as batch_op:
        batch_op.drop_constraint(
            "fk_projects_owner_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("owner_id")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")