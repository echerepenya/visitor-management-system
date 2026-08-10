"""add parking_settings

Revision ID: b5b5c91f1a23
Revises: ab9406f7855f
Create Date: 2026-07-27 11:32:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b5b5c91f1a23'
down_revision = 'ab9406f7855f'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('parking_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('spots_offset', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('parking_settings')
