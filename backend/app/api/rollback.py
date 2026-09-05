from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import RollbackAction
from app.schemas import RollbackRequest, RollbackResponse
from app.services.rollback_service import get_all_rollbacks, execute_rollback

router = APIRouter(prefix="/rollback", tags=["Rollback"])


@router.get("", response_model=List[RollbackResponse])
def list_rollback_actions(db: Session = Depends(get_db)):
    return get_all_rollbacks(db)


@router.post("", response_model=RollbackResponse)
def trigger_rollback(payload: RollbackRequest, db: Session = Depends(get_db)):
    """Executes rule rollback to previous version and records full audit log."""
    try:
        return execute_rollback(
            db=db,
            change_id=payload.change_id,
            initiated_by=payload.initiated_by,
            reason=payload.reason
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
