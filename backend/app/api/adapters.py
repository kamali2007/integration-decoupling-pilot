from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AdapterDelivery, CanonicalEvent
from app.schemas import (
    AdapterDeliveryResponse,
    SupplierValidationRequest,
    SupplierValidationResponse
)
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


@router.get("/contracts")
def get_supplier_contracts():
    """Exposes explicit schema contracts and field specifications for all suppliers."""
    adapter_a = SupplierAAdapter()
    adapter_b = SupplierBAdapter()
    adapter_c = SupplierCAdapter()
    return {
        "contracts": [
            adapter_a.get_contract_spec(),
            adapter_b.get_contract_spec(),
            adapter_c.get_contract_spec()
        ]
    }


@router.post("/validate", response_model=SupplierValidationResponse)
def validate_supplier_payload(payload_data: SupplierValidationRequest):
    """
    Validates a raw supplier payload against the specified supplier's explicit schema contract.
    Returns clear, understandable validation errors or a canonical event preview upon success.
    """
    supplier_code = payload_data.supplier_code.upper()
    adapter_map = {
        "SUP-A": SupplierAAdapter(),
        "SUP-B": SupplierBAdapter(),
        "SUP-C": SupplierCAdapter()
    }
    adapter = adapter_map.get(supplier_code)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Unknown supplier code '{supplier_code}'. Valid codes: SUP-A, SUP-B, SUP-C")

    is_valid, msg, parsed_model, errors = adapter.validate_inbound_message(payload_data.payload)
    preview = adapter.transform_to_canonical(parsed_model) if is_valid and parsed_model else None

    return SupplierValidationResponse(
        valid=is_valid,
        supplier_code=supplier_code,
        adapter_name=adapter.SUPPLIER_NAME,
        message=msg,
        errors=errors if not is_valid else None,
        canonical_preview=preview
    )


@router.post("/{supplier_code}/ingest")
def ingest_supplier_message(
    supplier_code: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Ingests an inbound message directly from a supplier in their proprietary schema.
    1. Validates strictly against explicit Pydantic schema contract (rejecting invalid with 422).
    2. Performs supplier-specific transformation inside the adapter into canonical format.
    3. Evaluates business rules in canonical layer.
    """
    supplier_code = supplier_code.upper()
    adapter_map = {
        "SUP-A": SupplierAAdapter(),
        "SUP-B": SupplierBAdapter(),
        "SUP-C": SupplierCAdapter()
    }
    adapter = adapter_map.get(supplier_code)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Unknown supplier '{supplier_code}'")

    is_valid, msg, parsed_model, errors = adapter.validate_inbound_message(payload)
    if not is_valid:
        raise HTTPException(
            status_code=422,
            detail={
                "message": f"Supplier {supplier_code} schema validation failed",
                "errors": errors,
                "schema_contract": adapter.FORMAT_SPEC
            }
        )

    # Transform to canonical within the adapter
    canonical_dict = adapter.transform_to_canonical(parsed_model)

    import uuid
    import datetime
    from app.models import Order
    from app.services.canonical_event_service import create_order_canonical_event

    order_id = canonical_dict["order_id"]
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        order = Order(
            order_id=order_id,
            supplier_id=canonical_dict["supplier_id"],
            product_id=canonical_dict["product_id"],
            quantity=canonical_dict["quantity"],
            unit=canonical_dict.get("unit", "EA"),
            is_urgent=canonical_dict.get("is_urgent", False),
            delivery_date=canonical_dict["delivery_date"],
            source_system=canonical_dict.get("source_system", supplier_code),
            status="PROCESSED",
            correlation_id=f"CORR-IN-{uuid.uuid4().hex[:8].upper()}",
            created_at=datetime.datetime.utcnow()
        )
        db.add(order)
        db.commit()
        db.refresh(order)

    canonical_event, is_new = create_order_canonical_event(db, order)

    return {
        "status": "ACCEPTED",
        "supplier_code": supplier_code,
        "canonical_event_id": canonical_event.event_id,
        "order_id": order.order_id,
        "business_rule_version": canonical_event.business_rule_version,
        "priority": canonical_event.priority,
        "detail": f"Message validated against {adapter.FORMAT_SPEC} contract and canonicalized successfully"
    }


@router.post("/retry/{delivery_id}", response_model=AdapterDeliveryResponse)
def retry_delivery(delivery_id: str, db: Session = Depends(get_db)):
    """Retries a failed adapter delivery transmission."""
    try:
        return retry_adapter_delivery(db, delivery_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

