"""Add canonical telemetry contract fields to sensor_readings"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0009_canonical_telemetry_fields"
down_revision = "0008_maintenance_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sensor_readings",
        sa.Column("provenance", sa.String(32), nullable=False, server_default="SIMULATED"),
    )
    op.add_column(
        "sensor_readings",
        sa.Column("firmware_version", sa.String(64), nullable=True),
    )
    op.add_column(
        "sensor_readings",
        sa.Column("calibration_state", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "sensor_readings",
        sa.Column("units", postgresql.JSONB(), nullable=False, server_default="{}"),
    )
    op.add_column(
        "sensor_readings",
        sa.Column("device_state", sa.String(32), nullable=False, server_default="ACTIVE"),
    )


def downgrade() -> None:
    op.drop_column("sensor_readings", "device_state")
    op.drop_column("sensor_readings", "units")
    op.drop_column("sensor_readings", "calibration_state")
    op.drop_column("sensor_readings", "firmware_version")
    op.drop_column("sensor_readings", "provenance")

