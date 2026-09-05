def test_list_failures(client):
    res = client.get("/api/failures")
    assert res.status_code == 200
    failures = res.json()
    assert len(failures) >= 5  # At least 5 failure modes populated
    types = {f["failure_type"] for f in failures}
    assert "MISSING_DATA" in types
    assert "DELAYED_DATA" in types
    assert "SCHEMA_VIOLATION" in types
    assert "ENDPOINT_UNAVAILABLE" in types
    assert "DUPLICATE_EVENT" in types


def test_simulate_and_retry_failure(client):
    # 1. Simulate endpoint unavailable failure
    sim_res = client.post("/api/failures/simulate", json={
        "failure_type": "ENDPOINT_UNAVAILABLE",
        "target_system": "SUP-C"
    })
    assert sim_res.status_code == 200
    fail_data = sim_res.json()
    assert fail_data["status"] == "OPEN"
    fail_id = fail_data["failure_id"]

    # 2. Retry the failure
    retry_res = client.post(f"/api/failures/{fail_id}/retry")
    assert retry_res.status_code == 200
    recovered_data = retry_res.json()
    assert recovered_data["status"] == "RESOLVED"
    assert recovered_data["retry_count"] >= 1
