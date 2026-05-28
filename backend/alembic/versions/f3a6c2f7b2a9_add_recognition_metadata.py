"""add recognition metadata

Revision ID: f3a6c2f7b2a9
Revises: d1b581a0817d
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa

revision = "f3a6c2f7b2a9"
down_revision = "d1b581a0817d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("recognition_logs", sa.Column("mood_scores_json", sa.JSON(), nullable=True))
    op.add_column("recognition_logs", sa.Column("snapshot_path", sa.String(length=512), nullable=True))
    op.add_column("recognition_logs", sa.Column("quality_score", sa.Float(), nullable=True))
    op.add_column("recognition_logs", sa.Column("low_light_score", sa.Float(), nullable=True))
    op.add_column("recognition_logs", sa.Column("pose_score", sa.Float(), nullable=True))
    op.add_column("recognition_logs", sa.Column("size_score", sa.Float(), nullable=True))


def downgrade():
    op.drop_column("recognition_logs", "size_score")
    op.drop_column("recognition_logs", "pose_score")
    op.drop_column("recognition_logs", "low_light_score")
    op.drop_column("recognition_logs", "quality_score")
    op.drop_column("recognition_logs", "snapshot_path")
    op.drop_column("recognition_logs", "mood_scores_json")
