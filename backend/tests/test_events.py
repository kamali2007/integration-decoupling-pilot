from app.models import Order
from app.services.canonical_event_service import create_order_canonical_event


def test_idempotency_duplicate_event_handling(client, db_session):
    # Create an order
    order = Order(
        order_id="ORD-IDEMP-999",
        supplier_id="SUP-A",
        product_id="PROD-105",
        quantity=130,
        unit="EA",
        is_urgent=True,
        delivery_date="2026-10-20",
        source_system="ERP",
        correlation_id="CORR-IDEMP-01"
    )
    db_session.add(order)
    db_session.commit()

    # First ingestion
    evt1, is_new1 = create_order_canonical_event(db_session, order, idempotency_key="UNIQUE-KEY-001")
    assert is_new1 is True
    assert evt1.status == "PROCESSED"

    # Second ingestion of the identical event
    evt2, is_new2 = create_order_canonical_event(db_session, order, idempotency_key="UNIQUE-KEY-001")
    assert is_new2 is False
    assert evt2.event_id == evt1.event_id

    # Verify audit log recorded DUPLICATE_DETECTED
    audit_res = client.get("/api/audit?action=DUPLICATE_DETECTED")
    assert audit_res.status_code == 200
    audits = audit_res.json()
    assert len(audits) > 0
    assert audits[0]["action"] == "DUPLICATE_DETECTED"
