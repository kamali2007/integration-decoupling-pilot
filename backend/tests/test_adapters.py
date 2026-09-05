from app.adapters.supplier_a import SupplierAAdapter
from app.adapters.supplier_b import SupplierBAdapter
from app.adapters.supplier_c import SupplierCAdapter


def test_supplier_a_adapter_transformation():
    adapter = SupplierAAdapter()
    canonical = {
        "event_id": "EVT-101",
        "order_id": "ORD-5001",
        "product_id": "PROD-201",
        "quantity": 140,
        "priority": "PRIORITY_HIGH",
        "delivery_date": "2026-10-15",
        "correlation_id": "CORR-501"
    }
    is_valid, msg = adapter.validate(canonical)
    assert is_valid is True

    result = adapter.transform(canonical)
    assert result["orderNumber"] == "ORD-5001"
    assert result["itemCode"] == "PROD-201"
    assert result["qty"] == 140
    assert result["dispatchPriority"] == "EXPEDITED"


def test_supplier_b_adapter_transformation():
    adapter = SupplierBAdapter()
    canonical = {
        "event_id": "EVT-102",
        "order_id": "ORD-5002",
        "product_id": "PROD-202",
        "quantity": 180,
        "priority": "PRIORITY_HIGH",
        "delivery_date": "2026-10-16",
        "correlation_id": "CORR-502"
    }
    is_valid, msg = adapter.validate(canonical)
    assert is_valid is True

    result = adapter.transform(canonical)
    assert result["poRef"] == "ORD-5002"
    assert result["partNumber"] == "PROD-202"
    assert result["orderedQuantity"] == 180
    assert result["urgencyLevel"] == "CRITICAL"


def test_supplier_c_adapter_transformation():
    adapter = SupplierCAdapter()
    canonical = {
        "event_id": "EVT-103",
        "order_id": "ORD-5003",
        "product_id": "PROD-203",
        "quantity": 90,
        "priority": "NORMAL",
        "delivery_date": "2026-10-17",
        "correlation_id": "CORR-503"
    }
    is_valid, msg = adapter.validate(canonical)
    assert is_valid is True

    result = adapter.transform(canonical)
    assert result["ORDER_NO"] == "ORD-5003"
    assert result["SKU"] == "PROD-203"
    assert result["QTY"] == 90
    assert result["EXPEDITE_FLAG"] is False


def test_adapter_compare_endpoint(client):
    res = client.get("/api/adapters/compare-transformations")
    assert res.status_code == 200
    data = res.json()
    assert "canonical_event" in data
    assert "transformations" in data
    assert "supplier_a" in data["transformations"]
    assert "supplier_b" in data["transformations"]
    assert "supplier_c" in data["transformations"]
