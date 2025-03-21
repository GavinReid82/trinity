"""Remove UserTask table

Revision ID: 3b0fe02ef7d0
Revises: 
Create Date: 2025-03-18 13:09:41.448438

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '3b0fe02ef7d0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_tasks')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_tasks',
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('task_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('completed_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], name='user_tasks_task_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='user_tasks_user_id_fkey'),
    sa.PrimaryKeyConstraint('user_id', 'task_id', name='user_tasks_pkey')
    )
    # ### end Alembic commands ###
