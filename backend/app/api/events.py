from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CanonicalEvent, AdapterDelivery
from app.schemas import CanonicalEventResponse, AdapterDeliveryResponse
from app.services.adapter_service import dispatch_event_to_adapter

router = APIRouter(prefix="/events", tags=["Canonical Events"])


@router.get("", response_model=List[CanonicalEventResponse])
def list_canonical_events(
    event_type: Optional[str] = None,
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(CanonicalEvent)
    if event_type:
        query = query.filter(CanonicalEvent.event_type == event_type)
    if supplier_id:
        query = query.filter(CanonicalEvent.supplier_id == supplier_id)
    if status:
        query = query.filter(CanonicalEvent.status == status)
    return query.order_by(CanonicalEvent.created_at.desc()).limit(limit).all()


@router.get("/{event_id}", response_model=CanonicalEventResponse)
def get_canonical_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(CanonicalEvent).filter(CanonicalEvent.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return event


@router.post("/process")
def process_pending_events(db: Session = Depends(get_db)):
    """Processes pending canonical events and dispatches to supplier adapters."""
    pending = db.query(CanonicalEvent).filter(CanonicalEvent.status.in_(["PENDING", "RETRYING"])).all()
    processed_count = 0
    for evt in pending:
        dispatch_event_to_adapter(db, evt)
        evt.status = "PROCESSED"
        processed_count += 1
    db.commit()
    return {"message": f"Processed {processed_count} pending canonical events."}
