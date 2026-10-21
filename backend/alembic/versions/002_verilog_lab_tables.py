"""Verilog laboratory sessions, runs, and messages."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "002_verilog_lab_tables"
down_revision: Union[str, None] = "001_initial_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lab_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=128), nullable=False),
        sa.Column("learner_key", sa.String(length=128), nullable=False),
        sa.Column("workspace_path", sa.String(length=1024), nullable=False),
        sa.Column("progress_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "lab_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("checkpoint_id", sa.String(length=32), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="queued"),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("artifact_path", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["lab_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "lab_messages",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("checkpoint_id", sa.String(length=32), nullable=False),
        sa.Column("run_id", sa.String(length=36), nullable=True),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("hint_level", sa.String(length=8), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["lab_runs.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["lab_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("lab_messages")
    op.drop_table("lab_runs")
    op.drop_table("lab_sessions")
