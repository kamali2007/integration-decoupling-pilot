import datetime
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Order, SystemStatus
from app.schemas import OrderCreate, OrderResponse
from app.services.canonical_event_service import create_order_canonical_event
from app.services.adapter_service import dispatch_event_to_adapter
from app.services.audit_service import record_audit

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", response_model=List[OrderResponse])
def list_orders(
    supplier_id: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Order)
    if supplier_id:
        query = query.filter(Order.supplier_id == supplier_id)
    return query.order_by(Order.created_at.desc()).limit(limit).all()


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db)
):
    """
    Creates an order from ERP.
    1. Validates payload
    2. Checks source system status (gracefully handles DELAYED without crashing)
    3. Persists Order
    4. Automatically generates Canonical Event
    5. Dispatches to Supplier Adapter
    6. Records comprehensive Audit Entry
    """
    # Check ERP status
    erp_status = db.query(SystemStatus).filter(SystemStatus.system_name == "ERP").first()
    is_delayed = erp_status and erp_status.status in ("DELAYED", "DEGRADED")

    order_id = payload.order_id or f"ORD-{uuid.uuid4().hex[:6].upper()}"
    correlation_id = f"CORR-{uuid.uuid4().hex[:8].upper()}"

    # Check if order_id exists
    existing = db.query(Order).filter(Order.order_id == order_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Order {order_id} already exists")

    order = Order(
        order_id=order_id,
        supplier_id=payload.supplier_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
        unit=payload.unit,
        is_urgent=payload.is_urgent,
        delivery_date=payload.delivery_date,
        source_system=payload.source_system,
        status="PENDING" if is_delayed else "PROCESSED",
        correlation_id=correlation_id,
        created_at=datetime.datetime.utcnow()
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Audit order creation
    record_audit(
        db=db,
        action="ORDER_CREATED",
        entity_type="ORDER",
        entity_id=order.order_id,
        new_value=f"Created order {order.order_id} ({order.quantity} {order.unit}, Urgent={order.is_urgent})",
        status="SUCCESS",
        correlation_id=correlation_id
    )

    # Create Canonical Event and dispatch if not delayed
    canonical_event, is_new = create_order_canonical_event(db, order)
    if is_new and not is_delayed:
        dispatch_event_to_adapter(db, canonical_event)
        order.status = "PROCESSED"
        db.commit()
        db.refresh(order)

    return order
