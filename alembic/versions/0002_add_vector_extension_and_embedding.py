"""Add pgvector extension and embedding column

Revision ID: 0002_add_vector_extension_and_embedding
Revises: b85b06cc6fab
Create Date: 2026-09-11 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_vec_emb'
down_revision = 'b85b06cc6fab'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        # create extension and add vector column with configurable dimension
        dim = int(op.get_context().config.get_main_option('emb_dimension') or 1536)
        op.execute('CREATE EXTENSION IF NOT EXISTS vector;')
        # ensure documents table exists (create minimal table if missing)
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR(64) PRIMARY KEY,
                content TEXT NOT NULL,
                source VARCHAR(256)
            );
            """
        )
        op.execute(f'ALTER TABLE documents ADD COLUMN IF NOT EXISTS embedding vector({dim});')


def downgrade():
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        op.execute('ALTER TABLE documents DROP COLUMN IF EXISTS embedding;')
        # don't drop extension to avoid removing it if shared
