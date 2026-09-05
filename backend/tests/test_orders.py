def test_create_order_and_canonical_event(client):
    payload = {
        "supplier_id": "SUP-A",
        "product_id": "PROD-101",
        "quantity": 150,
        "unit": "EA",
        "is_urgent": True,
        "delivery_date": "2026-09-30",
        "source_system": "ERP"
    }
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["supplier_id"] == "SUP-A"
    assert data["quantity"] == 150
    assert data["is_urgent"] is True

    # Check that canonical event was generated and marked PRIORITY_HIGH (since qty >= 100 and is_urgent)
    events_res = client.get(f"/api/events?supplier_id=SUP-A")
    assert events_res.status_code == 200
    events = events_res.json()
    order_event = next((e for e in events if e.get("order_id") == data["order_id"]), None)
    assert order_event is not None
    assert order_event["priority"] == "PRIORITY_HIGH"
    assert order_event["business_rule_version"] == "BR-1.0"


def test_create_urgent_order_below_threshold(client):
    payload = {
        "supplier_id": "SUP-B",
        "product_id": "PROD-102",
        "quantity": 80,
        "unit": "EA",
        "is_urgent": True,
        "delivery_date": "2026-10-05",
        "source_system": "ERP"
    }
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Below threshold (80 < 100), so priority remains NORMAL
    events_res = client.get(f"/api/events?supplier_id=SUP-B")
    events = events_res.json()
    order_event = next((e for e in events if e.get("order_id") == data["order_id"]), None)
    assert order_event is not None
    assert order_event["priority"] == "NORMAL"


def test_order_validation_failure(client):
    # Invalid quantity <= 0
    payload = {
        "supplier_id": "SUP-A",
        "product_id": "PROD-101",
        "quantity": -5,
        "delivery_date": "2026-10-01"
    }
    response = client.post("/api/orders", json=payload)
    assert response.status_code == 422  # Pydantic validation error
