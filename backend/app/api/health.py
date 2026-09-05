import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint validating database connectivity and system status."""
    db_status = "HEALTHY"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"UNHEALTHY: {str(exc)}"

    return {
        "status": "UP" if db_status == "HEALTHY" else "DEGRADED",
        "service": "Integration Control Tower - Canonical Gateway",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "database": db_status
    }
