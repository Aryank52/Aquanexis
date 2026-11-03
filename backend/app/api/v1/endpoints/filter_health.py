"""
Filter Health API endpoints - Enhanced for Phase E.
"""

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import get_db
from app.infrastructure.logging import get_logger
from app.infrastructure.security import get_device_claims
from app.models.filter_health import FilterHealth as FilterHealthModel
from app.schemas.telemetry import (
    CounterfactualAnalysisResponse,
    ExplanationPayload,
    FilterHealthResponse,
    MaintenanceBandResponse,
    ModelMetadata,
    RULStabilityResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/filter-health", tags=["filter-health"])


def _model_to_response(model: FilterHealthModel) -> FilterHealthResponse:
    explanation = None
    if model.explanation:
        explanation = ExplanationPayload(
            top_factors=model.explanation.get("top_factors", []),
            method=model.explanation.get("method", "deterministic"),
        )

    counterfactual = None
    if model.counterfactual:
        counterfactual = CounterfactualAnalysisResponse(
            previous_rul_days=model.counterfactual.get("previous_rul_days"),
            current_rul_days=model.counterfactual.get("current_rul_days"),
            rul_change_days=model.counterfactual.get("rul_change_days"),
            rul_change_pct=model.counterfactual.get("rul_change_pct"),
            contributing_changes=model.counterfactual.get("contributing_changes", []),
            narrative=model.counterfactual.get("narrative", ""),
        )

    maintenance_band = None
    if model.maintenance_band:
        maintenance_band = MaintenanceBandResponse(
            band=model.maintenance_band,
            description=_get_maintenance_band_description(model.maintenance_band),
            threshold_score=0,  # Would be computed
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
        explanation=model.explanation,
        data_freshness_seconds=0,
        counterfactual=counterfactual,
        maintenance_band=maintenance_band,
        rul_stability=None,  # Would be computed separately
    )


def _get_maintenance_band_description(band: str) -> str:
    descriptions = {
        "normal": "Filter operating normally. No action required.",
        "monitor": "Filter health declining. Increase monitoring frequency.",
        "plan_maintenance": "Filter approaching end of life. Plan replacement soon.",
        "replace_recommended": "Filter at end of life. Replacement recommended immediately.",
    }
    return descriptions.get(band, "Unknown maintenance state")


@router.get("/{device_id}", response_model=FilterHealthResponse)
async def get_filter_health(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
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
    response.data_freshness_seconds = int((datetime.utcnow() - health.timestamp).total_seconds())
    return response


@router.get("/{device_id}/history")
async def get_filter_health_history(
    device_id: UUID,
    start: datetime = Query(...),
    end: datetime = Query(...),
    interval: str = Query("1h"),
    limit: int = Query(1000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if start >= end:
        raise HTTPException(status_code=400, detail="Start must be before end")

    if (end - start).total_seconds() > 30 * 24 * 3600:
        raise HTTPException(status_code=400, detail="Maximum range is 30 days")

    query = (
        select(FilterHealthModel)
        .where(
            and_(
                FilterHealthModel.device_id == device_id,
                FilterHealthModel.timestamp >= start,
                FilterHealthModel.timestamp <= end,
            )
        )
        .order_by(FilterHealthModel.timestamp)
    )

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


@router.get("/{device_id}/rul", response_model=None)
async def get_rul_prediction(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
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
        "confidence_level": getattr(health, "confidence_level", "unknown"),
        "is_stable": getattr(health, "is_stable", True),
        "previous_rul_days": getattr(health, "previous_rul_days", None),
        "rul_change_days": getattr(health, "rul_change_days", None),
        "data_freshness_seconds": int((datetime.utcnow() - health.timestamp).total_seconds()),
    }


@router.get("/{device_id}/counterfactual", response_model=CounterfactualAnalysisResponse)
async def get_counterfactual_analysis(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(FilterHealthModel)
        .where(FilterHealthModel.device_id == device_id)
        .order_by(desc(FilterHealthModel.timestamp))
        .limit(2)
    )
    records = result.scalars().all()

    if len(records) < 2:
        raise HTTPException(
            status_code=404, detail="Insufficient history for counterfactual analysis"
        )

    current = records[0]
    previous = records[1]

    return CounterfactualAnalysisResponse(
        device_id=device_id,
        timestamp=datetime.utcnow(),
        previous_rul_days=previous.rul_days,
        current_rul_days=current.rul_days,
        rul_change_days=(current.rul_days - previous.rul_days)
        if current.rul_days and previous.rul_days
        else None,
        rul_change_pct=((current.rul_days - previous.rul_days) / previous.rul_days * 100)
        if current.rul_days and previous.rul_days
        else None,
        contributing_changes=[],
        narrative="RUL changed based on updated sensor readings and filter health assessment.",
    )


@router.get("/{device_id}/rul-stability", response_model=RULStabilityResponse)
async def get_rul_stability(
    device_id: UUID,
    window_hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get RUL history
    result = await db.execute(
        select(FilterHealthModel)
        .where(
            and_(
                FilterHealthModel.device_id == device_id,
                FilterHealthModel.timestamp >= datetime.utcnow() - timedelta(hours=window_hours),
            )
        )
        .order_by(FilterHealthModel.timestamp)
    )
    records = result.scalars().all()

    rul_values = [r.rul_days for r in records if r.rul_days is not None]

    max_change = 0.0
    for i in range(1, len(rul_values)):
        if rul_values[i - 1] > 0:
            change = abs(rul_values[i] - rul_values[i - 1]) / rul_values[i - 1] * 100
            max_change = max(max_change, change)

    is_stable = max_change <= 30  # 30% threshold

    return RULStabilityResponse(
        device_id=device_id,
        window_hours=window_hours,
        readings_count=len(rul_values),
        rul_values=rul_values,
        max_change_pct=round(max_change, 1),
        is_stable=is_stable,
        instability_reason=None
        if max_change <= 30
        else f"RUL changed by {max_change:.1f}% in window (threshold: 30%)",
    )


@router.get("/{device_id}/maintenance-band", response_model=MaintenanceBandResponse)
async def get_maintenance_band(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
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

    band = getattr(health, "maintenance_band", "normal")

    return MaintenanceBandResponse(
        band=band,
        description=_get_maintenance_band_description(band),
        threshold_score=health.fhi if hasattr(health, "fhi") else 0,
    )


@router.get("/{device_id}/risk")
async def get_failure_risk(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
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
        "maintenance_band": getattr(health, "maintenance_band", "normal"),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/{device_id}/baseline")
async def get_baseline(
    device_id: UUID,
    db: AsyncSession = Depends(get_db),
    device_claims=Depends(get_device_claims),
):
    if device_claims and device_claims.device_id != device_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    from app.services.baseline_service import BaselineService

    baseline_service = BaselineService()
    status = await baseline_service.get_baseline_status(device_id)

    if not status.is_established:
        return {
            "device_id": str(device_id),
            "status": status.status,
            "needed_samples": status.needed_samples,
            "message": f"Baseline not yet established. Need {status.needed_samples} more samples.",
        }

    return await BaselineService().get_baseline_metrics(device_id)


def _get_maintenance_band_description(band: str) -> str:
    descriptions = {
        "normal": "Filter operating normally. No action required.",
        "monitor": "Filter health declining. Increase monitoring frequency.",
        "plan_maintenance": "Filter approaching end of life. Plan replacement soon.",
        "replace_recommended": "Filter at end of life. Replacement recommended immediately.",
    }
    return descriptions.get(band, "Unknown maintenance state")
