def test_change_approval_deploy_and_rollback_flow(client):
    # 1. Create a Change Request
    cr_res = client.post("/api/changes", json={
        "title": "Shift Priority Threshold to 200",
        "description": "Increase volume requirement for urgent high-priority flags to 200 EA.",
        "new_threshold": 200,
        "submitted_by": "Senior Architect"
    })
    assert cr_res.status_code == 201
    cr = cr_res.json()
    change_id = cr["change_id"]
    assert cr["status"] == "DRAFT"

    # 2. Cannot deploy directly from DRAFT (Approval is strictly required)
    fail_deploy = client.post(f"/api/changes/{change_id}/deploy")
    assert fail_deploy.status_code == 400

    # 3. Submit and Approve
    client.post(f"/api/changes/{change_id}/submit")
    app_res = client.post(f"/api/changes/{change_id}/approve?approver=ChiefArchitect")
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "APPROVED"

    # 4. Deploy Change (Now active rule is BR-2.0 with threshold 200)
    dep_res = client.post(f"/api/changes/{change_id}/deploy")
    assert dep_res.status_code == 200
    assert dep_res.json()["status"] == "DEPLOYED"

    # 5. Under BR-2.0, an urgent order with quantity 150 should be NORMAL (150 < 200)
    ord_res1 = client.post("/api/orders", json={
        "supplier_id": "SUP-A",
        "product_id": "PROD-101",
        "quantity": 150,
        "unit": "EA",
        "is_urgent": True,
        "delivery_date": "2026-11-01"
    })
    order_data1 = ord_res1.json()
    events_res1 = client.get("/api/events?supplier_id=SUP-A")
    evt1 = next(e for e in events_res1.json() if e.get("order_id") == order_data1["order_id"])
    assert evt1["priority"] == "NORMAL"
    assert evt1["business_rule_version"] == "BR-2.0"

    # 6. Execute Rollback
    rb_res = client.post(f"/api/changes/{change_id}/rollback?reason=ProductionReversal")
    assert rb_res.status_code == 200
    rb_data = rb_res.json()
    assert rb_data["restored_version"] == "BR-1.0"

    # 7. Under restored BR-1.0, an urgent order with quantity 150 should be PRIORITY_HIGH (150 >= 100)
    ord_res2 = client.post("/api/orders", json={
        "supplier_id": "SUP-B",
        "product_id": "PROD-101",
        "quantity": 150,
        "unit": "EA",
        "is_urgent": True,
        "delivery_date": "2026-11-02"
    })
    order_data2 = ord_res2.json()
    events_res2 = client.get("/api/events?supplier_id=SUP-B")
    evt2 = next(e for e in events_res2.json() if e.get("order_id") == order_data2["order_id"])
    assert evt2["priority"] == "PRIORITY_HIGH"
    assert evt2["business_rule_version"] == "BR-1.0"

    # 8. Check Audit Trail recorded ROLLBACK_COMPLETED
    audit_res = client.get("/api/audit?action=ROLLBACK_COMPLETED")
    assert audit_res.status_code == 200
    audits = audit_res.json()
    assert len(audits) > 0
