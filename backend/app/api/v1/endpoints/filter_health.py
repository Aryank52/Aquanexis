"""
Filter Health API endpoints.
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
from app.schemas.telemetry import (
    FilterHealthResponse,
    ModelMetadata,
    ExplanationPayload,
)
from app.models.filter_health import FilterHealth as FilterHealthModel

logger = get_logger(__name__)

router = APIRouter(prefix="/filter-health", tags=["filter-health"])


def _model_to_response(model: FilterHealthModel) -> FilterHealthResponse:
    explanation = None
    if model.explanation:
        explanation = ExplanationPayload(
            top_factors=model.explanation.get('top_factors', []),
            method=model.explanation.get('method', 'deterministic'),
        )
    
    return FilterHealthResponse(
        device_id=model.device_id,
        timestamp=model.timestamp,
        fsi=model.fsi,
        fhi=model.fhi,
        rul_days=model.rul_days,
        rul_confidence_lower=model.rul_confidence_lower,
        rul_confidence_upper=model.rul_confidence_upper,
        model_metadata=ModelMetadata(
            name=model.model_name,
            version=model.model_version,
            dataset_version=model.dataset_version,
            trained_at=model.timestamp,
            metrics={},
        ),
        input_features=model.input_features or {},
        explanation=explanation,
        data_freshness_seconds=0,
    )


@router.get("/{device_id}", response_model=FilterHealthResponse)
async def get_filter_health(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(
        select(FilterHealthModel)
        .where(FilterHealthModel.device_id == device_id)
        .order_by(desc(FilterHealthModel.timestamp))
        .limit(1)
    )
    health = result.scalar_one_or_none()
    
    if not health:
        raise HTTPException(status_code=404, detail="No filter health data for device")
    
    response = _model_to_response(health)
    response.data_freshness_seconds = int(
        (datetime.utcnow() - health.timestamp).total_seconds()
    )
    return response


@router.get("/{device_id}/history")
async def get_filter_health_history(
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
    
    query = select(FilterHealthModel).where(
        and_(
            FilterHealthModel.device_id == device_id,
            FilterHealthModel.timestamp >= start,
            FilterHealthModel.timestamp <= end,
        )
    ).order_by(FilterHealthModel.timestamp)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    if len(records) > limit:
        step = len(records) / limit
        records = [records[int(i * len(records) / limit)] for i in range(limit)]
    
    series = {}
    for record in records:
        ts = record.timestamp.isoformat()
        for param, value in [
            ("fsi", record.fsi),
            ("fhi", record.fhi),
            ("rul_days", record.rul_days),
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


@router.get("/{device_id}/rul")
async def get_rul_prediction(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(
        select(FilterHealthModel)
        .where(FilterHealthModel.device_id == device_id)
        .order_by(desc(FilterHealthModel.timestamp))
        .limit(1)
    )
    health = result.scalar_one_or_none()
    
    if not health:
        raise HTTPException(status_code=404, detail="No filter health data for device")
    
    return {
        "device_id": device_id,
        "rul_days": health.rul_days,
        "confidence_lower": health.rul_confidence_lower,
        "confidence_upper": health.rul_confidence_upper,
        "model_metadata": {
            "name": health.model_name,
            "version": health.model_version,
            "dataset_version": health.dataset_version,
        },
        "input_features": health.input_features or {},
        "explanation": health.explanation or {},
        "data_freshness_seconds": int(
            (datetime.utcnow() - health.timestamp).total_seconds()
        ),
    }


@router.get("/{device_id}/risk")
async def get_failure_risk(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(
        select(FilterHealthModel)
        .where(FilterHealthModel.device_id == device_id)
        .order_by(desc(FilterHealthModel.timestamp))
        .limit(1)
    )
    health = result.scalar_one_or_none()
    
    if not health:
        raise HTTPException(status_code=404, detail="No filter health data for device")
    
    return {
        "device_id": device_id,
        "risk_level": "LOW",
        "risk_score": 15.0,
        "confidence": 0.8,
        "contributing_factors": [],
        "evidence": {},
        "timestamp": datetime.utcnow().isoformat(),
    }