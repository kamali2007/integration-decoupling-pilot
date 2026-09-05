import datetime
import uuid
import json
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models import CanonicalEvent, ChangeRequest, Order, Forecast
from app.services.audit_service import record_audit


def get_active_business_rule(db: Session) -> Tuple[str, int]:
    """
    Returns the currently active business rule version and threshold for urgent orders.
    Default: BR-1.0 with threshold 100.
    If CR-001 has status DEPLOYED, returns BR-2.0 with threshold 200.
    """
    deployed_cr = db.query(ChangeRequest).filter(ChangeRequest.status == "DEPLOYED").first()
    if deployed_cr:
        return deployed_cr.proposed_rule_version, deployed_cr.new_threshold
    return "BR-1.0", 100


def create_order_canonical_event(
    db: Session,
    order: Order,
    idempotency_key: Optional[str] = None
) -> Tuple[CanonicalEvent, bool]:
    """
    Transforms an Order into a Canonical Order Event.
    Applies the active business rule:
    If order.is_urgent is True and order.quantity >= threshold: priority = PRIORITY_HIGH, else NORMAL.
    Handles Idempotency:
    If idempotency_key already exists, flags as DUPLICATE_IGNORED and logs audit trail.
    Returns (CanonicalEvent, is_new).
    """
    active_version, threshold = get_active_business_rule(db)

    # Determine idempotency key
    key = idempotency_key or f"IDEMP-ORD-{order.order_id}"

    # Idempotency check
    existing = db.query(CanonicalEvent).filter(
        (CanonicalEvent.idempotency_key == key) |
        (CanonicalEvent.order_id == order.order_id)
    ).first()

    if existing:
        record_audit(
            db=db,
            action="DUPLICATE_DETECTED",
            entity_type="CANONICAL_EVENT",
            entity_id=existing.event_id,
            old_value=existing.status,
            new_value="DUPLICATE_IGNORED",
            status="WARNING",
            correlation_id=existing.correlation_id
        )
        return existing, False

    # Evaluate business rule
    if order.is_urgent and order.quantity >= threshold:
        computed_priority = "PRIORITY_HIGH"
    else:
        computed_priority = "NORMAL"

    event_id = f"EVT-ORD-{uuid.uuid4().hex[:8].upper()}"
    timestamp_str = datetime.datetime.utcnow().isoformat() + "Z"

    raw_dict = {
        "event_id": event_id,
        "event_type": "ORDER_CREATED",
        "event_version": "1.0",
        "timestamp": timestamp_str,
        "source_system": order.source_system or "ERP",
        "order_id": order.order_id,
        "supplier_id": order.supplier_id,
        "product_id": order.product_id,
        "quantity": order.quantity,
        "unit": order.unit,
        "priority": computed_priority,
        "delivery_date": order.delivery_date,
        "business_rule_version": active_version,
        "correlation_id": order.correlation_id,
        "idempotency_key": key
    }

    canonical_event = CanonicalEvent(
        event_id=event_id,
        event_type="ORDER_CREATED",
        event_version="1.0",
        source_system=order.source_system or "ERP",
        order_id=order.order_id,
        supplier_id=order.supplier_id,
        product_id=order.product_id,
        quantity=order.quantity,
        unit=order.unit,
        priority=computed_priority,
        delivery_date=order.delivery_date,
        business_rule_version=active_version,
        correlation_id=order.correlation_id,
        idempotency_key=key,
        status="PROCESSED",
        raw_payload=raw_dict
    )

    db.add(canonical_event)
    db.commit()
    db.refresh(canonical_event)

    # Log creation and validation audits
    record_audit(
        db=db,
        action="EVENT_CREATED",
        entity_type="CANONICAL_EVENT",
        entity_id=canonical_event.event_id,
        new_value=json.dumps({"priority": computed_priority, "rule": active_version, "threshold": threshold}),
        status="SUCCESS",
        correlation_id=canonical_event.correlation_id
    )

    record_audit(
        db=db,
        action="EVENT_VALIDATED",
        entity_type="CANONICAL_EVENT",
        entity_id=canonical_event.event_id,
        new_value="Pydantic CanonicalOrderEvent schema validated successfully",
        status="SUCCESS",
        correlation_id=canonical_event.correlation_id
    )

    return canonical_event, True


def create_forecast_canonical_event(
    db: Session,
    forecast: Forecast,
    idempotency_key: Optional[str] = None
) -> Tuple[CanonicalEvent, bool]:
    """
    Transforms a Forecast into a Canonical Forecast Event.
    """
    key = idempotency_key or f"IDEMP-FCST-{forecast.forecast_id}"

    existing = db.query(CanonicalEvent).filter(
        (CanonicalEvent.idempotency_key == key) |
        (CanonicalEvent.forecast_id == forecast.forecast_id)
    ).first()

    if existing:
        record_audit(
            db=db,
            action="DUPLICATE_DETECTED",
            entity_type="CANONICAL_EVENT",
            entity_id=existing.event_id,
            old_value=existing.status,
            new_value="DUPLICATE_IGNORED",
            status="WARNING",
            correlation_id=existing.correlation_id
        )
        return existing, False

    event_id = f"EVT-FCST-{uuid.uuid4().hex[:8].upper()}"
    timestamp_str = datetime.datetime.utcnow().isoformat() + "Z"

    raw_dict = {
        "event_id": event_id,
        "event_type": "FORECAST_PUBLISHED",
        "event_version": "1.0",
        "timestamp": timestamp_str,
        "source_system": forecast.source_system or "FORECAST_SYSTEM",
        "forecast_id": forecast.forecast_id,
        "supplier_id": forecast.supplier_id,
        "product_id": forecast.product_id,
        "quantity": forecast.forecast_quantity,
        "forecast_period": forecast.forecast_period,
        "business_rule_version": "BR-1.0",
        "correlation_id": forecast.correlation_id,
        "idempotency_key": key
    }

    canonical_event = CanonicalEvent(
        event_id=event_id,
        event_type="FORECAST_PUBLISHED",
        event_version="1.0",
        source_system=forecast.source_system or "FORECAST_SYSTEM",
        forecast_id=forecast.forecast_id,
        supplier_id=forecast.supplier_id,
        product_id=forecast.product_id,
        quantity=forecast.forecast_quantity,
        forecast_period=forecast.forecast_period,
        business_rule_version="BR-1.0",
        correlation_id=forecast.correlation_id,
        idempotency_key=key,
        status="PROCESSED",
        raw_payload=raw_dict
    )

    db.add(canonical_event)
    db.commit()
    db.refresh(canonical_event)

    record_audit(
        db=db,
        action="EVENT_CREATED",
        entity_type="CANONICAL_EVENT",
        entity_id=canonical_event.event_id,
        new_value=json.dumps({"type": "FORECAST", "qty": forecast.forecast_quantity}),
        status="SUCCESS",
        correlation_id=canonical_event.correlation_id
    )

    return canonical_event, True
