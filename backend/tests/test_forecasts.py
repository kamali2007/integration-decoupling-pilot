def test_create_forecast(client):
    payload = {
        "supplier_id": "SUP-C",
        "product_id": "PROD-103",
        "forecast_quantity": 750,
        "forecast_period": "2026-Q4",
        "source_system": "FORECAST_SYSTEM",
        "confidence_level": 0.94
    }
    response = client.post("/api/forecasts", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["forecast_id"].startswith("FCST-")
    assert data["forecast_quantity"] == 750
    assert data["forecast_period"] == "2026-Q4"


def test_forecast_delay_does_not_crash_system(client):
    # 1. Simulate Forecast Delay in SystemStatus
    client.post("/api/systems/simulate", json={
        "system_name": "FORECAST",
        "target_status": "DELAYED"
    })

    # 2. Orders should STILL work completely fine (Requirement 9: Case 1)
    order_res = client.post("/api/orders", json={
        "supplier_id": "SUP-A",
        "product_id": "PROD-104",
        "quantity": 110,
        "unit": "EA",
        "is_urgent": True,
        "delivery_date": "2026-11-15",
        "source_system": "ERP"
    })
    assert order_res.status_code == 201

    # 3. Forecast creation under delay records as DELAYED without crashing
    fcst_res = client.post("/api/forecasts", json={
        "supplier_id": "SUP-B",
        "product_id": "PROD-104",
        "forecast_quantity": 400,
        "forecast_period": "2026-Q4"
    })
    assert fcst_res.status_code == 201
    assert fcst_res.json()["status"] == "DELAYED"

    # Restore system
    client.post("/api/systems/recover-all")
