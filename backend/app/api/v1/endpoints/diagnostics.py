"""
System Diagnostics API endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.security import get_device_claims, verify_api_key, rate_limit
from app.infrastructure.logging import get_logger
from app.models.system_diagnostics import SystemDiagnostics as DiagnosticsModel

logger = get_logger(__name__)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])
from app.models.system_diagnostics import SystemDiagnostics as DiagnosticsModel

logger = get_logger(__name__)

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


def _model_to_dict(model: DiagnosticsModel) -> dict:
    return {
        "id": model.id,
        "device_id": model.device_id,
        "timestamp": model.timestamp.isoformat(),
        "pressure_trend": model.pressure_trend,
        "flow_trend": model.flow_trend,
        "leak_probability": model.leak_probability,
        "tank_fill_rate": model.tank_fill_rate,
        "tank_empty_rate": model.tank_empty_rate,
        "pump_efficiency": model.pump_efficiency,
        "pump_current_trend": model.pump_current_trend,
        "fouling_indicator": model.fouling_indicator,
    }


@router.get("/{device_id}/current")
async def get_current_diagnostics(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(
        select(DiagnosticsModel)
        .where(DiagnosticsModel.device_id == device_id)
        .order_by(desc(DiagnosticsModel.timestamp))
        .limit(1)
    )
    diag = result.scalar_one_or_none()
    
    if not diag:
        raise HTTPException(status_code=404, detail="No diagnostics data for device")
    
    data = _model_to_dict(diag)
    data["data_freshness_seconds"] = int(
        (datetime.utcnow() - diag.timestamp).total_seconds()
    )
    return data


@router.get("/{device_id}/history")
async def get_diagnostics_history(
    device_id: UUID,
    start: datetime = Query(...),
    end: datetime = Query(...),
    interval: str = Query("1h"),
    limit: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if start >= end:
        raise HTTPException(status_code=400, detail="Start must be before end")
    
    if (end - start).total_seconds() > 30 * 24 * 3600:
        raise HTTPException(status_code=400, detail="Maximum range is 30 days")
    
    query = select(DiagnosticsModel).where(
        and_(
            DiagnosticsModel.device_id == device_id,
            DiagnosticsModel.timestamp >= start,
            DiagnosticsModel.timestamp <= end,
        )
    ).order_by(DiagnosticsModel.timestamp)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    if len(records) > limit:
        step = len(records) / limit
        records = [records[int(i * len(records) / limit)] for i in range(limit)]
    
    series = {}
    for record in records:
        ts = record.timestamp.isoformat()
        for param, value in [
            ("pressure_trend", record.pressure_trend),
            ("flow_trend", record.flow_trend),
            ("leak_probability", record.leak_probability),
            ("tank_fill_rate", record.tank_fill_rate),
            ("tank_empty_rate", record.tank_empty_rate),
            ("pump_efficiency", record.pump_efficiency),
            ("pump_current_trend", record.pump_current_trend),
            ("fouling_indicator", record.fouling_indicator),
        ]:
            if value is not None:
                if param not in series:
                    series[param] = []
                series[param].append({"timestamp": ts, "value": value})
    
    return {
        "device_id": device_id,
        "interval": interval,
        "series": series,
    }


@router.get("/{device_id}/pressure")
async def get_pressure_diagnostics(
    device_id: UUID,
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get pressure-related diagnostics
    query = select(DiagnosticsModel).where(
        and_(
            DiagnosticsModel.device_id == device_id,
            DiagnosticsModel.timestamp >= start,
            DiagnosticsModel.timestamp <= end,
        )
    ).order_by(DiagnosticsModel.timestamp)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    return {
        "device_id": device_id,
        "pressure_data": [
            {
                "timestamp": r.timestamp.isoformat(),
                "pressure_trend": r.pressure_trend,
                "fouling_indicator": r.fouling_indicator,
            }
            for r in records
        ],
    }


@router.get("/{device_id}/leak")
async def get_leak_diagnostics(
    device_id: UUID,
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = select(DiagnosticsModel).where(
        and_(
            DiagnosticsModel.device_id == device_id,
            DiagnosticsModel.timestamp >= start,
            DiagnosticsModel.timestamp <= end,
        )
    ).order_by(DiagnosticsModel.timestamp)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    return {
        "device_id": device_id,
        "leak_data": [
            {
                "timestamp": r.timestamp.isoformat(),
                "leak_probability": r.leak_probability,
            }
            for r in records
        ],
    }