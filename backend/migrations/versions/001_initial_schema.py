"""Initial database schema with pgvector support

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Attempt to enable pgvector extension if running on PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Documents table
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=20), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False, default=0),
        sa.Column("processing_status", sa.String(length=20), nullable=False, default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_status", "documents", ["processing_status"])
    op.create_index("ix_documents_created_at", "documents", ["created_at"])

    # Document chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("embedding_json", sa.Text(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_document_chunks_doc_id", "document_chunks", ["document_id"])
    op.create_index("ix_document_chunks_index", "document_chunks", ["chunk_index"])

    # Processing jobs table
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(length=50), nullable=False, default="ingestion"),
        sa.Column("status", sa.String(length=20), nullable=False, default="pending"),
        sa.Column("attempt_count", sa.Integer(), nullable=False, default=0),
        sa.Column("max_attempts", sa.Integer(), nullable=False, default=3),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])
    op.create_index("ix_processing_jobs_created_at", "processing_jobs", ["created_at"])

    # Chat sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chat_sessions_created_at", "chat_sessions", ["created_at"])

    # Chat messages table
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("session_id", sa.String(length=36), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_index("ix_chat_messages_created_at", "chat_messages", ["created_at"])


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("processing_jobs")
    op.drop_table("document_chunks")
    op.drop_table("documents")
