from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import StakeholderValidation
from app.schemas import StakeholderValidationCreate, StakeholderValidationResponse

router = APIRouter(prefix="/validation", tags=["Stakeholder Validation"])


@router.get("", response_model=List[StakeholderValidationResponse])
def list_validations(db: Session = Depends(get_db)):
    return db.query(StakeholderValidation).order_by(StakeholderValidation.created_at.desc()).all()


@router.get("/summary")
def get_validation_summary(db: Session = Depends(get_db)):
    """Computes aggregate ratings and summary for stakeholder validation."""
    validations = db.query(StakeholderValidation).all()
    count = len(validations)
    if count == 0:
        return {
            "response_count": 0,
            "average_overall_score": 0.0,
            "category_averages": {},
            "label": "Prototype Validation – Sample/Simulated",
            "key_takeaways": []
        }

    avg_flow = sum(v.score_flow for v in validations) / count
    avg_health = sum(v.score_health for v in validations) / count
    avg_recovery = sum(v.score_recovery for v in validations) / count
    avg_change = sum(v.score_change for v in validations) / count
    avg_rollback = sum(v.score_rollback for v in validations) / count
    avg_decoupling = sum(v.score_decoupling for v in validations) / count
    overall_avg = (avg_flow + avg_health + avg_recovery + avg_change + avg_rollback + avg_decoupling) / 6.0

    return {
        "response_count": count,
        "average_overall_score": round(overall_avg, 2),
        "label": "Prototype Validation – Sample/Simulated",
        "category_averages": {
            "event_flow": round(avg_flow, 2),
            "integration_health": round(avg_health, 2),
            "failure_recovery": round(avg_recovery, 2),
            "change_workflow": round(avg_change, 2),
            "rollback_clarity": round(avg_rollback, 2),
            "decoupling_ease": round(avg_decoupling, 2)
        },
        "positive_feedback": [
            "83.3% blast radius reduction provides an executive-ready case for canonical decoupling.",
            "Visualizing adapter transformations side-by-side clarifies supplier schema isolation.",
            "Audited rollback eliminates risk of uncontrolled production business-rule changes."
        ],
        "improvement_areas": [
            "Add automated alerting hooks (e.g. Slack/PagerDuty webhooks) when supplier failure retries exhaust.",
            "Provide self-service JSON schema editor for prospective new supplier adapters."
        ]
    }


@router.post("", response_model=StakeholderValidationResponse, status_code=201)
def submit_validation(payload: StakeholderValidationCreate, db: Session = Depends(get_db)):
    """Allows simulated and prototype stakeholder feedback to be persisted in SQLite."""
    entry = StakeholderValidation(
        respondent_name=payload.respondent_name,
        respondent_role=payload.respondent_role,
        score_flow=payload.score_flow,
        score_health=payload.score_health,
        score_recovery=payload.score_recovery,
        score_change=payload.score_change,
        score_rollback=payload.score_rollback,
        score_decoupling=payload.score_decoupling,
        comments=payload.comments,
        is_simulated=True
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry
