"""
Hydraulic Intelligence service - computes differential pressure, flow deviation, etc.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

from app.domain.filter_intelligence import HydraulicIntelligence


class HydraulicService:
    """Service for computing hydraulic intelligence metrics."""

    def __init__(self):
        # Default baselines - in production these would be learned per device
        self.default_baselines = {
            "flow_rate": 1.5,  # L/min
            "fill_time_minutes": 30.0,  # minutes to fill tank
        }

    def compute_hydraulic_intelligence(
        self,
        reading,
        previous_readings: List = None,
        device_baselines: Dict = None,
    ) -> "HydraulicIntelligence":
        """
        Compute hydraulic intelligence metrics from a reading.
        
        Args:
            reading: Current sensor reading
            previous_readings: List of previous readings for trend calculation
            device_baselines: Device-specific baselines (flow_rate, fill_time, etc.)
            
        Returns:
            HydraulicIntelligence object
        """
        baselines = self.default_baselines.copy()
        if device_baselines:
            baselines.update(device_baselines)
        
        # Differential pressure
        inlet_pressure = getattr(reading, 'pressure', None)  # inlet pressure
        outlet_pressure = getattr(reading, 'outlet_pressure', None)
        differential_pressure = None
        if inlet_pressure is not None and outlet_pressure is not None:
            differential_pressure = inlet_pressure - outlet_pressure
        elif inlet_pressure is not None:
            # If no outlet pressure, estimate from typical pressure drop
            differential_pressure = inlet_pressure * 0.15  # rough estimate
        
        # Flow deviation
        flow_rate = getattr(reading, 'flow_rate', None) or getattr(reading, 'flow', None)
        flow_deviation_pct = None
        if flow_rate is not None:
            baseline_flow = baselines.get("flow_rate", 1.5)
            if baseline_flow > 0:
                flow_deviation_pct = ((flow_rate - baseline_flow) / baseline_flow) * 100
        
        # Fill time deviation (requires tank level history)
        fill_time_deviation_pct = None
        if previous_readings and len(previous_readings) >= 2:
            # Estimate fill time from tank level changes
            fill_time_deviation_pct = self._estimate_fill_time_deviation(
                previous_readings, baselines.get("fill_time_minutes", 30.0)
            )
        
        # Pressure stability (volatility over window)
        pressure_stability = None
        pressure_trend = None
        if previous_readings and len(previous_readings) >= 5:
            pressures = [getattr(r, 'pressure', None) for r in previous_readings if getattr(r, 'pressure', None) is not None]
            if len(pressures) >= 5:
                pressure_stability = self._calculate_volatility(pressures)
                pressure_trend = self._calculate_trend(pressures)
        
        # Flow trend
        flow_trend = None
        if previous_readings and len(previous_readings) >= 5:
            flows = [getattr(r, 'flow_rate', None) or getattr(r, 'flow', None) for r in previous_readings]
            flows = [f for f in flows if f is not None]
            if len(flows) >= 5:
                flow_trend = self._calculate_trend(flows)
        
        return HydraulicIntelligence(
            device_id=getattr(reading, 'device_id', UUID(int=0)),
            timestamp=getattr(reading, 'timestamp', datetime.utcnow()),
            differential_pressure=differential_pressure,
            flow_deviation_pct=flow_deviation_pct,
            fill_time_deviation_pct=fill_time_deviation_pct,
            pressure_stability=pressure_stability,
            pressure_trend=pressure_trend,
            flow_trend=flow_trend,
            inlet_pressure=getattr(reading, 'pressure', None),
            outlet_pressure=getattr(reading, 'outlet_pressure', None),
            flow_rate=flow_rate,
            calculation_version="1.0",
        )
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate coefficient of variation as stability metric."""
        if len(values) < 2:
            return 0.0
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        return (std_dev / mean_val) * 100  # CV as percentage
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend (slope) per hour."""
        if len(values) < 2:
            return 0.0
        n = len(values)
        x = list(range(n))
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        if n * sum_x2 == sum_x * sum_x:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        # Convert to per-hour (assuming readings are ~1 minute apart)
        return slope * 60
    
    def _estimate_fill_time_deviation(
        self,
        readings: List,
        baseline_fill_time: float,
    ) -> Optional[float]:
        """Estimate fill time deviation from tank level changes."""
        # Find consecutive readings where tank level is increasing
        increasing_segments = []
        current_segment = []
        
        for i in range(1, len(readings)):
            prev_level = getattr(readings[i-1], 'tank_level', None)
            curr_level = getattr(readings[i], 'tank_level', None)
            prev_time = getattr(readings[i-1], 'timestamp', None)
            curr_time = getattr(readings[i], 'timestamp', None)
            
            if (prev_level is not None and curr_level is not None and 
                prev_time is not None and curr_time is not None and
                curr_level > prev_level):
                # Tank is filling
                level_change = curr_level - prev_level
                time_change = (curr_time - prev_time).total_seconds() / 60  # minutes
                if time_change > 0:
                    fill_rate = level_change / time_change  # % per minute
                    if fill_rate > 0:
                        estimated_fill_time = 100 / fill_rate  # minutes to fill 100%
                        current_segment.append(estimated_fill_time)
            elif current_segment:
                increasing_segments.append(current_segment)
                current_segment = []
        
        if current_segment:
            increasing_segments.append(current_segment)
        
        if not increasing_segments:
            return None
        
        # Average fill time from all segments
        all_estimates = [est for seg in increasing_segments for est in seg]
        if not all_estimates:
            return None
        
        avg_fill_time = sum(all_estimates) / len(all_estimates)
        if baseline_fill_time > 0:
            return ((avg_fill_time - baseline_fill_time) / baseline_fill_time) * 100
        return None