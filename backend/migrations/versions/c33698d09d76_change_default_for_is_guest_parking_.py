"""Change default for is_guest_parking_allowed to true

Revision ID: c33698d09d76
Revises: 094cccbfc8ad
Create Date: 2026-08-31 11:47:25.559625

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c33698d09d76'
down_revision: Union[str, Sequence[str], None] = '094cccbfc8ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('users', 'is_guest_parking_allowed', server_default=sa.text('true'))


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('users', 'is_guest_parking_allowed', server_default=sa.text('false'))
