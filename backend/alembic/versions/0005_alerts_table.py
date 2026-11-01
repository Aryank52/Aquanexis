"""Add alerts table"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0005_alerts_table'
down_revision = '0004_derived_data_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_code', sa.String(64), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False, server_default='info'),
        sa.Column('status', sa.String(16), nullable=False, server_default='detected'),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('trigger_source', sa.String(64), nullable=False),
        sa.Column('trigger_value', postgresql.JSONB(), nullable=True),
        sa.Column('threshold_value', postgresql.JSONB(), nullable=True),
        sa.Column('evidence', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('snoozed_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('auto_cleared_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(128), nullable=True),
        sa.Column('acknowledged_by', sa.String(128), nullable=True),
        sa.Column('resolved_by', sa.String(128), nullable=True),
        sa.Column('rule_version', sa.String(32), nullable=True),
        sa.Column('last_evaluated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_alerts_device_status', 'alerts', ['device_id', 'status'])
    op.create_index('ix_alerts_device_code_status', 'alerts', ['device_id', 'alert_code', 'status'])
    op.create_index('ix_alerts_created_at', 'alerts', ['created_at'])
    op.create_index('ix_alerts_severity_status', 'alerts', ['severity', 'status'])
    op.create_index('ix_alerts_alert_code', 'alerts', ['alert_code'])


def downgrade() -> None:
    op.drop_table('alerts')