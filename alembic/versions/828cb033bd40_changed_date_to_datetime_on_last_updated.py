"""Changed Date to DateTime on last_updated

Revision ID: 828cb033bd40
Revises: 684b3ef11949
Create Date: 2024-09-30 19:09:08.704741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '828cb033bd40'
down_revision: Union[str, None] = '684b3ef11949'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

def upgrade():
    # Get the table names
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # For each table that has a last_updated column
    for table in tables:
        columns = [col['name'] for col in inspector.get_columns(table)]
        if 'last_updated' in columns:
            # Create a new temporary table
            with op.batch_alter_table(table, recreate='always') as batch_op:
                batch_op.alter_column('last_updated',
                               existing_type=sa.DATE(),
                               type_=sa.DateTime(),
                               existing_nullable=True)

def downgrade():
    # If you need to roll back, you'd convert DATETIME back to DATE
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    for table in tables:
        columns = [col['name'] for col in inspector.get_columns(table)]
        if 'last_updated' in columns:
            with op.batch_alter_table(table, recreate='always') as batch_op:
                batch_op.alter_column('last_updated',
                               existing_type=sa.DateTime(),
                               type_=sa.DATE(),
                               existing_nullable=True)
