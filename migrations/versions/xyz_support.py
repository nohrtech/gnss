"""Add XYZ support fields

Revision ID: xyz_support
Create Date: 2024-03-15
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

def upgrade():
    op.add_column('analysis_result', sa.Column('solution_quality', JSON))
    op.add_column('analysis_result', sa.Column('xyz_stats', JSON))

def downgrade():
    op.drop_column('analysis_result', 'solution_quality')
    op.drop_column('analysis_result', 'xyz_stats')
