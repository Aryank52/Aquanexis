"""
Water Quality API endpoints.
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
    AquaScoreResponse,
    ParameterScore,
    TrendAnalysis,
    AnomalyFlag,
)
from app.models.water_quality import WaterQualityScore as WaterQualityScoreModel

logger = get_logger(__name__)

router = APIRouter(prefix="/water-quality", tags=["water-quality"])


def _model_to_response(model: WaterQualityScoreModel) -> AquaScoreResponse:
    """Convert WaterQualityScore model to response schema."""
    # Parse parameter scores
    param_scores = []
    if model.tds_score is not None:
        param_scores.append(ParameterScore(
            parameter="tds",
            value=None,
            score=model.tds_score,
            guideline_min=0,
            guideline_max=300,
            unit="ppm",
        ))
    if model.ph_score is not None:
        param_scores.append(ParameterScore(
            parameter="ph",
            value=None,
            score=model.ph_score,
            guideline_min=6.5,
            guideline_max=8.5,
            unit="",
        ))
    if model.turbidity_score is not None:
        param_scores.append(ParameterScore(
            parameter="turbidity",
            value=None,
            score=model.turbidity_score,
            guideline_min=0,
            guideline_max=1,
            unit="NTU",
        ))
    if model.temp_score is not None:
        param_scores.append(ParameterScore(
            parameter="temperature",
            value=None,
            score=model.temp_score,
            guideline_min=10,
            guideline_max=25,
            unit="°C",
        ))
    if model.conductivity_score is not None:
        param_scores.append(ParameterScore(
            parameter="conductivity",
            value=None,
            score=model.conductivity_score,
            guideline_min=0,
            guideline_max=500,
            unit="µS/cm",
        ))
    
    # Parse trends from JSON
    trends = []
    if model.trends:
        for param, trend_data in model.trends.items():
            if trend_data:
                trends.append(TrendAnalysis(
                    parameter=param,
                    window=trend_data.get('window', '24h'),
                    direction=trend_data.get('direction', 'stable'),
                    magnitude=trend_data.get('magnitude', 0),
                    points=[TrendPoint(**p) for p in trend_data.get('points', [])],
                    slope_per_hour=trend_data.get('slope_per_hour', 0),
                ))
    
    # Parse anomaly flags
    anomaly_flags = []
    if model.anomaly_flags:
        for flag in model.anomaly_flags:
            anomaly_flags.append(AnomalyFlag(
                parameter=flag.get('parameter', ''),
                score=flag.get('score', 0),
                threshold=flag.get('threshold', 0),
                type=flag.get('type', 'unknown'),
                message=flag.get('message', ''),
            ))
    
    return AquaScoreResponse(
        device_id=model.device_id,
        timestamp=model.timestamp,
        overall_score=model.overall_score,
        parameter_scores=param_scores,
        trends=trends,
        anomaly_score=model.anomaly_score or 0.0,
        anomaly_flags=anomaly_flags,
        data_freshness_seconds=0,  # Calculated at query time
    )


@router.get("/current/{device_id}", response_model=AquaScoreResponse)
async def get_current_water_quality(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get current water quality (AquaScore) for a device."""
    # Check authorization
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    result = await db.execute(
        select(WaterQualityScoreModel)
        .where(WaterQualityScoreModel.device_id == device_id)
        .order_by(desc(WaterQualityScoreModel.timestamp))
        .limit(1)
    )
    score = result.scalar_one_or_none()
    
    if not score:
        raise HTTPException(status_code=404, detail="No water quality data for device")
    
    response = _model_to_response(score)
    response.data_freshness_seconds = int(
        (datetime.utcnow() - score.timestamp).total_seconds()
    )
    return response


@router.get("/history/{device_id}")
async def get_water_quality_history(
    device_id: UUID,
    start: datetime = Query(...),
    end: datetime = Query(...),
    interval: str = Query("1h"),
    limit: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get historical water quality with optional downsampling."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if start >= end:
        raise HTTPException(status_code=400, detail="Start must be before end")
    
    if (end - start).total_seconds() > 30 * 24 * 3600:
        raise HTTPException(status_code=400, detail="Maximum range is 30 days")
    
    query = select(WaterQualityScoreModel).where(
        and_(
            WaterQualityScoreModel.device_id == device_id,
            WaterQualityScoreModel.timestamp >= start,
            WaterQualityScoreModel.timestamp <= end,
        )
    ).order_by(WaterQualityScoreModel.timestamp)
    
    result = await db.execute(query)
    scores = result.scalars().all()
    
    if len(scores) > limit:
        # Simple downsampling
        step = len(scores) / limit
        scores = [scores[int(i * step)] for i in range(limit)]
    
    # Build series for each parameter
    series = {}
    for score in scores:
        ts = score.timestamp.isoformat()
        for param, value in [
            ("overall_score", score.overall_score),
            ("tds_score", score.tds_score),
            ("ph_score", score.ph_score),
            ("turbidity_score", score.turbidity_score),
            ("temp_score", score.temp_score),
            ("conductivity_score", score.conductivity_score),
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


@router.get("/trends/{device_id}")
async def get_water_quality_trends(
    device_id: UUID,
    windows: List[str] = Query(["1h", "24h", "7d", "30d"]),
    parameters: List[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get trend analysis for water quality parameters."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # This would use the water quality service to compute trends
    # For now, return placeholder
    return {
        "device_id": device_id,
        "trends": [],
        "message": "Trend computation not yet implemented in API",
    }


@router.get("/anomalies/{device_id}")
async def get_water_quality_anomalies(
    device_id: UUID,
    window: str = Query("24h"),
    db: AsyncSession = Depends(get_db),
    device_claims = Depends(get_device_claims),
):
    """Get detected anomalies for water quality."""
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Return placeholder
    return {
        "device_id": device_id,
        "window": window,
        "anomalies": [],
        "message": "Anomaly detection not yet implemented in API",
    }