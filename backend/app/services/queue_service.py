import datetime
import uuid
import json
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models import (
    MessageQueueItem,
    Order,
    Forecast,
    CanonicalEvent,
    SystemStatus,
    FailureCase
)
from app.services.audit_service import record_audit
from app.services.canonical_event_service import (
    create_order_canonical_event,
    create_forecast_canonical_event
)
from app.services.adapter_service import dispatch_event_to_adapter


def enqueue_message(
    db: Session,
    topic: str,
    payload: Dict[str, Any],
    idempotency_key: Optional[str] = None,
    source_system: str = "ERP",
    correlation_id: Optional[str] = None,
    max_retries: int = 3
) -> Tuple[MessageQueueItem, bool]:
    """
    Enqueues a message into the asynchronous message queue / buffer.
    Protects against duplicate messages using idempotency_key.
    Returns (item, is_new).
    """
    corr_id = correlation_id or f"CORR-Q-{uuid.uuid4().hex[:8].upper()}"

    # -------------------------------------------------------------
    # Error Boundary / Idempotency Check:
    # Verifies whether a message with this idempotency key was previously
    # accepted. If found, suppresses duplicate processing, preserves the
    # existing queue item, and records a WARNING audit trail entry.
    # -------------------------------------------------------------
    if idempotency_key:
        existing = db.query(MessageQueueItem).filter(
            MessageQueueItem.idempotency_key == idempotency_key
        ).first()
        if existing:
            record_audit(
                db=db,
                action="DUPLICATE_DETECTED",
                entity_type="MESSAGE_QUEUE",
                entity_id=existing.queue_id,
                old_value=existing.status,
                new_value="DUPLICATE_IGNORED",
                status="WARNING",
                correlation_id=existing.correlation_id
            )
            return existing, False

    # Allocate new unique queue message identifier
    queue_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
    item = MessageQueueItem(
        queue_id=queue_id,
        topic=topic,
        payload=payload,
        idempotency_key=idempotency_key,
        status="QUEUED",
        retry_count=0,
        max_retries=max_retries,
        error_message=None,
        source_system=source_system,
        correlation_id=corr_id,
        created_at=datetime.datetime.utcnow()
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    record_audit(
        db=db,
        action="MESSAGE_QUEUED",
        entity_type="MESSAGE_QUEUE",
        entity_id=item.queue_id,
        new_value=f"Enqueued to topic '{topic}' from {source_system}",
        status="SUCCESS",
        correlation_id=corr_id
    )

    return item, True


def process_message(
    db: Session,
    queue_id: str,
    simulate_failure: bool = False
) -> Tuple[bool, str, MessageQueueItem, Optional[str]]:
    """
    Processes a queued message through the canonical decoupling pipeline.
    Handles temporary failures with automatic retry scheduling and failure tracking.
    Returns (success, message_detail, queue_item, canonical_event_id).
    """
    item = db.query(MessageQueueItem).filter(MessageQueueItem.queue_id == queue_id).first()
    if not item:
        raise ValueError(f"Message queue item {queue_id} not found")

    if item.status == "PROCESSED":
        return True, "Message already processed", item, None

    item.status = "PROCESSING"
    db.commit()

    canonical_event_id = None

    try:
        # Check source/target system health status
        target_supplier = item.payload.get("supplier_id")
        if target_supplier:
            sys_status = db.query(SystemStatus).filter(SystemStatus.system_name == target_supplier).first()
            if sys_status and sys_status.status == "OFFLINE":
                simulate_failure = True

        if simulate_failure:
            raise ConnectionError(f"Temporary network error transmitting to {target_supplier or item.source_system}")

        # Route processing based on topic
        if item.topic in ("orders.incoming", "orders", "orders.buffered"):
            payload = item.payload
            order_id = payload.get("order_id") or f"ORD-Q-{uuid.uuid4().hex[:6].upper()}"
            
            # Check or create Order
            order = db.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                order = Order(
                    order_id=order_id,
                    supplier_id=payload["supplier_id"],
                    product_id=payload["product_id"],
                    quantity=int(payload["quantity"]),
                    unit=payload.get("unit", "EA"),
                    is_urgent=bool(payload.get("is_urgent", False)),
                    delivery_date=payload["delivery_date"],
                    source_system=item.source_system or "ERP",
                    status="PROCESSED",
                    correlation_id=item.correlation_id,
                    created_at=datetime.datetime.utcnow()
                )
                db.add(order)
                db.commit()
                db.refresh(order)

            # Create Canonical Event
            canonical_event, is_new = create_order_canonical_event(
                db=db,
                order=order,
                idempotency_key=item.idempotency_key
            )
            canonical_event_id = canonical_event.event_id

            # Dispatch to supplier adapter
            if is_new or canonical_event.status == "PROCESSED":
                dispatch_event_to_adapter(db, canonical_event)

        elif item.topic in ("forecasts.incoming", "forecasts", "forecasts.buffered"):
            payload = item.payload
            forecast_id = payload.get("forecast_id") or f"FCST-Q-{uuid.uuid4().hex[:6].upper()}"
            
            forecast = db.query(Forecast).filter(Forecast.forecast_id == forecast_id).first()
            if not forecast:
                forecast = Forecast(
                    forecast_id=forecast_id,
                    supplier_id=payload["supplier_id"],
                    product_id=payload["product_id"],
                    forecast_quantity=int(payload["forecast_quantity"]),
                    forecast_period=payload["forecast_period"],
                    source_system=item.source_system or "FORECAST_SYSTEM",
                    confidence_level=float(payload.get("confidence_level", 0.90)),
                    status="PROCESSED",
                    correlation_id=item.correlation_id,
                    created_at=datetime.datetime.utcnow()
                )
                db.add(forecast)
                db.commit()
                db.refresh(forecast)

            canonical_event, is_new = create_forecast_canonical_event(
                db=db,
                forecast=forecast,
                idempotency_key=item.idempotency_key
            )
            canonical_event_id = canonical_event.event_id

        elif item.topic == "events.dispatch":
            event_id = item.payload.get("event_id")
            event = db.query(CanonicalEvent).filter(CanonicalEvent.event_id == event_id).first()
            if not event:
                raise ValueError(f"CanonicalEvent {event_id} not found for dispatch")
            dispatch_event_to_adapter(db, event)
            canonical_event_id = event.event_id

        # Mark processed
        item.status = "PROCESSED"
        item.processed_at = datetime.datetime.utcnow()
        item.error_message = None
        db.commit()
        db.refresh(item)

        record_audit(
            db=db,
            action="MESSAGE_PROCESSED",
            entity_type="MESSAGE_QUEUE",
            entity_id=item.queue_id,
            new_value=f"Successfully processed message {item.queue_id} on topic '{item.topic}'",
            status="SUCCESS",
            correlation_id=item.correlation_id
        )

        return True, "Message processed successfully", item, canonical_event_id

    except Exception as exc:
        # -------------------------------------------------------------
        # Error Boundary / Fault Interception:
        # Traps transient communication, downstream offline, or validation faults.
        # Implements a bounded state machine:
        # - When attempts < max_retries: transitions to RETRYING with audit warning.
        # - When attempts >= max_retries: transitions to FAILED (dead-letter).
        # -------------------------------------------------------------
        item.retry_count += 1
        item.error_message = str(exc)

        if item.retry_count < item.max_retries:
            item.status = "RETRYING"
            record_audit(
                db=db,
                action="MESSAGE_RETRY_SCHEDULED",
                entity_type="MESSAGE_QUEUE",
                entity_id=item.queue_id,
                new_value=f"Attempt {item.retry_count} failed: {str(exc)}. Scheduled for retry.",
                status="WARNING",
                correlation_id=item.correlation_id
            )
        else:
            item.status = "FAILED"
            record_audit(
                db=db,
                action="MESSAGE_FAILED",
                entity_type="MESSAGE_QUEUE",
                entity_id=item.queue_id,
                new_value=f"Max retries exhausted ({item.max_retries}): {str(exc)}",
                status="FAILED",
                correlation_id=item.correlation_id
            )

        # -------------------------------------------------------------
        # Failure Center Integration:
        # Escalates unhandled or retrying queue exceptions into the centralized
        # FailureCase repository so dashboard operators have immediate visibility.
        # -------------------------------------------------------------
        target_sys = item.payload.get("supplier_id") or item.source_system
        fail_case = FailureCase(
            failure_id=f"FAIL-Q-{uuid.uuid4().hex[:6].upper()}",
            failure_type="ENDPOINT_UNAVAILABLE" if "network" in str(exc).lower() else "SCHEMA_VIOLATION",
            affected_system=target_sys,
            severity="HIGH" if item.status == "FAILED" else "MEDIUM",
            cause=f"Queue message {item.queue_id} processing exception: {str(exc)}",
            impact=f"Message {item.queue_id} held in buffer (status: {item.status})",
            detection_method="Async Queue Worker exception interceptor",
            recovery_action="Automated backoff retry or operator queue retry replay",
            status="OPEN",
            retry_count=item.retry_count,
            audit_reference=item.queue_id,
            created_at=datetime.datetime.utcnow()
        )
        db.add(fail_case)

        db.commit()
        db.refresh(item)

        return False, str(exc), item, None


def retry_message(db: Session, queue_id: str) -> Tuple[bool, str, MessageQueueItem, Optional[str]]:
    """
    Retries processing a failed or retrying message.
    """
    item = db.query(MessageQueueItem).filter(MessageQueueItem.queue_id == queue_id).first()
    if not item:
        raise ValueError(f"Message {queue_id} not found")

    record_audit(
        db=db,
        action="MESSAGE_RETRY_INITIATED",
        entity_type="MESSAGE_QUEUE",
        entity_id=item.queue_id,
        new_value=f"Manual/automated retry triggered for {queue_id} (previous status: {item.status})",
        status="SUCCESS",
        correlation_id=item.correlation_id
    )

    success, detail, item, evt_id = process_message(db, queue_id, simulate_failure=False)

    if success:
        # -------------------------------------------------------------
        # Self-Healing Resolution Flow:
        # Once retry execution succeeds, any corresponding FailureCase
        # entries holding the failure condition are automatically transitioned
        # to RESOLVED, clearing the operator alert in Failure Center.
        # -------------------------------------------------------------
        open_failures = db.query(FailureCase).filter(
            FailureCase.audit_reference == queue_id,
            FailureCase.status == "OPEN"
        ).all()
        for fc in open_failures:
            fc.status = "RESOLVED"
            fc.resolved_at = datetime.datetime.utcnow()
        db.commit()

        record_audit(
            db=db,
            action="MESSAGE_RECOVERED",
            entity_type="MESSAGE_QUEUE",
            entity_id=item.queue_id,
            new_value=f"Message {queue_id} successfully recovered and processed",
            status="SUCCESS",
            correlation_id=item.correlation_id
        )

    return success, detail, item, evt_id


def process_all_queued(db: Session) -> Dict[str, Any]:
    """
    Drains all queued or retrying messages in FIFO order.
    Demonstrates asynchronous batch/delay buffer processing.
    """
    pending = db.query(MessageQueueItem).filter(
        MessageQueueItem.status.in_(["QUEUED", "RETRYING"])
    ).order_by(MessageQueueItem.created_at.asc()).all()

    processed_count = 0
    failed_count = 0
    results = []

    for item in pending:
        success, detail, updated_item, evt_id = process_message(db, item.queue_id, simulate_failure=False)
        if success:
            processed_count += 1
        else:
            failed_count += 1
        results.append({
            "queue_id": item.queue_id,
            "topic": item.topic,
            "success": success,
            "status": updated_item.status,
            "detail": detail,
            "canonical_event_id": evt_id
        })

    return {
        "total_attempted": len(pending),
        "processed_count": processed_count,
        "failed_count": failed_count,
        "results": results
    }


def get_queue_stats(db: Session) -> Dict[str, int]:
    """Returns queue statistics breakdown."""
    items = db.query(MessageQueueItem).all()
    stats = {
        "total": len(items),
        "queued": sum(1 for i in items if i.status == "QUEUED"),
        "processing": sum(1 for i in items if i.status == "PROCESSING"),
        "processed": sum(1 for i in items if i.status == "PROCESSED"),
        "retrying": sum(1 for i in items if i.status == "RETRYING"),
        "failed": sum(1 for i in items if i.status == "FAILED"),
        "dead_letter": sum(1 for i in items if i.status == "DEAD_LETTER")
    }
    return stats
