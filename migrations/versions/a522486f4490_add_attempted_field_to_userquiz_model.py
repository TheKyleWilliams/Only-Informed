"""Add attempted field to UserQuiz model

Revision ID: a522486f4490
Revises: 6eb6ffaceee1
Create Date: 2024-12-04 16:25:15.926443

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a522486f4490'
down_revision = '6eb6ffaceee1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_quiz', schema=None) as batch_op:
        batch_op.add_column(sa.Column('attempted', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_quiz', schema=None) as batch_op:
        batch_op.drop_column('attempted')

    # ### end Alembic commands ###
