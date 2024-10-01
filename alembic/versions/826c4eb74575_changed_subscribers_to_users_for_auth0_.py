"""Changed subscribers to users for auth0 integration

Revision ID: 826c4eb74575
Revises: daf35f3683b7
Create Date: 2024-10-01 09:21:55.528015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '826c4eb74575'
down_revision: Union[str, None] = 'daf35f3683b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('auth0_id', sa.String(length=64), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('is_premium', sa.Boolean(), nullable=False),
    sa.Column('premium_expiry', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('last_login', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('auth0_id'),
    sa.UniqueConstraint('email')
    )
    op.drop_table('subscribers')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('subscribers',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('email', sa.VARCHAR(length=120), nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('1'), nullable=False),
    sa.Column('date_joined', sa.DATETIME(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.Column('last_login', sa.DATETIME(), nullable=True),
    sa.Column('login_token', sa.VARCHAR(length=64), nullable=True),
    sa.Column('token_expiry', sa.DATETIME(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('login_token')
    )
    op.drop_table('users')
    # ### end Alembic commands ###
