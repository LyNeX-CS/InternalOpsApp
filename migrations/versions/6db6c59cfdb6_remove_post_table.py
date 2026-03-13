"""remove post table

Revision ID: 6db6c59cfdb6
Revises: f4e62e8bd11b
Create Date: 2026-03-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6db6c59cfdb6'
down_revision = 'f4e62e8bd11b'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table('post')


def downgrade():
    op.create_table(
        'post',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('body', sa.String(length=140), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_post_timestamp', 'post', ['timestamp'], unique=False)
    op.create_index('ix_post_user_id', 'post', ['user_id'], unique=False)