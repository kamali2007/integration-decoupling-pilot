from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MessageQueueItem
from app.schemas import (
    QueuedMessageCreate,
    QueuedMessageResponse,
    QueueProcessResponse,
    QueueStatsResponse
)
from app.services.queue_service import (
    enqueue_message,
    process_message,
    retry_message,
    process_all_queued,
    get_queue_stats
)

router = APIRouter(prefix="/queue", tags=["Asynchronous Message Queue"])


@router.get("", response_model=List[QueuedMessageResponse])
def list_queue_messages(
    status: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lists queued messages with optional status and topic filters."""
    query = db.query(MessageQueueItem)
    if status:
        query = query.filter(MessageQueueItem.status == status)
    if topic:
        query = query.filter(MessageQueueItem.topic == topic)
    return query.order_by(MessageQueueItem.created_at.desc()).limit(limit).all()


@router.get("/stats", response_model=QueueStatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Returns queue status counts and metrics."""
    return get_queue_stats(db)


@router.post("/enqueue", response_model=QueuedMessageResponse, status_code=201)
def enqueue(payload: QueuedMessageCreate, db: Session = Depends(get_db)):
    """
    Enqueues a message into the asynchronous message queue / buffer.
    Guarantees idempotency protection when idempotency_key is supplied.
    """
    item, is_new = enqueue_message(
        db=db,
        topic=payload.topic,
        payload=payload.payload,
        idempotency_key=payload.idempotency_key,
        source_system=payload.source_system,
        correlation_id=payload.correlation_id
    )
    return item


@router.post("/process/{queue_id}", response_model=QueueProcessResponse)
def process_single(
    queue_id: str,
    simulate_failure: bool = Query(default=False),
    db: Session = Depends(get_db)
):
    """Processes a single message from the queue with optional failure simulation."""
    try:
        success, detail, item, evt_id = process_message(
            db=db,
            queue_id=queue_id,
            simulate_failure=simulate_failure
        )
        return QueueProcessResponse(
            success=success,
            queue_id=item.queue_id,
            status=item.status,
            detail=detail,
            attempt_count=item.retry_count,
            canonical_event_id=evt_id
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/retry/{queue_id}", response_model=QueueProcessResponse)
def retry_single(queue_id: str, db: Session = Depends(get_db)):
    """Retries a failed or retrying message in the queue."""
    try:
        success, detail, item, evt_id = retry_message(db=db, queue_id=queue_id)
        return QueueProcessResponse(
            success=success,
            queue_id=item.queue_id,
            status=item.status,
            detail=detail,
            attempt_count=item.retry_count,
            canonical_event_id=evt_id
        )
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))


@router.post("/process-all")
def process_all(db: Session = Depends(get_db)):
    """Drains and processes all queued/pending messages in FIFO order."""
    return process_all_queued(db)
