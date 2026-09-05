import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import SystemStatus
from app.schemas import SystemStatusResponse, SystemSimulationRequest
from app.services.audit_service import record_audit

router = APIRouter(prefix="/systems", tags=["Integration Systems"])


@router.get("", response_model=List[SystemStatusResponse])
def list_systems(db: Session = Depends(get_db)):
    """Returns the live statuses of all integrated systems."""
    return db.query(SystemStatus).all()


@router.post("/simulate", response_model=SystemStatusResponse)
def simulate_system_status(payload: SystemSimulationRequest, db: Session = Depends(get_db)):
    """
    Modifies system state in SQLite database.
    Supports: Simulate ERP Delay, Simulate Forecast Delay, Simulate Supplier Failure, Recover Supplier.
    """
    sys = db.query(SystemStatus).filter(SystemStatus.system_name == payload.system_name).first()
    if not sys:
        raise HTTPException(status_code=404, detail=f"System {payload.system_name} not found")

    old_status = sys.status
    sys.status = payload.target_status
    if payload.latency_ms is not None:
        sys.latency_ms = payload.latency_ms
    elif payload.target_status == "DELAYED":
        sys.latency_ms = 4500
    elif payload.target_status == "OFFLINE":
        sys.latency_ms = 0
    elif payload.target_status == "ONLINE":
        sys.latency_ms = 35

    if payload.error_rate is not None:
        sys.error_rate = payload.error_rate
    elif payload.target_status == "OFFLINE":
        sys.error_rate = 1.0
    elif payload.target_status == "ONLINE":
        sys.error_rate = 0.0

    if payload.details:
        sys.details = payload.details
    sys.last_heartbeat = datetime.datetime.utcnow()

    db.commit()
    db.refresh(sys)

    record_audit(
        db=db,
        action="SYSTEM_STATUS_CHANGED",
        entity_type="SYSTEM",
        entity_id=sys.system_name,
        old_value=old_status,
        new_value=sys.status,
        status="WARNING" if sys.status != "ONLINE" else "SUCCESS"
    )

    return sys


@router.post("/recover-all", response_model=List[SystemStatusResponse])
def recover_all_systems(db: Session = Depends(get_db)):
    """Restores all systems to ONLINE with normal latencies."""
    systems = db.query(SystemStatus).all()
    for sys in systems:
        sys.status = "ONLINE"
        sys.latency_ms = 35
        sys.error_rate = 0.0
        sys.last_heartbeat = datetime.datetime.utcnow()
    db.commit()
    return systems
