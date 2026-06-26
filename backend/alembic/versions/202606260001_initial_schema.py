"""Initial schema.

Revision ID: 202606260001
Revises:
Create Date: 2026-06-26
"""

from alembic import op
import sqlalchemy as sa


revision = '202606260001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=255), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True),
        sa.Column('subscription_status', sa.String(length=50), nullable=False),
        sa.Column('plan', sa.String(length=50), nullable=False),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('has_active_subscription', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_stripe_customer_id'), 'users', ['stripe_customer_id'], unique=False)
    op.create_index(op.f('ix_users_stripe_subscription_id'), 'users', ['stripe_subscription_id'], unique=False)

    op.create_table(
        'content_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_content_items_id'), 'content_items', ['id'], unique=False)

    op.create_table(
        'stripe_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stripe_event_id', sa.String(length=255), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_event_id', name='uq_stripe_event_id'),
    )
    op.create_index(op.f('ix_stripe_events_id'), 'stripe_events', ['id'], unique=False)
    op.create_index(op.f('ix_stripe_events_stripe_event_id'), 'stripe_events', ['stripe_event_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_stripe_events_stripe_event_id'), table_name='stripe_events')
    op.drop_index(op.f('ix_stripe_events_id'), table_name='stripe_events')
    op.drop_table('stripe_events')
    op.drop_index(op.f('ix_content_items_id'), table_name='content_items')
    op.drop_table('content_items')
    op.drop_index(op.f('ix_users_stripe_subscription_id'), table_name='users')
    op.drop_index(op.f('ix_users_stripe_customer_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
