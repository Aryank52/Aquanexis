"""Initial schema - devices and sensor_readings tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Devices table
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('serial_number', sa.String(64), nullable=False),
        sa.Column('name', sa.String(128), nullable=True),
        sa.Column('firmware_version', sa.String(32), nullable=True),
        sa.Column('sensor_config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('calibration', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('safety_config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('status', sa.String(32), nullable=False, server_default='offline'),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('serial_number'),
    )
    op.create_index('ix_devices_status_last_seen', 'devices', ['status', 'last_seen'])

    # Sensor readings table
    op.create_table(
        'sensor_readings',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('tds', sa.Float(), nullable=True),
        sa.Column('ec', sa.Float(), nullable=True),
        sa.Column('ph', sa.Float(), nullable=True),
        sa.Column('turbidity', sa.Float(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('flow', sa.Float(), nullable=True),
        sa.Column('pressure', sa.Float(), nullable=True),
        sa.Column('tank_level', sa.Float(), nullable=True),
        sa.Column('leak_detected', sa.Boolean(), nullable=True),
        sa.Column('pump_current', sa.Float(), nullable=True),
        sa.Column('permeate_flow', sa.Float(), nullable=True),
        sa.Column('reject_flow', sa.Float(), nullable=True),
        sa.Column('uv_state', sa.Boolean(), nullable=True),
        sa.Column('vibration', sa.Float(), nullable=True),
        sa.Column('quality_flags', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('overall_quality', sa.String(16), nullable=False, server_default='GOOD'),
        sa.PrimaryKeyConstraint('device_id', 'timestamp', 'id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_sensor_readings_device_timestamp', 'sensor_readings', ['device_id', 'timestamp'])


def downgrade() -> None:
    op.drop_table('sensor_readings')
    op.drop_table('devices')