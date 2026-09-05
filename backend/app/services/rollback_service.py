import datetime
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import ChangeRequest, RollbackAction
from app.services.audit_service import record_audit


def get_all_rollbacks(db: Session) -> List[RollbackAction]:
    return db.query(RollbackAction).order_by(RollbackAction.timestamp.desc()).all()


def execute_rollback(
    db: Session,
    change_id: str,
    initiated_by: str = "Release Manager",
    reason: str = "Operational regression detected in downstream dispatch"
) -> RollbackAction:
    """
    Executes a formal rollback of a deployed business rule.
    Restores the previous business rule version, updates status, and writes complete audit trail.
    """
    cr = db.query(ChangeRequest).filter(ChangeRequest.change_id == change_id).first()
    if not cr:
        raise ValueError(f"Change request {change_id} not found")
    
    if cr.status != "DEPLOYED":
        raise ValueError(f"Cannot rollback change with status '{cr.status}'. Only DEPLOYED changes can be rolled back.")

    rollback_id = f"RB-{uuid.uuid4().hex[:6].upper()}"

    # 1. Audit Rollback Started
    record_audit(
        db=db,
        action="ROLLBACK_STARTED",
        entity_type="CHANGE_REQUEST",
        entity_id=cr.change_id,
        actor=initiated_by,
        old_value=cr.proposed_rule_version,
        new_value=cr.current_rule_version,
        status="WARNING"
    )

    # 2. Update Change Request
    cr.status = "ROLLED_BACK"
    cr.rolled_back_at = datetime.datetime.utcnow()
    cr.notes = f"{cr.notes or ''} [Rolled back to {cr.current_rule_version} by {initiated_by}: {reason}]"

    # 3. Create Rollback Action Record
    rb_action = RollbackAction(
        rollback_id=rollback_id,
        change_id=cr.change_id,
        from_version=cr.proposed_rule_version,
        to_version=cr.current_rule_version,
        initiated_by=initiated_by,
        reason=reason,
        status="COMPLETED",
        timestamp=datetime.datetime.utcnow()
    )
    db.add(rb_action)
    db.commit()
    db.refresh(rb_action)

    # 4. Audit Rollback Completed
    record_audit(
        db=db,
        action="ROLLBACK_COMPLETED",
        entity_type="ROLLBACK_ACTION",
        entity_id=rb_action.rollback_id,
        actor=initiated_by,
        old_value=f"Threshold {cr.new_threshold}",
        new_value=f"Restored Threshold {cr.previous_threshold} ({cr.current_rule_version})",
        status="SUCCESS"
    )

    return rb_action
