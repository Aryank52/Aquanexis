"""Add sequence column and update sensor_readings for Slice B telemetry"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0003_add_telemetry_fields'
down_revision = '0002_timescale_hypertables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add sequence column to sensor_readings
    op.add_column('sensor_readings', 
        sa.Column('sequence', sa.BigInteger(), nullable=True))
    
    # Add outlet_pressure column
    op.add_column('sensor_readings',
        sa.Column('outlet_pressure', sa.Float(), nullable=True))
    
    # Add permeate_flow, reject_flow (already exist but ensure)
    # Add pump_power
    op.add_column('sensor_readings',
        sa.Column('pump_power', sa.Float(), nullable=True))
    
    # Add index on device_id + sequence for deduplication
    op.create_index('ix_sensor_readings_device_sequence', 'sensor_readings', ['device_id', 'sequence'])
    
    # Add received_at column if not exists (should exist from initial schema)
    # op.add_column('sensor_readings', sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')))


def downgrade() -> None:
    op.drop_index('ix_sensor_readings_device_sequence', table_name='sensor_readings')
    op.drop_column('sensor_readings', 'sequence')
    op.drop_column('sensor_readings', 'outlet_pressure')
    op.drop_column('sensor_readings', 'pump_power')