"""Add login fields to Subscriber model

Revision ID: 684b3ef11949
Revises: feba1deeed79
Create Date: 2024-09-30 18:14:03.852054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '684b3ef11949'
down_revision: Union[str, None] = 'feba1deeed79'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create new tables with desired structure
    op.create_table('new_feedback',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True)
    )
    
    op.create_table('new_subscribers',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True, autoincrement=True),
        sa.Column('email', sa.String(length=120), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('date_joined', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('login_token', sa.String(length=64), nullable=True, unique=True),
        sa.Column('token_expiry', sa.DateTime(), nullable=True)
    )

    # Copy data from old tables to new tables
    op.execute('INSERT INTO new_feedback SELECT id, content, timestamp FROM feedback')
    op.execute('INSERT INTO new_subscribers (id, email, date_joined) SELECT id, email, date_joined FROM subscribers')

    # Drop old tables
    op.drop_table('feedback')
    op.drop_table('subscribers')

    # Rename new tables to original names
    op.rename_table('new_feedback', 'feedback')
    op.rename_table('new_subscribers', 'subscribers')

    # Update transport_budget table
    with op.batch_alter_table('transport_budget', schema=None) as batch_op:
        batch_op.alter_column('last_updated',
               existing_type=sa.DATE(),
               type_=sa.DateTime(),
               existing_nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))

    # We're removing the changes to the universities table
    # as we want to keep english_name nullable


def downgrade() -> None:
    # This downgrade function is simplified and may not perfectly reverse the upgrade
    # It's generally safer to restore from a backup when downgrading
    
    with op.batch_alter_table('transport_budget', schema=None) as batch_op:
        batch_op.alter_column('last_updated',
               existing_type=sa.DateTime(),
               type_=sa.DATE(),
               existing_nullable=True,
               existing_server_default=sa.text('(CURRENT_TIMESTAMP)'))

    with op.batch_alter_table('subscribers', schema=None) as batch_op:
        batch_op.drop_column('token_expiry')
        batch_op.drop_column('login_token')
        batch_op.drop_column('last_login')
        batch_op.drop_column('is_active')

    # We don't need to modify the feedback table in the downgrade
    # as the changes are compatible with the previous version
