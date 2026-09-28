import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Forecast, SystemStatus
from app.schemas import ForecastCreate, ForecastResponse
from app.services.canonical_event_service import create_forecast_canonical_event
from app.services.audit_service import record_audit

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.get("", response_model=List[ForecastResponse])
def list_forecasts(
    supplier_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Forecast)
    if supplier_id:
        query = query.filter(Forecast.supplier_id == supplier_id)
    return query.order_by(Forecast.created_at.desc()).limit(limit).all()


@router.post("", response_model=ForecastResponse, status_code=201)
def create_forecast(
    payload: ForecastCreate,
    db: Session = Depends(get_db)
):
    """
    Creates a Forecast from Forecast Planning System.
    1. Validates payload
    2. Handles forecast system delay scenario without blocking
    3. Persists Forecast
    4. Generates Canonical Forecast Event
    5. Records Audit Entry
    """
    fcst_sys = db.query(SystemStatus).filter(SystemStatus.system_name == "FORECAST").first()
    is_delayed = fcst_sys and fcst_sys.status in ("DELAYED", "DEGRADED")

    forecast_id = payload.forecast_id or f"FCST-{uuid.uuid4().hex[:6].upper()}"
    correlation_id = f"CORR-{uuid.uuid4().hex[:8].upper()}"

    existing = db.query(Forecast).filter(Forecast.forecast_id == forecast_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Forecast {forecast_id} already exists")

    forecast = Forecast(
        forecast_id=forecast_id,
        supplier_id=payload.supplier_id,
        product_id=payload.product_id,
        forecast_quantity=payload.forecast_quantity,
        forecast_period=payload.forecast_period,
        source_system=payload.source_system,
        confidence_level=payload.confidence_level,
        status="DELAYED" if is_delayed else "PROCESSED",
        correlation_id=correlation_id,
        created_at=datetime.datetime.utcnow()
    )
    db.add(forecast)
    db.commit()
    db.refresh(forecast)

    record_audit(
        db=db,
        action="FORECAST_CREATED",
        entity_type="FORECAST",
        entity_id=forecast.forecast_id,
        new_value=f"Forecast {forecast.forecast_id} created: {forecast.forecast_quantity} units for {forecast.forecast_period}",
        status="SUCCESS",
        correlation_id=correlation_id
    )

    if not is_delayed:
        create_forecast_canonical_event(db, forecast)
    else:
        # Asynchronously buffer delayed forecast into message queue for resilience
        from app.services.queue_service import enqueue_message
        enqueue_message(
            db=db,
            topic="forecasts.buffered",
            payload={
                "forecast_id": forecast.forecast_id,
                "supplier_id": forecast.supplier_id,
                "product_id": forecast.product_id,
                "forecast_quantity": forecast.forecast_quantity,
                "forecast_period": forecast.forecast_period,
                "confidence_level": forecast.confidence_level
            },
            idempotency_key=f"BUFFER-FCST-{forecast.forecast_id}",
            source_system=forecast.source_system or "FORECAST_SYSTEM",
            correlation_id=correlation_id
        )

    return forecast
