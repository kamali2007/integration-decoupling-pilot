import datetime
import uuid
from typing import Optional
from sqlalchemy.orm import Session
from app.models import AuditEntry


def record_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    actor: str = "SYSTEM",
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    status: str = "SUCCESS",
    correlation_id: Optional[str] = None,
    commit: bool = True
) -> AuditEntry:
    """Creates an immutable audit log entry."""
    audit_id = f"AUD-{uuid.uuid4().hex[:8].upper()}"
    entry = AuditEntry(
        audit_id=audit_id,
        timestamp=datetime.datetime.utcnow(),
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        status=status,
        correlation_id=correlation_id or str(uuid.uuid4())
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    return entry
