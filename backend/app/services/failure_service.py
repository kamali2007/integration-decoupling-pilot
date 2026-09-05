import datetime
import uuid
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import FailureCase, SystemStatus, AdapterDelivery
from app.services.audit_service import record_audit

FAILURE_CATALOG = [
    {
        "type": "MISSING_DATA",
        "affected_system": "ERP System",
        "severity": "HIGH",
        "cause": "ERP order payload missing required product_id or quantity fields.",
        "impact": "Order rejected by canonical validation layer; prevent dirty data propagation.",
        "detection_method": "Pydantic Schema Pre-validation in canonical event service.",
        "recovery_action": "Reject transaction with 422 Unprocessable Entity and request ERP source correction."
    },
    {
        "type": "DELAYED_DATA",
        "affected_system": "Forecast Planning System",
        "severity": "MEDIUM",
        "cause": "Forecast planning batch job delayed due to overnight ETL load spike.",
        "impact": "Forecast events delayed; Order pipeline continues operating in unblocked mode.",
        "detection_method": "Heartbeat & SLA monitor exceeding 120s timeout threshold.",
        "recovery_action": "Graceful non-blocking queuing; process backlog once stream resumes."
    },
    {
        "type": "SCHEMA_VIOLATION",
        "affected_system": "Supplier B (Beta Manufacturing)",
        "severity": "HIGH",
        "cause": "Supplier B adapter rejected payload due to legacy string formatted quantity.",
        "impact": "Order transmission blocked for Beta Manufacturing; Alpha and Gamma unaffected.",
        "detection_method": "Adapter validate() check returning explicit validation error.",
        "recovery_action": "Sanitize numeric typing in adapter transform layer and trigger retry."
    },
    {
        "type": "ENDPOINT_UNAVAILABLE",
        "affected_system": "Supplier C (Gamma Parts)",
        "severity": "CRITICAL",
        "cause": "Gamma Parts gateway returned HTTP 503 Service Unavailable / Connection Refused.",
        "impact": "Event delivery marked FAILED; held in dead-letter queue awaiting recovery.",
        "detection_method": "HTTP connection timeout / socket error during adapter send().",
        "recovery_action": "Exponential backoff retry policy; operator-triggered replay via UI."
    },
    {
        "type": "DUPLICATE_EVENT",
        "affected_system": "Canonical Ingestion Gateway",
        "severity": "LOW",
        "cause": "ERP network retry sent identical order message twice with same order_id.",
        "impact": "Potential duplicate fabrication order prevented by idempotency lock.",
        "detection_method": "SQLite unique constraint check on idempotency_key.",
        "recovery_action": "Flag as DUPLICATE_IGNORED, retain first processed record, log warning audit."
    }
]


def initialize_default_failures(db: Session):
    """Populates baseline failure modes if not present."""
    count = db.query(FailureCase).count()
    if count == 0:
        for idx, item in enumerate(FAILURE_CATALOG, 1):
            fc = FailureCase(
                failure_id=f"FAIL-00{idx}",
                failure_type=item["type"],
                affected_system=item["affected_system"],
                severity=item["severity"],
                cause=item["cause"],
                impact=item["impact"],
                detection_method=item["detection_method"],
                recovery_action=item["recovery_action"],
                status="OPEN" if idx in (3, 4) else "RESOLVED",
                retry_count=1 if idx in (3, 4) else 0,
                audit_reference=f"AUD-INIT-{idx}",
                created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=idx * 2)
            )
            db.add(fc)
        db.commit()


def simulate_failure(db: Session, failure_type: str, target_system: Optional[str] = None) -> FailureCase:
    """Dynamically simulates a failure case and records an audit trail entry."""
    spec = next((f for f in FAILURE_CATALOG if f["type"] == failure_type), None)
    if not spec:
        spec = {
            "type": failure_type,
            "affected_system": target_system or "ERP",
            "severity": "MEDIUM",
            "cause": f"Dynamic simulation of {failure_type}",
            "impact": "Downstream flow degraded",
            "detection_method": "Simulated exception monitor",
            "recovery_action": "Trigger automated retry"
        }

    failure_id = f"FAIL-{uuid.uuid4().hex[:6].upper()}"
    fc = FailureCase(
        failure_id=failure_id,
        failure_type=failure_type,
        affected_system=target_system or spec["affected_system"],
        severity=spec["severity"],
        cause=spec["cause"],
        impact=spec["impact"],
        detection_method=spec["detection_method"],
        recovery_action=spec["recovery_action"],
        status="OPEN",
        retry_count=0,
        audit_reference=f"AUD-{uuid.uuid4().hex[:6].upper()}",
        created_at=datetime.datetime.utcnow()
    )
    db.add(fc)
    db.commit()
    db.refresh(fc)

    record_audit(
        db=db,
        action="FAILURE_DETECTED",
        entity_type="FAILURE_CASE",
        entity_id=fc.failure_id,
        new_value=f"Detected {failure_type} on {fc.affected_system}",
        status="FAILED",
        correlation_id=fc.failure_id
    )

    return fc


def resolve_failure(db: Session, failure_id: str) -> FailureCase:
    """Marks a failure case as resolved with audit trail."""
    fc = db.query(FailureCase).filter(FailureCase.failure_id == failure_id).first()
    if not fc:
        raise ValueError(f"Failure case {failure_id} not found")

    fc.status = "RESOLVED"
    fc.resolved_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(fc)

    record_audit(
        db=db,
        action="FAILURE_RESOLVED",
        entity_type="FAILURE_CASE",
        entity_id=fc.failure_id,
        old_value="OPEN",
        new_value="RESOLVED",
        status="SUCCESS"
    )
    return fc


def retry_failure(db: Session, failure_id: str) -> FailureCase:
    """Attempts recovery of an open failure case."""
    fc = db.query(FailureCase).filter(FailureCase.failure_id == failure_id).first()
    if not fc:
        raise ValueError(f"Failure case {failure_id} not found")

    fc.retry_count += 1
    fc.status = "RESOLVED"
    fc.resolved_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(fc)

    record_audit(
        db=db,
        action="EVENT_RETRIED",
        entity_type="FAILURE_CASE",
        entity_id=fc.failure_id,
        new_value=f"Retry attempt {fc.retry_count} recovered failure condition",
        status="SUCCESS"
    )
    return fc
