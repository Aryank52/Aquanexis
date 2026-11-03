"""
Purification Performance service - computes rejection rate, recovery, efficiency.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from app.domain.filter_intelligence import (
    PurificationPerformance,
)


class PurificationService:
    """Service for computing purification performance metrics."""

    def __init__(self):
        pass

    def compute_purification_performance(
        self,
        reading,
        previous_reading=None,
    ) -> Optional["PurificationPerformance"]:
        """
        Compute purification performance from a reading.

        Requires:
        - TDS input (feed) and TDS output (permeate) for rejection rate
        - Permeate flow and reject flow for recovery ratio

        Returns None if required data is missing.
        """
        # Check for required data
        feed_tds = getattr(reading, "tds", None)
        permeate_tds = getattr(reading, "permeate_tds", None)
        feed_conductivity = getattr(reading, "conductivity", None)
        permeate_conductivity = getattr(reading, "permeate_conductivity", None)
        permeate_flow = getattr(reading, "permeate_flow", None)
        reject_flow = getattr(reading, "reject_flow", None)
        feed_flow = getattr(reading, "flow_rate", None) or getattr(reading, "flow", None)

        # Try to compute rejection rate
        rejection_rate = None
        if feed_tds is not None and permeate_tds is not None and feed_tds > 0:
            rejection_rate = ((feed_tds - permeate_tds) / feed_tds) * 100
        elif (
            feed_conductivity is not None
            and permeate_conductivity is not None
            and feed_conductivity > 0
        ):
            rejection_rate = ((feed_conductivity - permeate_conductivity) / feed_conductivity) * 100

        # Try to compute recovery ratio
        recovery_ratio = None
        if permeate_flow is not None and reject_flow is not None:
            total_flow = permeate_flow + reject_flow
            if total_flow > 0:
                recovery_ratio = (permeate_flow / total_flow) * 100
        elif permeate_flow is not None and feed_flow is not None and feed_flow > 0:
            recovery_ratio = (permeate_flow / feed_flow) * 100

        # If no metrics can be computed, return None
        if rejection_rate is None and recovery_ratio is None:
            return None

        # Calculate efficiency (simplified: rejection * recovery / 100)
        efficiency = None
        if rejection_rate is not None and recovery_ratio is not None:
            efficiency = (rejection_rate * recovery_ratio) / 100

        return PurificationPerformance(
            device_id=getattr(reading, "device_id", UUID(int=0)),
            timestamp=getattr(reading, "timestamp", datetime.utcnow()),
            rejection_rate=rejection_rate,
            recovery_ratio=recovery_ratio,
            feed_tds=feed_tds,
            permeate_tds=permeate_tds,
            feed_conductivity=feed_conductivity,
            permeate_conductivity=permeate_conductivity,
            permeate_flow=permeate_flow,
            reject_flow=reject_flow,
            feed_quality=feed_tds or feed_conductivity,
            permeate_quality=permeate_tds or permeate_conductivity,
            efficiency=efficiency,
            calculation_version="1.0",
        )

    def compute_recovery_from_flows(
        self,
        permeate_flow: Optional[float],
        reject_flow: Optional[float],
        feed_flow: Optional[float] = None,
    ) -> Optional[float]:
        """Compute recovery ratio from flow measurements."""
        if permeate_flow is not None and reject_flow is not None:
            total = permeate_flow + reject_flow
            if total > 0:
                return (permeate_flow / total) * 100
        if permeate_flow is not None and feed_flow is not None and feed_flow > 0:
            return (permeate_flow / feed_flow) * 100
        return None

    def compute_rejection_rate(
        self,
        feed_tds: Optional[float],
        permeate_tds: Optional[float],
        feed_conductivity: Optional[float] = None,
        permeate_conductivity: Optional[float] = None,
    ) -> Optional[float]:
        """Compute TDS/conductivity rejection rate."""
        if feed_tds is not None and permeate_tds is not None and feed_tds > 0:
            return ((feed_tds - permeate_tds) / feed_tds) * 100
        if (
            feed_conductivity is not None
            and permeate_conductivity is not None
            and feed_conductivity > 0
        ):
            return ((feed_conductivity - permeate_conductivity) / feed_conductivity) * 100
        return None
