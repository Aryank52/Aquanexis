"""Add safety tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0006_safety_tables'
down_revision = '0005_alerts_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # safety_config table
    op.create_table(
        'safety_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('leak_action', sa.String(32), nullable=False, server_default='close_inlet_valve'),
        sa.Column('leak_validate_with', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('leak_cooldown_sec', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('leak_persistence_readings', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('pressure_max_kpa', sa.Float(), nullable=False, server_default='600.0'),
        sa.Column('pressure_action', sa.String(32), nullable=False, server_default='close_inlet_valve'),
        sa.Column('pressure_cooldown_sec', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('pressure_min_kpa', sa.Float(), nullable=False, server_default='50.0'),
        sa.Column('pressure_action_low', sa.String(32), nullable=False, server_default='open_inlet_valve'),
        sa.Column('flow_min_lpm', sa.Float(), nullable=False, server_default='0.1'),
        sa.Column('dry_run_action', sa.String(32), nullable=False, server_default='stop_pump'),
        sa.Column('dry_run_cooldown_sec', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('flow_unstable_threshold_pct', sa.Float(), nullable=False, server_default='20.0'),
        sa.Column('pump_current_max_a', sa.Float(), nullable=False, server_default='2.5'),
        sa.Column('overcurrent_action', sa.String(32), nullable=False, server_default='stop_pump'),
        sa.Column('overcurrent_cooldown_sec', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('pump_power_max_w', sa.Float(), nullable=False, server_default='2000.0'),
        sa.Column('persistence_required_readings', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('cooldown_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('cooldown_by_code', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('device_id', name='uq_safety_config_device'),
    )
    op.create_index('ix_safety_config_device', 'safety_config', ['device_id'])

    # safety_action table
    op.create_table(
        'safety_action',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_type', sa.String(32), nullable=False),
        sa.Column('trigger_code', sa.String(32), nullable=False),
        sa.Column('trigger_value', postgresql.JSONB(), nullable=True),
        sa.Column('threshold_value', postgresql.JSONB(), nullable=True),
        sa.Column('action_taken', sa.String(64), nullable=False),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('idempotency_key', sa.String(128), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_safety_action_device', 'safety_action', ['device_id'])
    op.create_index('ix_safety_action_executed', 'safety_action', ['executed_at'])
    op.create_index('ix_safety_action_idempotency', 'safety_action', ['idempotency_key'], unique=True)

    # safety_cooldown table
    op.create_table(
        'safety_cooldown',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action_code', sa.String(32), nullable=False),
        sa.Column('cooldown_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('device_id', 'action_code', name='uq_safety_cooldown_device_action'),
    )
    op.create_index('ix_safety_cooldown_device_until', 'safety_cooldown', ['device_id', 'cooldown_until'])


def downgrade() -> None:
    op.drop_table('safety_cooldown')
    op.drop_table('safety_action')
    op.drop_table('safety_config')