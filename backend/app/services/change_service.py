import datetime
import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import ChangeRequest
from app.services.audit_service import record_audit


def get_all_changes(db: Session) -> List[ChangeRequest]:
    return db.query(ChangeRequest).order_by(ChangeRequest.created_at.desc()).all()


def get_change_by_id(db: Session, change_id: str) -> Optional[ChangeRequest]:
    return db.query(ChangeRequest).filter(ChangeRequest.change_id == change_id).first()


def create_change_request(
    db: Session,
    title: str,
    description: str,
    new_threshold: int = 200,
    submitted_by: str = "Supply Chain Architect",
    notes: Optional[str] = None
) -> ChangeRequest:
    change_id = f"CR-{uuid.uuid4().hex[:4].upper()}"
    cr = ChangeRequest(
        change_id=change_id,
        title=title,
        description=description,
        rule_key="URGENT_ORDER_THRESHOLD",
        current_rule_version="BR-1.0",
        proposed_rule_version="BR-2.0",
        previous_threshold=100,
        new_threshold=new_threshold,
        status="DRAFT",
        submitted_by=submitted_by,
        baseline_systems_changed=6,
        decoupled_systems_changed=1,
        notes=notes or "High-impact change affecting urgent order priority routing."
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)

    record_audit(
        db=db,
        action="CHANGE_CREATED",
        entity_type="CHANGE_REQUEST",
        entity_id=cr.change_id,
        actor=submitted_by,
        new_value=f"Draft created: threshold update to {new_threshold}",
        status="SUCCESS"
    )
    return cr


def submit_for_review(db: Session, change_id: str, actor: str = "Supply Chain Architect") -> ChangeRequest:
    cr = get_change_by_id(db, change_id)
    if not cr:
        raise ValueError(f"Change request {change_id} not found")
    if cr.status != "DRAFT":
        raise ValueError(f"Cannot submit change in '{cr.status}' state for review")

    old_status = cr.status
    cr.status = "UNDER_REVIEW"
    db.commit()
    db.refresh(cr)

    record_audit(
        db=db,
        action="CHANGE_SUBMITTED",
        entity_type="CHANGE_REQUEST",
        entity_id=cr.change_id,
        actor=actor,
        old_value=old_status,
        new_value="UNDER_REVIEW",
        status="SUCCESS"
    )
    return cr


def approve_change(db: Session, change_id: str, approver: str = "Lead Enterprise Architect") -> ChangeRequest:
    cr = get_change_by_id(db, change_id)
    if not cr:
        raise ValueError(f"Change request {change_id} not found")
    if cr.status not in ("UNDER_REVIEW", "DRAFT"):
        raise ValueError(f"Cannot approve change in '{cr.status}' state")

    old_status = cr.status
    cr.status = "APPROVED"
    cr.approved_by = approver
    db.commit()
    db.refresh(cr)

    record_audit(
        db=db,
        action="CHANGE_APPROVED",
        entity_type="CHANGE_REQUEST",
        entity_id=cr.change_id,
        actor=approver,
        old_value=old_status,
        new_value="APPROVED",
        status="SUCCESS"
    )
    return cr


def reject_change(db: Session, change_id: str, reviewer: str = "Lead Enterprise Architect", reason: str = "Impact unverified") -> ChangeRequest:
    cr = get_change_by_id(db, change_id)
    if not cr:
        raise ValueError(f"Change request {change_id} not found")

    old_status = cr.status
    cr.status = "REJECTED"
    cr.notes = f"{cr.notes or ''} [Rejection Reason: {reason}]"
    db.commit()
    db.refresh(cr)

    record_audit(
        db=db,
        action="CHANGE_REJECTED",
        entity_type="CHANGE_REQUEST",
        entity_id=cr.change_id,
        actor=reviewer,
        old_value=old_status,
        new_value="REJECTED",
        status="WARNING"
    )
    return cr


def deploy_change(db: Session, change_id: str, deployer: str = "DevOps Engineer") -> ChangeRequest:
    cr = get_change_by_id(db, change_id)
    if not cr:
        raise ValueError(f"Change request {change_id} not found")
    if cr.status != "APPROVED":
        raise ValueError(f"Cannot deploy unapproved change! Current status is '{cr.status}'. Approval is strictly required.")

    # Mark any previously deployed CR as superseded
    prior_deployed = db.query(ChangeRequest).filter(ChangeRequest.status == "DEPLOYED").all()
    for item in prior_deployed:
        item.status = "SUPERSEDED"

    old_status = cr.status
    cr.status = "DEPLOYED"
    cr.deployed_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(cr)

    record_audit(
        db=db,
        action="CHANGE_DEPLOYED",
        entity_type="CHANGE_REQUEST",
        entity_id=cr.change_id,
        actor=deployer,
        old_value=old_status,
        new_value=f"DEPLOYED version {cr.proposed_rule_version} (Threshold: {cr.new_threshold})",
        status="SUCCESS"
    )
    return cr
