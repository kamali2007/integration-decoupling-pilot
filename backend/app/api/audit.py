from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AuditEntry
from app.schemas import AuditEntryResponse

router = APIRouter(prefix="/audit", tags=["Audit Trail"])


@router.get("", response_model=List[AuditEntryResponse])
def list_audit_trail(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    query = db.query(AuditEntry)
    if action:
        query = query.filter(AuditEntry.action == action)
    if entity_type:
        query = query.filter(AuditEntry.entity_type == entity_type)
    if status:
        query = query.filter(AuditEntry.status == status)
    if search:
        query = query.filter(
            (AuditEntry.entity_id.ilike(f"%{search}%")) |
            (AuditEntry.action.ilike(f"%{search}%")) |
            (AuditEntry.actor.ilike(f"%{search}%"))
        )
    return query.order_by(AuditEntry.timestamp.desc()).limit(limit).all()
