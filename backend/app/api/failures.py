from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import FailureCase
from app.schemas import FailureCaseResponse, FailureSimulateRequest
from app.services.failure_service import (
    simulate_failure,
    retry_failure,
    resolve_failure
)

router = APIRouter(prefix="/failures", tags=["Failures"])


@router.get("", response_model=List[FailureCaseResponse])
def list_failures(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(FailureCase)
    if status:
        query = query.filter(FailureCase.status == status)
    if severity:
        query = query.filter(FailureCase.severity == severity)
    return query.order_by(FailureCase.created_at.desc()).limit(limit).all()


@router.post("/simulate", response_model=FailureCaseResponse)
def trigger_simulated_failure(
    payload: FailureSimulateRequest,
    db: Session = Depends(get_db)
):
    """Simulates one of the 5 realistic failure modes."""
    try:
        return simulate_failure(
            db=db,
            failure_type=payload.failure_type,
            target_system=payload.target_system
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{failure_id}/retry", response_model=FailureCaseResponse)
def retry_failure_case(failure_id: str, db: Session = Depends(get_db)):
    """Retries and attempts recovery of a failure case."""
    try:
        return retry_failure(db, failure_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/{failure_id}/resolve", response_model=FailureCaseResponse)
def resolve_failure_case(failure_id: str, db: Session = Depends(get_db)):
    """Manually marks a failure as resolved."""
    try:
        return resolve_failure(db, failure_id)
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc))
