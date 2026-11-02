"""Add notification tables"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

revision = '0007_notification_tables'
down_revision = '0006_safety_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # notification_outbox table
    op.create_table(
        'notification_outbox',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.String(16), nullable=False),
        sa.Column('provider', sa.String(32), nullable=False),
        sa.Column('recipient', sa.String(256), nullable=False),
        sa.Column('subject', sa.String(256), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('template_name', sa.String(64), nullable=True),
        sa.Column('template_data', postgresql.JSONB(), nullable=True),
        sa.Column('dedupe_key', sa.String(128), nullable=False),
        sa.Column('status', sa.String(16), nullable=False, server_default='pending'),
        sa.Column('error_category', sa.String(16), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['alert_id'], ['alerts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_notification_outbox_device_status', 'notification_outbox', ['device_id', 'status'])
    op.create_index('ix_notification_outbox_alert_channel', 'notification_outbox', ['alert_id', 'channel'])
    op.create_index('ix_notification_outbox_next_attempt', 'notification_outbox', ['next_attempt_at', 'status'])
    op.create_index('ix_notification_outbox_dedupe', 'notification_outbox', ['dedupe_key'], unique=True)
    
    # notification_provider_config table
    op.create_table(
        'notification_provider_config',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('channel', sa.String(16), nullable=False),
        sa.Column('provider', sa.String(32), nullable=False),
        sa.Column('enabled', sa.JSON(), nullable=False, server_default='true'),
        sa.Column('config', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('min_severity', sa.String(16), nullable=False, server_default='info'),
        sa.Column('alert_codes', sa.JSON(), nullable=True),
        sa.Column('rate_limit_per_hour', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_notification_provider_config_device_channel', 'notification_provider_config', ['device_id', 'channel'], unique=True)
    
    # notification_template table
    op.create_table(
        'notification_template',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(64), nullable=False),
        sa.Column('channel', sa.String(16), nullable=False),
        sa.Column('subject_template', sa.String(256), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.JSON(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notification_template_name', 'notification_template', ['name'], unique=True)
    op.create_index('ix_notification_template_channel', 'notification_template', ['channel'])
    
    # Insert default templates
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    # Default console template
    op.execute(f"""
        INSERT INTO notification_template (id, name, channel, subject_template, body_template, description, is_default, created_at, updated_at)
        VALUES (
            '{uuid.uuid4()}',
            'default',
            'console',
            'AquaNexis Alert: {{ alert_code }}',
            'Alert: {{ title }}\\nSeverity: {{ severity }}\\nDevice: {{ device_id }}\\nTime: {{ created_at }}\\n\\n{{ message }}\\n\\nTrigger: {{ trigger_source }}\\nValue: {{ trigger_value }}\\nThreshold: {{ threshold_value }}\\n\\nEvidence: {{ evidence }}',
            'Default template for all alert types',
            true,
            '{now.isoformat()}',
            '{now.isoformat()}'
        )
    """)
    
    # Leak detected template
    op.execute(f"""
        INSERT INTO notification_template (id, name, channel, subject_template, body_template, description, is_default, created_at, updated_at)
        VALUES (
            '{uuid.uuid4()}',
            'leak_detected',
            'console',
            '🚨 CRITICAL: Leak Detected - Device {{ device_id }}',
            'CRITICAL ALERT: Water leak detected!\\n\\nDevice: {{ device_id }}\\nTime: {{ created_at }}\\n\\n{{ message }}\\n\\nIMMEDIATE ACTION REQUIRED: Check the device location for water accumulation.\\nThe system may have automatically closed the inlet valve.\\n\\nTrigger: {{ trigger_source }}\\nEvidence: {{ evidence }}',
            'Template for leak detected alerts',
            true,
            '{now.isoformat()}',
            '{now.isoformat()}'
        )
    """)
    
    # Pressure high template
    op.execute(f"""
        INSERT INTO notification_template (id, name, channel, subject_template, body_template, description, is_default, created_at, updated_at)
        VALUES (
            '{uuid.uuid4()}',
            'pressure_high',
            'console',
            '🚨 CRITICAL: High Pressure - Device {{ device_id }}',
            'CRITICAL ALERT: Excessive pressure detected!\\n\\nDevice: {{ device_id }}\\nTime: {{ created_at }}\\n\\n{{ message }}\\n\\nThe system may have automatically opened the relief valve or stopped the pump.\\n\\nTrigger: {{ trigger_source }}\\nValue: {{ trigger_value }}\\nThreshold: {{ threshold_value }}',
            'Template for high pressure alerts',
            true,
            '{now.isoformat()}',
            '{now.isoformat()}'
        )
    """)
    
    # Pump overcurrent template
    op.execute(f"""
        INSERT INTO notification_template (id, name, channel, subject_template, body_template, description, is_default, created_at, updated_at)
        VALUES (
            '{uuid.uuid4()}',
            'pump_overcurrent',
            'console',
            '🚨 CRITICAL: Pump Overcurrent - Device {{ device_id }}',
            'CRITICAL ALERT: Pump overcurrent detected!\\n\\nDevice: {{ device_id }}\\nTime: {{ created_at }}\\n\\n{{ message }}\\n\\nThe system may have automatically stopped the pump to prevent damage.\\n\\nTrigger: {{ trigger_source }}\\nValue: {{ trigger_value }}\\nThreshold: {{ threshold_value }}',
            'Template for pump overcurrent alerts',
            true,
            '{now.isoformat()}',
            '{now.isoformat()}'
        )
    """)
    
    # Water quality degraded template
    op.execute(f"""
        INSERT INTO notification_template (id, name, channel, subject_template, body_template, description, is_default, created_at, updated_at)
        VALUES (
            '{uuid.uuid4()}',
            'water_quality_degraded',
            'console',
            '⚠️ WARNING: Water Quality Degraded - Device {{ device_id }}',
            'WARNING: Water quality has degraded.\\n\\nDevice: {{ device_id }}\\nTime: {{ created_at }}\\n\\n{{ message }}\\n\\nTrigger: {{ trigger_source }}\\nValue: {{ trigger_value }}\\nThreshold: {{ threshold_value }}\\n\\nConsider checking or replacing filters.',
            'Template for water quality degraded alerts',
            true,
            '{now.isoformat()}',
            '{now.isoformat()}'
        )
    """)
    
    # Filter health critical template
    op.execute(f"""
        INSERT INTO notification_template (id, name, channel, subject_template, body_template, description, is_default, created_at, updated_at)
        VALUES (
            '{uuid.uuid4()}',
            'filter_health_critical',
            'console',
            '🚨 CRITICAL: Filter Health Critical - Device {{ device_id }}',
            'CRITICAL ALERT: Filter health is critical!\\n\\nDevice: {{ device_id }}\\nTime: {{ created_at }}\\n\\n{{ message }}\\n\\nFilter replacement is urgently required.\\n\\nTrigger: {{ trigger_source }}\\nValue: {{ trigger_value }}\\nThreshold: {{ threshold_value }}',
            'Template for filter health critical alerts',
            true,
            '{now.isoformat()}',
            '{now.isoformat()}'
        )
    """)


def downgrade() -> None:
    op.drop_table('notification_template')
    op.drop_table('notification_provider_config')
    op.drop_table('notification_outbox')