"""Add name column to users table

Revision ID: add_name_to_users
Revises: 52a26c878bc0
Create Date: 2026-06-18

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_name_to_users'
down_revision = '52a26c878bc0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('name', sa.String(255), nullable=True))
    # Set default name from email prefix for existing users
    op.execute("UPDATE users SET name = split_part(email, '@', 1)")


def downgrade():
    op.drop_column('users', 'name')
