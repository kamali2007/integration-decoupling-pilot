import datetime
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import CanonicalEvent, AdapterDelivery, SystemStatus
from app.adapters.supplier_a import SupplierAAdapter
from app.adapters.supplier_b import SupplierBAdapter
from app.adapters.supplier_c import SupplierCAdapter
from app.services.audit_service import record_audit

ADAPTER_MAP = {
    "SUP-A": (SupplierAAdapter(), "Alpha Components Adapter"),
    "SUP-B": (SupplierBAdapter(), "Beta Manufacturing Adapter"),
    "SUP-C": (SupplierCAdapter(), "Gamma Parts Adapter")
}


def get_adapter_for_supplier(supplier_code: str):
    return ADAPTER_MAP.get(supplier_code)


def dispatch_event_to_adapter(
    db: Session,
    event: CanonicalEvent,
    simulate_delay: bool = False,
    simulate_failure: bool = False
) -> AdapterDelivery:
    """
    Routinely dispatches a canonical event through the appropriate supplier adapter.
    Executes validate -> transform -> send.
    Persists delivery status and creates audit log.
    """
    adapter_info = get_adapter_for_supplier(event.supplier_id)
    if not adapter_info:
        # Fallback to Supplier A if unspecified
        adapter_info = ADAPTER_MAP["SUP-A"]
    
    adapter_instance, adapter_name = adapter_info
    canonical_payload = event.raw_payload or {
        "event_id": event.event_id,
        "order_id": event.order_id,
        "forecast_id": event.forecast_id,
        "supplier_id": event.supplier_id,
        "product_id": event.product_id,
        "quantity": event.quantity,
        "priority": event.priority,
        "delivery_date": event.delivery_date,
        "correlation_id": event.correlation_id
    }

    # Check system status for supplier
    sys_status = db.query(SystemStatus).filter(SystemStatus.system_name == event.supplier_id).first()
    if sys_status and sys_status.status == "OFFLINE":
        simulate_failure = True
    elif sys_status and sys_status.status in ("DELAYED", "DEGRADED"):
        simulate_delay = True

    # 1. Validate
    is_valid, val_msg = adapter_instance.validate(canonical_payload)
    if not is_valid:
        delivery = AdapterDelivery(
            delivery_id=f"DELIV-{uuid.uuid4().hex[:8].upper()}",
            event_id=event.event_id,
            supplier_id=event.supplier_id,
            adapter_name=adapter_name,
            transformed_payload={"error": val_msg, "canonical": canonical_payload},
            delivery_status="FAILED",
            attempt_count=1,
            last_attempt=datetime.datetime.utcnow(),
            error_message=f"Validation failed: {val_msg}",
            latency_ms=10,
            retry_status="SCHEDULED"
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        record_audit(
            db=db,
            action="EVENT_FAILED",
            entity_type="ADAPTER_DELIVERY",
            entity_id=delivery.delivery_id,
            new_value=f"Validation error: {val_msg}",
            status="FAILED",
            correlation_id=event.correlation_id
        )
        return delivery

    # 2. Transform
    transformed = adapter_instance.transform(canonical_payload)
    record_audit(
        db=db,
        action="EVENT_TRANSFORMED",
        entity_type="CANONICAL_EVENT",
        entity_id=event.event_id,
        new_value=f"Transformed to {adapter_name} schema format",
        status="SUCCESS",
        correlation_id=event.correlation_id
    )

    # 3. Send
    try:
        send_result = adapter_instance.send(
            transformed,
            simulate_delay=simulate_delay,
            simulate_failure=simulate_failure
        )
        delivery = AdapterDelivery(
            delivery_id=f"DELIV-{uuid.uuid4().hex[:8].upper()}",
            event_id=event.event_id,
            supplier_id=event.supplier_id,
            adapter_name=adapter_name,
            transformed_payload=transformed,
            delivery_status="PROCESSED",
            attempt_count=1,
            last_attempt=datetime.datetime.utcnow(),
            error_message=None,
            latency_ms=send_result.get("latencyMs", send_result.get("LATENCY_MS", 40)),
            retry_status="NONE"
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        record_audit(
            db=db,
            action="EVENT_SENT",
            entity_type="ADAPTER_DELIVERY",
            entity_id=delivery.delivery_id,
            new_value=f"Successfully delivered to {adapter_name}",
            status="SUCCESS",
            correlation_id=event.correlation_id
        )
        return delivery

    except Exception as exc:
        delivery = AdapterDelivery(
            delivery_id=f"DELIV-{uuid.uuid4().hex[:8].upper()}",
            event_id=event.event_id,
            supplier_id=event.supplier_id,
            adapter_name=adapter_name,
            transformed_payload=transformed,
            delivery_status="FAILED",
            attempt_count=1,
            last_attempt=datetime.datetime.utcnow(),
            error_message=str(exc),
            latency_ms=120,
            retry_status="SCHEDULED"
        )
        db.add(delivery)
        db.commit()
        db.refresh(delivery)

        record_audit(
            db=db,
            action="EVENT_FAILED",
            entity_type="ADAPTER_DELIVERY",
            entity_id=delivery.delivery_id,
            new_value=str(exc),
            status="FAILED",
            correlation_id=event.correlation_id
        )
        return delivery


def retry_adapter_delivery(db: Session, delivery_id: str) -> AdapterDelivery:
    """
    Retries a failed adapter delivery.
    Increments attempt_count, executes send, and updates status upon success.
    """
    delivery = db.query(AdapterDelivery).filter(AdapterDelivery.delivery_id == delivery_id).first()
    if not delivery:
        raise ValueError(f"Delivery {delivery_id} not found")

    adapter_info = get_adapter_for_supplier(delivery.supplier_id)
    if not adapter_info:
        adapter_info = ADAPTER_MAP["SUP-A"]
    adapter_instance, _ = adapter_info

    delivery.attempt_count += 1
    delivery.last_attempt = datetime.datetime.utcnow()

    try:
        send_res = adapter_instance.send(delivery.transformed_payload, simulate_failure=False)
        delivery.delivery_status = "PROCESSED"
        delivery.error_message = None
        delivery.retry_status = "RECOVERED"
        delivery.latency_ms = send_res.get("latencyMs", 35)

        record_audit(
            db=db,
            action="EVENT_RETRIED",
            entity_type="ADAPTER_DELIVERY",
            entity_id=delivery.delivery_id,
            new_value=f"Retry attempt {delivery.attempt_count} succeeded",
            status="SUCCESS"
        )
    except Exception as exc:
        delivery.delivery_status = "FAILED"
        delivery.error_message = str(exc)
        delivery.retry_status = "EXHAUSTED" if delivery.attempt_count >= 3 else "SCHEDULED"

        record_audit(
            db=db,
            action="EVENT_FAILED",
            entity_type="ADAPTER_DELIVERY",
            entity_id=delivery.delivery_id,
            new_value=f"Retry attempt {delivery.attempt_count} failed: {str(exc)}",
            status="FAILED"
        )

    db.commit()
    db.refresh(delivery)
    return delivery
