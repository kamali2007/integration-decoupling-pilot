import pytest


def test_supplier_contracts_metadata_endpoint(client):
    """Test that all supplier adapter contracts are exposed in API documentation/endpoint."""
    res = client.get("/api/adapters/contracts")
    assert res.status_code == 200
    data = res.json()
    assert "contracts" in data
    assert len(data["contracts"]) == 3

    codes = {c["supplier_code"] for c in data["contracts"]}
    assert codes == {"SUP-A", "SUP-B", "SUP-C"}

    # Verify field mappings and required fields are documented
    for contract in data["contracts"]:
        assert "required_fields" in contract
        assert "field_mapping" in contract
        assert len(contract["required_fields"]) > 0


def test_valid_supplier_a_schema_contract(client):
    """Test that a valid Supplier A payload is accepted and canonicalized."""
    valid_payload = {
        "orderNumber": "ORD-ALPHA-801",
        "itemCode": "PROD-101",
        "qty": 175,
        "dispatchPriority": "EXPEDITED",
        "targetDelivery": "2026-11-01"
    }

    # 1. Validation check endpoint
    val_res = client.post("/api/adapters/validate", json={
        "supplier_code": "SUP-A",
        "payload": valid_payload
    })
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["valid"] is True
    assert val_data["canonical_preview"] is not None
    assert val_data["canonical_preview"]["order_id"] == "ORD-ALPHA-801"
    assert val_data["canonical_preview"]["quantity"] == 175
    assert val_data["canonical_preview"]["priority"] == "PRIORITY_HIGH"

    # 2. Ingestion endpoint
    ing_res = client.post("/api/adapters/SUP-A/ingest", json=valid_payload)
    assert ing_res.status_code == 200
    ing_data = ing_res.json()
    assert ing_data["status"] == "ACCEPTED"
    assert ing_data["canonical_event_id"].startswith("EVT-")
    assert ing_data["priority"] == "PRIORITY_HIGH"


def test_invalid_supplier_a_schema_contract(client):
    """Test that an invalid Supplier A payload is rejected with understandable errors."""
    # Missing required 'targetDelivery' and non-positive 'qty'
    invalid_payload = {
        "orderNumber": "ORD-ALPHA-BAD",
        "itemCode": "PROD-101",
        "qty": -10
    }

    # 1. Validation check endpoint
    val_res = client.post("/api/adapters/validate", json={
        "supplier_code": "SUP-A",
        "payload": invalid_payload
    })
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["valid"] is False
    assert val_data["errors"] is not None
    assert len(val_data["errors"]) >= 1

    # 2. Ingestion rejection with 422 Unprocessable Entity
    ing_res = client.post("/api/adapters/SUP-A/ingest", json=invalid_payload)
    assert ing_res.status_code == 422
    err_detail = ing_res.json()["detail"]
    assert "errors" in err_detail
    assert len(err_detail["errors"]) >= 1


def test_valid_and_invalid_supplier_b_schema_contract(client):
    """Test Supplier B contract validation with valid and invalid messages."""
    valid_beta = {
        "poRef": "ORD-BETA-901",
        "partNumber": "PROD-102",
        "orderedQuantity": 220,
        "urgencyLevel": "CRITICAL",
        "requestedDate": "2026-11-10",
        "partnerCode": "MFG-APEX"
    }
    res_valid = client.post("/api/adapters/SUP-B/ingest", json=valid_beta)
    assert res_valid.status_code == 200
    assert res_valid.json()["status"] == "ACCEPTED"
    assert res_valid.json()["priority"] == "PRIORITY_HIGH"

    # Invalid: missing 'partNumber' and orderedQuantity <= 0
    invalid_beta = {
        "poRef": "ORD-BETA-BAD",
        "orderedQuantity": 0,
        "requestedDate": "2026-11-10"
    }
    res_invalid = client.post("/api/adapters/SUP-B/ingest", json=invalid_beta)
    assert res_invalid.status_code == 422
    assert "errors" in res_invalid.json()["detail"]


def test_valid_and_invalid_supplier_c_schema_contract(client):
    """Test Supplier C contract validation with valid and invalid messages."""
    valid_gamma = {
        "ORDER_NO": "ORD-GAMMA-902",
        "SKU": "PROD-103",
        "QTY": 85,
        "EXPEDITE_FLAG": False,
        "SCHEDULE_DATE": "2026-11-12",
        "SYSTEM_ORIGIN": "CANONICAL_GATEWAY"
    }
    res_valid = client.post("/api/adapters/SUP-C/ingest", json=valid_gamma)
    assert res_valid.status_code == 200
    assert res_valid.json()["status"] == "ACCEPTED"
    assert res_valid.json()["priority"] == "NORMAL"

    # Invalid: missing 'ORDER_NO'
    invalid_gamma = {
        "SKU": "PROD-103",
        "QTY": 50,
        "SCHEDULE_DATE": "2026-11-12"
    }
    res_invalid = client.post("/api/adapters/SUP-C/ingest", json=invalid_gamma)
    assert res_invalid.status_code == 422
    assert "errors" in res_invalid.json()["detail"]
