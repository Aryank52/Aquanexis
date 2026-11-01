"""Add derived data tables for water quality, filter health, diagnostics, performance"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0004_derived_data_tables'
down_revision = '0003_add_telemetry_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Water Quality Scores
    op.create_table(
        'water_quality_scores',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('overall_score', sa.SmallInteger(), nullable=False),
        sa.Column('tds_score', sa.SmallInteger(), nullable=True),
        sa.Column('ph_score', sa.SmallInteger(), nullable=True),
        sa.Column('turbidity_score', sa.SmallInteger(), nullable=True),
        sa.Column('temperature_score', sa.SmallInteger(), nullable=True),
        sa.Column('conductivity_score', sa.SmallInteger(), nullable=True),
        sa.Column('trends', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('anomaly_score', sa.Float(), nullable=True),
        sa.Column('anomaly_flags', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('device_id', 'timestamp', 'id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_wqs_device_timestamp', 'water_quality_scores', ['device_id', 'timestamp'])
    
    # Convert to hypertable
    op.execute("""
        SELECT create_hypertable('water_quality_scores', 'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE,
            migrate_data => TRUE);
    """)
    
    # Filter Health
    op.create_table(
        'filter_health',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fsi', sa.Float(), nullable=False),
        sa.Column('fhi', sa.Float(), nullable=False),
        sa.Column('rul_days', sa.Float(), nullable=True),
        sa.Column('rul_confidence_lower', sa.Float(), nullable=True),
        sa.Column('rul_confidence_upper', sa.Float(), nullable=True),
        sa.Column('model_name', sa.String(64), nullable=False),
        sa.Column('model_version', sa.String(32), nullable=False),
        sa.Column('dataset_version', sa.String(32), nullable=True),
        sa.Column('input_features', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('explanation', postgresql.JSONB(), nullable=True),
        sa.PrimaryKeyConstraint('device_id', 'timestamp', 'id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_fh_device_timestamp', 'filter_health', ['device_id', 'timestamp'])
    
    op.execute("""
        SELECT create_hypertable('filter_health', 'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE,
            migrate_data => TRUE);
    """)
    
    # System Diagnostics
    op.create_table(
        'system_diagnostics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('pressure_trend', sa.Float(), nullable=True),
        sa.Column('flow_trend', sa.Float(), nullable=True),
        sa.Column('leak_probability', sa.Float(), nullable=True),
        sa.Column('tank_fill_rate', sa.Float(), nullable=True),
        sa.Column('tank_empty_rate', sa.Float(), nullable=True),
        sa.Column('pump_efficiency', sa.Float(), nullable=True),
        sa.Column('pump_current_trend', sa.Float(), nullable=True),
        sa.Column('fouling_indicator', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('device_id', 'timestamp', 'id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_sd_device_timestamp', 'system_diagnostics', ['device_id', 'timestamp'])
    
    op.execute("""
        SELECT create_hypertable('system_diagnostics', 'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE,
            migrate_data => TRUE);
    """)
    
    # Purification Performance
    op.create_table(
        'purification_performance',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('rejection_rate', sa.Float(), nullable=True),
        sa.Column('recovery_ratio', sa.Float(), nullable=True),
        sa.Column('permeate_quality', sa.Float(), nullable=True),
        sa.Column('feed_quality', sa.Float(), nullable=True),
        sa.Column('efficiency', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('device_id', 'timestamp', 'id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_pp_device_timestamp', 'purification_performance', ['device_id', 'timestamp'])
    
    op.execute("""
        SELECT create_hypertable('purification_performance', 'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE,
            migrate_data => TRUE);
    """)


def downgrade() -> None:
    op.drop_table('purification_performance')
    op.drop_table('system_diagnostics')
    op.drop_table('filter_health')
    op.drop_table('water_quality_scores')