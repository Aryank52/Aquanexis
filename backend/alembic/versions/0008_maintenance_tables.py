"""Add maintenance and lifecycle tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision = '0008_maintenance_tables'
down_revision = '0007_notification_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # filter_catalog table
    op.create_table(
        'filter_catalog',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filter_identifier', sa.String(128), nullable=False),
        sa.Column('manufacturer', sa.String(128), nullable=False),
        sa.Column('product_name', sa.String(128), nullable=False),
        sa.Column('category', sa.String(32), nullable=False),
        sa.Column('purifier_compatibility', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('stage_position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('specifications', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('connector_details', sa.Text(), nullable=True),
        sa.Column('dimensions_mm', postgresql.JSONB(), nullable=True),
        sa.Column('rated_service_interval_days', sa.Integer(), nullable=True),
        sa.Column('rated_usage_volume_liters', sa.Float(), nullable=True),
        sa.Column('installation_requirements', sa.Text(), nullable=True),
        sa.Column('maintenance_instructions', sa.Text(), nullable=True),
        sa.Column('datasheet_reference', sa.String(256), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_filter_catalog_category_active', 'filter_catalog', ['category', 'is_active'])
    op.create_index('ix_filter_catalog_identifier', 'filter_catalog', ['filter_identifier'], unique=True)
    
    # installed_filters table
    op.create_table(
        'installed_filters',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('catalog_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage_position', sa.Integer(), nullable=False),
        sa.Column('installation_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('installer', sa.String(128), nullable=True),
        sa.Column('serial_number', sa.String(128), nullable=True),
        sa.Column('batch_identifier', sa.String(128), nullable=True),
        sa.Column('cumulative_volume_liters', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('operating_hours', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('lifecycle_state', sa.String(32), nullable=False, server_default='available'),
        sa.Column('previous_installation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('removal_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replacement_reason', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['catalog_id'], ['filter_catalog.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['previous_installation_id'], ['installed_filters.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_installed_filters_device_state', 'installed_filters', ['device_id', 'lifecycle_state'])
    op.create_index('ix_installed_filters_catalog', 'installed_filters', ['catalog_id'])
    op.create_index('ix_installed_filters_device_stage_state', 'installed_filters', ['device_id', 'stage_position', 'lifecycle_state'], 
                   postgresql_where=sa.text("lifecycle_state = 'installed'"), unique=True)
    
    # maintenance_events table
    op.create_table(
        'maintenance_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filter_instance_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('event_type', sa.String(16), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('initiated_by', sa.String(128), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('pre_maintenance_state', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('post_maintenance_state', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('evidence', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('verification_status', sa.String(16), nullable=True),
        sa.Column('correlation_id', sa.String(64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['filter_instance_id'], ['installed_filters.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_maintenance_events_device_type', 'maintenance_events', ['device_id', 'event_type'])
    op.create_index('ix_maintenance_events_timestamp', 'maintenance_events', ['timestamp'])
    op.create_index('ix_maintenance_events_correlation', 'maintenance_events', ['correlation_id'])
    
    # maintenance_workflows table
    op.create_table(
        'maintenance_workflows',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('maintenance_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('state', sa.String(32), nullable=False, server_default='requested'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['maintenance_event_id'], ['maintenance_events.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_maintenance_workflows_device_state', 'maintenance_workflows', ['device_id', 'state'])
    
    # calibration_records table
    op.create_table(
        'calibration_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sensor_id', sa.String(64), nullable=False),
        sa.Column('sensor_type', sa.String(32), nullable=False),
        sa.Column('calibration_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('calibration_method', sa.String(64), nullable=False),
        sa.Column('reference_standard', sa.String(128), nullable=False),
        sa.Column('reference_value', sa.Float(), nullable=False),
        sa.Column('measured_value', sa.Float(), nullable=False),
        sa.Column('correction_offset', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('tolerance', sa.Float(), nullable=False),
        sa.Column('result', sa.String(16), nullable=False),
        sa.Column('technician', sa.String(128), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('next_calibration_due', sa.DateTime(timezone=True), nullable=True),
        sa.Column('calibration_state', sa.String(16), nullable=False, server_default='unknown'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_calibration_records_device_type', 'calibration_records', ['device_id', 'sensor_type'])
    op.create_index('ix_calibration_records_due', 'calibration_records', ['next_calibration_due', 'calibration_state'])
    
    # calibration_policies table
    op.create_table(
        'calibration_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sensor_id', sa.String(64), nullable=False),
        sa.Column('sensor_type', sa.String(32), nullable=False),
        sa.Column('time_interval_days', sa.Integer(), nullable=True),
        sa.Column('usage_interval_measurements', sa.Integer(), nullable=True),
        sa.Column('usage_interval_volume_liters', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_calibration_policies_device_type', 'calibration_policies', ['device_id', 'sensor_type'])
    
    # verification_runs table
    op.create_table(
        'verification_runs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('maintenance_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('state', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('checks', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('overall_result', sa.Boolean(), nullable=True),
        sa.Column('failure_reasons', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('baseline_before', postgresql.JSONB(), nullable=True),
        sa.Column('baseline_after', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['maintenance_event_id'], ['maintenance_events.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_verification_runs_device_state', 'verification_runs', ['device_id', 'state'])
    
    # baseline_versions table
    op.create_table(
        'baseline_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('maintenance_event_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('metrics', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['maintenance_event_id'], ['maintenance_events.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_baseline_versions_device_active', 'baseline_versions', ['device_id', 'is_active'])
    op.create_unique_constraint('uq_device_baseline_version', 'baseline_versions', ['device_id', 'version'])
    
    # maintenance_recommendations table
    op.create_table(
        'maintenance_recommendations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filter_instance_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('trigger', sa.String(32), nullable=False),
        sa.Column('severity', sa.String(16), nullable=False, server_default='info'),
        sa.Column('evidence', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('urgency_days', sa.Integer(), nullable=True),
        sa.Column('recommended_action', sa.String(256), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['filter_instance_id'], ['installed_filters.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_maintenance_recommendations_device_severity', 'maintenance_recommendations', ['device_id', 'severity'])


def downgrade() -> None:
    op.drop_table('maintenance_recommendations')
    op.drop_table('baseline_versions')
    op.drop_table('verification_runs')
    op.drop_table('calibration_policies')
    op.drop_table('calibration_records')
    op.drop_table('maintenance_workflows')
    op.drop_table('maintenance_events')
    op.drop_table('installed_filters')
    op.drop_table('filter_catalog')