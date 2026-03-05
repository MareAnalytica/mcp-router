"""Add trust_level, source, repo_url to mcp_servers

Revision ID: 002
Revises: 001
Create Date: 2026-03-05

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("mcp_servers", sa.Column("trust_level", sa.String(20), nullable=True, server_default="unverified"))
    op.add_column("mcp_servers", sa.Column("source", sa.String(100), nullable=True))
    op.add_column("mcp_servers", sa.Column("repo_url", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("mcp_servers", "repo_url")
    op.drop_column("mcp_servers", "source")
    op.drop_column("mcp_servers", "trust_level")
