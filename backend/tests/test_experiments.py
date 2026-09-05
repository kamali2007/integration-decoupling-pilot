def test_decoupling_kpi_calculation(client):
    res = client.get("/api/experiments/metrics")
    assert res.status_code == 200
    data = res.json()

    # Core KPI verification
    assert data["baseline_systems_changed"] == 6
    assert data["decoupled_systems_changed"] == 1
    assert data["improvement_pct"] == 83.3
    assert data["reduction_count"] == 5


def test_run_experiment_endpoint(client):
    res = client.post("/api/experiments/run?threshold=200")
    assert res.status_code == 200
    exp = res.json()
    assert exp["baseline_systems_changed"] == 6
    assert exp["decoupled_systems_changed"] == 1
    assert exp["improvement_pct"] == 83.3
    assert exp["run_id"].startswith("EXP-")
