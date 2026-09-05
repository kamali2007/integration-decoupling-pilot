from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AdapterDelivery, CanonicalEvent
from app.schemas import AdapterDeliveryResponse
from app.adapters.supplier_a import SupplierAAdapter
from app.adapters.supplier_b import SupplierBAdapter
from app.adapters.supplier_c import SupplierCAdapter
from app.services.adapter_service import dispatch_event_to_adapter, retry_adapter_delivery

router = APIRouter(prefix="/adapters", tags=["Adapters"])


@router.get("", response_model=List[AdapterDeliveryResponse])
def list_adapter_deliveries(
    supplier_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(AdapterDelivery)
    if supplier_id:
        query = query.filter(AdapterDelivery.supplier_id == supplier_id)
    if status:
        query = query.filter(AdapterDelivery.delivery_status == status)
    return query.order_by(AdapterDelivery.created_at.desc()).limit(limit).all()


@router.get("/compare-transformations")
def compare_transformations(event_id: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Shows side-by-side how the exact same canonical order event is transformed
    differently by Supplier A, Supplier B, and Supplier C adapters.
    """
    event = None
    if event_id:
        event = db.query(CanonicalEvent).filter(CanonicalEvent.event_id == event_id).first()
    if not event:
        event = db.query(CanonicalEvent).filter(CanonicalEvent.event_type == "ORDER_CREATED").first()

    canonical_sample = event.raw_payload if event else {
        "event_id": "EVT-10001",
        "order_id": "ORD-1001",
        "supplier_id": "SUP-A",
        "product_id": "PROD-101",
        "quantity": 150,
        "priority": "PRIORITY_HIGH",
        "delivery_date": "2026-09-20",
        "correlation_id": "CORR-001"
    }

    adapter_a = SupplierAAdapter()
    adapter_b = SupplierBAdapter()
    adapter_c = SupplierCAdapter()

    return {
        "canonical_event": canonical_sample,
        "transformations": {
            "supplier_a": {
                "name": "Alpha Components",
                "format_spec": "Alpha REST v1 JSON",
                "payload": adapter_a.transform(canonical_sample)
            },
            "supplier_b": {
                "name": "Beta Manufacturing",
                "format_spec": "Beta SOAP/JSON EDI v2",
                "payload": adapter_b.transform(canonical_sample)
            },
            "supplier_c": {
                "name": "Gamma Parts",
                "format_spec": "Gamma SAP/RFC Gateway JSON",
                "payload": adapter_c.transform(canonical_sample)
            }
        }
    }


@router.post("/retry/{delivery_id}", response_model=AdapterDeliveryResponse)
def retry_delivery(delivery_id: str, db: Session = Depends(get_db)):
    """Retries a failed adapter delivery transmission."""
    try:
        return retry_adapter_delivery(db, delivery_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
