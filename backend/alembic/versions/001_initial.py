"""initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("full_name", sa.String(180), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(32), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_role", "users", ["role"])
    op.create_index("idx_users_active", "users", ["is_active"])

    op.create_table(
        "datasets",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_path", sa.String(512), nullable=True),
        sa.Column("total_images", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_images", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(40), nullable=False, server_default="pending"),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_datasets_status", "datasets", ["status"])

    op.create_table(
        "persons",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("person_code", sa.String(64), nullable=False),
        sa.Column("full_name", sa.String(180), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("department", sa.String(120), nullable=True),
        sa.Column("title", sa.String(120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("primary_image_path", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("embedding_model", sa.String(80), nullable=False, server_default="insightface_buffalo_l"),
        sa.Column("duplicate_of", sa.BigInteger(), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("person_code"),
    )
    op.create_index("idx_persons_name", "persons", ["full_name"])
    op.create_index("idx_persons_active", "persons", ["is_active"])

    op.create_table(
        "face_samples",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("person_id", sa.BigInteger(), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_path", sa.String(512), nullable=False),
        sa.Column("crop_path", sa.String(512), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("blur_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("low_light_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("detection_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("embedding_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_face_samples_person", "face_samples", ["person_id"])
    op.create_index("idx_face_samples_hash", "face_samples", ["embedding_hash"])

    op.create_table(
        "face_embeddings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("sample_id", sa.BigInteger(), sa.ForeignKey("face_samples.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", sa.BigInteger(), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("embedding_dim", sa.Integer(), nullable=False),
        sa.Column("embedding_vector", sa.LargeBinary(), nullable=False),
        sa.Column("similarity_threshold", sa.Float(), nullable=False, server_default="0.45"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_face_embeddings_person", "face_embeddings", ["person_id"])
    op.create_index("idx_face_embeddings_sample", "face_embeddings", ["sample_id"])

    op.create_table(
        "recognition_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("person_id", sa.BigInteger(), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("person_name", sa.String(180), nullable=True),
        sa.Column("source_type", sa.String(40), nullable=False),
        sa.Column("source_ref", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("distance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_unknown", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("frame_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("bounding_box_json", sa.JSON(), nullable=True),
        sa.Column("embedding_hash", sa.String(64), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_recognition_logs_person", "recognition_logs", ["person_id"])
    op.create_index("idx_recognition_logs_unknown", "recognition_logs", ["is_unknown"])
    op.create_index("idx_recognition_logs_occurred", "recognition_logs", ["occurred_at"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("actor_user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.String(80), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("idx_audit_actor", "audit_logs", ["actor_user_id"])
    op.create_index("idx_audit_action", "audit_logs", ["action"])
    op.create_index("idx_audit_created", "audit_logs", ["created_at"])

def downgrade():
    for t in ["audit_logs","recognition_logs","face_embeddings","face_samples","persons","datasets","users"]:
        op.drop_table(t)
