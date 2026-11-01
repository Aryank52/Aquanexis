"""
Purification Performance API endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.infrastructure.database import get_db
from app.infrastructure.security import get_device_claims, verify_api_key, rate_limit
from app.infrastructure.logging import get_logger
from app.models.purification_performance import PurificationPerformance as PPModel

logger = get_logger(__name__)

router = APIRouter(prefix="/purification-performance", tags=["purification-performance"])


def _model_to_dict(model: PPModel) -> dict:
    return {
        "id": model.id,
        "device_id": model.device_id,
        "timestamp": model.timestamp.isoformat(),
        "rejection_rate": model.rejection_rate,
        "recovery_ratio": model.recovery_ratio,
        "permeate_quality": model.permeate_quality,
        "feed_quality": model.feed_quality,
        "efficiency": model.efficiency,
        "permeate_flow": model.permeate_flow,
        "reject_flow": model.reject_flow,
    }


@router.get("/{device_id}/current")
async def get_current_purification_performance(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(
        select(PPModel)
        .where(PPModel.device_id == device_id)
        .order_by(desc(PPModel.timestamp))
        .limit(1)
    )
    perf = result.scalar_one_or_none()
    
    if not perf:
        raise HTTPException(status_code=404, detail="No purification performance data for device")
    
    data = _model_to_dict(perf)
    data["data_freshness_seconds"] = int(
        (datetime.utcnow() - perf.timestamp).total_seconds()
    )
    return data


@router.get("/{device_id}/history")
async def get_purification_history(
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
    
    query = select(PPModel).where(
        and_(
            PPModel.device_id == device_id,
            PPModel.timestamp >= start,
            PPModel.timestamp <= end,
        )
    ).order_by(PPModel.timestamp)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    if len(records) > limit:
        step = len(records) / limit
        records = [records[int(i * len(records) / limit)] for i in range(limit)]
    
    series = {}
    for record in records:
        ts = record.timestamp.isoformat()
        for param, value in [
            ("rejection_rate", record.rejection_rate),
            ("recovery_ratio", record.recovery_ratio),
            ("permeate_quality", record.permeate_quality),
            ("feed_quality", record.feed_quality),
            ("efficiency", record.efficiency),
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