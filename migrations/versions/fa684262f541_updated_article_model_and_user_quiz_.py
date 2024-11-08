"""Updated Article model and user_quiz model with explicit constraint names

Revision ID: fa684262f541
Revises: 2e1ddcb3de90
Create Date: 2024-11-07 21:10:51.651271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa684262f541'
down_revision = '2e1ddcb3de90'
branch_labels = None
depends_on = None


def upgrade():
    # ### Commands to recreate the 'article' table with updated schema ###
    
    # 1. Create a new 'article_temp' table with the updated schema
    op.create_table(
        'article_temp',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(length=250), nullable=False, unique=True),  # New length and unique constraint
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('source', sa.String(length=200), nullable=False),
        sa.Column('date_posted', sa.DateTime, nullable=False)
    )

    # 2. Copy data from the existing 'article' table to 'article_temp'
    op.execute("""
        INSERT INTO article_temp (id, title, content, source, date_posted)
        SELECT id, title, content, source, date_posted FROM article
    """)

    # 3. Drop the old 'article' table
    op.drop_table('article')

    # 4. Rename 'article_temp' to 'article'
    op.rename_table('article_temp', 'article')


def downgrade():
    # ### Commands to revert the 'article' table to the original schema ###

    # 1. Create a new 'article_temp' table with the original schema
    op.create_table(
        'article_temp',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('title', sa.String(length=200), nullable=False),  # Original length and no unique constraint
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('source', sa.String(length=200), nullable=False),
        sa.Column('date_posted', sa.DateTime, nullable=False)
    )

    # 2. Copy data back from 'article' to 'article_temp'
    op.execute("""
        INSERT INTO article_temp (id, title, content, source, date_posted)
        SELECT id, title, content, source, date_posted FROM article
    """)

    # 3. Drop the modified 'article' table
    op.drop_table('article')

    # 4. Rename 'article_temp' back to 'article'
    op.rename_table('article_temp', 'article')