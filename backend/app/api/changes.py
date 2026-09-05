from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChangeRequest
from app.schemas import ChangeRequestCreate, ChangeRequestResponse
from app.services.change_service import (
    get_all_changes,
    get_change_by_id,
    create_change_request,
    submit_for_review,
    approve_change,
    reject_change,
    deploy_change
)
from app.services.rollback_service import execute_rollback

router = APIRouter(prefix="/changes", tags=["Change Management"])


@router.get("", response_model=List[ChangeRequestResponse])
def list_changes(db: Session = Depends(get_db)):
    return get_all_changes(db)


@router.get("/{change_id}", response_model=ChangeRequestResponse)
def get_change(change_id: str, db: Session = Depends(get_db)):
    cr = get_change_by_id(db, change_id)
    if not cr:
        raise HTTPException(status_code=404, detail=f"Change request {change_id} not found")
    return cr


@router.post("", response_model=ChangeRequestResponse, status_code=201)
def create_change(payload: ChangeRequestCreate, db: Session = Depends(get_db)):
    return create_change_request(
        db=db,
        title=payload.title,
        description=payload.description,
        new_threshold=payload.new_threshold,
        submitted_by=payload.submitted_by,
        notes=payload.notes
    )


@router.post("/{change_id}/submit", response_model=ChangeRequestResponse)
def submit_change(change_id: str, actor: str = Query(default="Supply Chain Architect"), db: Session = Depends(get_db)):
    try:
        return submit_for_review(db, change_id, actor)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{change_id}/approve", response_model=ChangeRequestResponse)
def approve_change_request(
    change_id: str,
    approver: str = Query(default="Lead Enterprise Architect"),
    db: Session = Depends(get_db)
):
    try:
        return approve_change(db, change_id, approver)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{change_id}/reject", response_model=ChangeRequestResponse)
def reject_change_request(
    change_id: str,
    reviewer: str = Query(default="Lead Enterprise Architect"),
    reason: str = Query(default="Downstream readiness not verified"),
    db: Session = Depends(get_db)
):
    try:
        return reject_change(db, change_id, reviewer, reason)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{change_id}/deploy", response_model=ChangeRequestResponse)
def deploy_change_request(
    change_id: str,
    deployer: str = Query(default="DevOps Engineer"),
    db: Session = Depends(get_db)
):
    """Deploys an approved change request. High-impact changes REQUIRE prior approval."""
    try:
        return deploy_change(db, change_id, deployer)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{change_id}/rollback")
def rollback_change_request(
    change_id: str,
    initiated_by: str = Query(default="Release Manager"),
    reason: str = Query(default="Downstream regression detected"),
    db: Session = Depends(get_db)
):
    try:
        rb = execute_rollback(db, change_id, initiated_by, reason)
        return {
            "message": f"Change {change_id} successfully rolled back to previous rule version",
            "rollback_id": rb.rollback_id,
            "status": rb.status,
            "restored_version": rb.to_version
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
