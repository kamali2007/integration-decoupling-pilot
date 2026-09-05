from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ExperimentRun
from app.schemas import ExperimentRunResponse
from app.services.experiment_service import run_decoupling_experiment, get_all_experiment_runs
from app.services.baseline_service import compare_architectures

router = APIRouter(prefix="/experiments", tags=["Experiments"])


@router.get("", response_model=List[ExperimentRunResponse])
def list_experiment_runs(db: Session = Depends(get_db)):
    return get_all_experiment_runs(db)


@router.get("/metrics")
def get_current_kpi_comparison():
    """Returns the live calculated KPI metrics comparing Baseline vs Decoupled."""
    return compare_architectures(new_threshold=200)


@router.post("/run", response_model=ExperimentRunResponse)
def execute_experiment(
    threshold: int = 200,
    db: Session = Depends(get_db)
):
    """Executes the decoupling benchmark simulation and persists the run."""
    try:
        return run_decoupling_experiment(
            db=db,
            rule_change_name=f"CR-001 Urgent Order Threshold (100 -> {threshold})",
            threshold=threshold
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
