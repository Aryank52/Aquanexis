"""Add TimescaleDB hypertables for time-series tables"""
from alembic import op
import sqlalchemy as sa

revision = '0002_timescale_hypertables'
down_revision = '0001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # Convert sensor_readings to hypertable
    op.execute("""
        SELECT create_hypertable('sensor_readings', 'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE,
            migrate_data => TRUE);
    """)

    # Add compression for older chunks
    op.execute("""
        ALTER TABLE sensor_readings SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'device_id'
        );
    """)
    op.execute("SELECT add_compression_policy('sensor_readings', INTERVAL '7 days');")


def downgrade() -> None:
    # Remove compression policy
    op.execute("SELECT remove_compression_policy('sensor_readings', if_exists => TRUE);")
    op.execute("ALTER TABLE sensor_readings SET (timescaledb.compress = false);")

    # Drop hypertable (converts back to regular table)
    op.execute("SELECT drop_hypertable('sensor_readings', if_exists => TRUE);")

    # Drop extension (careful - only if no other hypertables)
    # op.execute("DROP EXTENSION IF EXISTS timescaledb CASCADE;")