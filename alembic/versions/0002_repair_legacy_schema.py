"""repair legacy schema drift

Revision ID: 0002_repair_legacy_schema
Revises: 0001_initial
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0002_repair_legacy_schema"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(idx["name"] == index_name for idx in indexes)


def upgrade() -> None:
    if not _column_exists("users", "created_at"):
        op.add_column("users", sa.Column("created_at", sa.DateTime(), nullable=True))
    if not _column_exists("users", "updated_at"):
        op.add_column("users", sa.Column("updated_at", sa.DateTime(), nullable=True))

    if not _column_exists("transactions", "created_at"):
        op.add_column("transactions", sa.Column("created_at", sa.DateTime(), nullable=True))
    if not _column_exists("transactions", "updated_at"):
        op.add_column("transactions", sa.Column("updated_at", sa.DateTime(), nullable=True))

    if not _index_exists("transactions", "ix_transactions_user_id_date"):
        op.create_index("ix_transactions_user_id_date", "transactions", ["user_id", "date"], unique=False)


def downgrade() -> None:
    if _index_exists("transactions", "ix_transactions_user_id_date"):
        op.drop_index("ix_transactions_user_id_date", table_name="transactions")

    if _column_exists("transactions", "updated_at"):
        op.drop_column("transactions", "updated_at")
    if _column_exists("transactions", "created_at"):
        op.drop_column("transactions", "created_at")

    if _column_exists("users", "updated_at"):
        op.drop_column("users", "updated_at")
    if _column_exists("users", "created_at"):
        op.drop_column("users", "created_at")
