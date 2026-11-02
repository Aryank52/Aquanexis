"""
Baseline Service - computes and maintains historical baselines for sensor readings.
Supports rolling baselines with configurable windows and minimum sample requirements.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from collections import defaultdict
import statistics

from app.domain.filter_intelligence import (
    BaselineMetrics,
    BaselineStatus,
    BaselineConfig,
    DEFAULT_BASELINE_CONFIG,
)
from app.models.reading import SensorReading as SensorReadingModel
from app.infrastructure.database import get_db
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class BaselineService:
    """Service for computing and maintaining historical baselines."""
    
    def __init__(self, config: BaselineConfig = None):
        self.config = config or DEFAULT_BASELINE_CONFIG
        # In-memory cache for baselines (in production, use Redis or DB)
        self._baseline_cache: Dict[UUID, Tuple[BaselineStatus, datetime]] = {}
    
    async def get_baseline_status(self, device_id: UUID) -> BaselineStatus:
        """Get current baseline status for a device."""
        # Check cache first
        if device_id in self._baseline_cache:
            status, cached_at = self._baseline_cache[device_id]
            if datetime.utcnow() - cached_at < timedelta(hours=1):
                return status
        
        # Compute fresh baseline
        status = await self._compute_baseline()
        self._baseline_cache[device_id] = (status, datetime.utcnow())
        return status
    
    async def _compute_baseline(self, device_id: UUID) -> BaselineStatus:
        """Compute baseline metrics from recent readings."""
        from app.infrastructure.database import get_db
        
        async with get_db() as db:
            cutoff = datetime.utcnow() - timedelta(hours=self.config.window_hours)
            
            # Query recent readings
            from app.models.reading import SensorReading as SensorReadingModel
            from sqlalchemy import select, and_, desc
            
            result = await db.execute(
                select(SensorReadingModel)
                .where(
                    and_(
                        SensorReadingModel.device_id == device_id,
                        SensorReadingModel.timestamp >= cutoff,
                    )
                )
                .order_by(SensorReadingModel.timestamp)
            )
            readings = result.scalars().all()
            
            if len(readings) < self.config.min_samples_for_baseline:
                return BaselineStatus(
                    device_id=device_id,
                    is_established=False,
                    needed_samples=self.config.min_samples_for_baseline - len(readings),
                    status="BASELINE_ESTABLISHING",
                )
            
            # Calculate baseline metrics
            flow_values = [r.flow for r in readings if r.flow is not None]
            pressure_values = [r.pressure for r in readings if r.pressure is not None]
            outlet_pressure_values = [r.outlet_pressure for r in readings if r.outlet_pressure is not None]
            turbidity_values = [r.turbidity for r in readings if r.turbidity is not None]
            tds_values = [r.tds for r in readings if r.tds is not None]
            
            # Calculate daily volume (sum of flow * time intervals)
            daily_volume = 0.0
            if len(readings) >= 2:
                for i in range(1, len(readings)):
                    prev = readings[i-1]
                    curr = readings[i]
                    if prev.flow and curr.flow and prev.timestamp and curr.timestamp:
                        avg_flow = (prev.flow + curr.flow) / 2
                        hours = (curr.timestamp - prev.timestamp).total_seconds() / 3600
                        daily_volume += avg_flow * hours
            
            # Calculate differential pressure baseline
            delta_pressure_values = []
            for r in readings:
                if r.pressure is not None and r.outlet_pressure is not None:
                    delta = r.pressure - r.outlet_pressure
                    delta_pressure_values.append(delta)
            
            metrics = BaselineMetrics(
                device_id=device_id,
                timestamp=datetime.utcnow(),
                window_hours=self.config.window_hours,
                sample_count=len(readings),
                flow_baseline_lpm=statistics.mean(flow_values) if flow_values else None,
                pressure_baseline_kpa=statistics.mean(pressure_values) if pressure_values else None,
                outlet_pressure_baseline_kpa=statistics.mean(outlet_pressure_values) if outlet_pressure_values else None,
                delta_pressure_baseline_kpa=statistics.mean(delta_pressure_values) if delta_pressure_values else None,
                turbidity_baseline_ntu=statistics.mean(turbidity_values) if turbidity_values else None,
                tds_baseline_ppm=statistics.mean(tds_values) if tds_values else None,
                daily_volume_baseline_l=daily_volume if daily_volume > 0 else None,
                pressure_stability_cv=self._calculate_cv(pressure_values) if pressure_values else None,
                flow_stability_cv=self._calculate_cv(flow_values) if flow_values else None,
                sufficient_samples=True,
                calculation_version="1.0",
            )
            
            return BaselineStatus(
                device_id=device_id,
                is_established=True,
                metrics=metrics,
                needed_samples=0,
                status="ESTABLISHED",
            )
    
    def _calculate_cv(self, values: List[float]) -> Optional[float]:
        """Calculate coefficient of variation (std/mean * 100)."""
        if len(values) < 2:
            return None
        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0.0
        stdev = statistics.stdev(values)
        return (stdev / mean_val) * 100
    
    async def update_baselines(self, device_ids: List[UUID] = None):
        """Update baselines for all devices or specific devices."""
        from app.infrastructure.database import get_db
        from app.models.device import Device as DeviceModel
        from sqlalchemy import select
        
        if device_ids is None:
            async with get_db() as db:
                result = await db.execute(select(DeviceModel.id))
                device_ids = [row[0] for row in result.fetchall()]
        
        for device_id in device_ids:
            # Invalidate cache
            if device_id in self._baseline_cache:
                del self._baseline_cache[device_id]
            # Recompute
            await self.get_baseline_status(device_id)
    
    async def get_baseline_metrics(self, device_id: UUID) -> Optional[dict]:
        """Get baseline metrics as dict for API response."""
        status = await self.get_baseline_status(device_id)
        if not status.is_established or not status.metrics:
            return None
        
        m = status.metrics
        return {
            "flow_baseline_lpm": m.flow_baseline_lpm,
            "pressure_baseline_kpa": m.pressure_baseline_kpa,
            "delta_pressure_baseline_kpa": m.delta_pressure_baseline_kpa,
            "turbidity_baseline_ntu": m.turbidity_baseline_ntu,
            "tds_baseline_ppm": m.tds_baseline_ppm,
            "daily_volume_baseline_l": m.daily_volume_baseline_l,
            "pressure_stability_cv": m.pressure_stability_cv,
            "flow_stability_cv": m.flow_stability_cv,
            "window_hours": m.window_hours,
            "sample_count": m.sample_count,
            "last_updated": m.timestamp.isoformat(),
            "calculation_version": m.calculation_version,
        }