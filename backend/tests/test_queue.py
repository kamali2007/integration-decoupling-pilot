import pytest


def test_queued_message_enqueue_and_process(client):
    """Test that a message enters the queue and is processed through canonical decoupling."""
    payload = {
        "topic": "orders.incoming",
        "payload": {
            "order_id": "ORD-Q-TEST-001",
            "supplier_id": "SUP-A",
            "product_id": "PROD-101",
            "quantity": 160,
            "unit": "EA",
            "is_urgent": True,
            "delivery_date": "2026-11-20"
        },
        "idempotency_key": "IDEMP-Q-TEST-001",
        "source_system": "ERP"
    }

    # 1. Enqueue message
    enq_res = client.post("/api/queue/enqueue", json=payload)
    assert enq_res.status_code == 201
    q_data = enq_res.json()
    assert q_data["status"] == "QUEUED"
    assert q_data["topic"] == "orders.incoming"
    assert q_data["idempotency_key"] == "IDEMP-Q-TEST-001"
    queue_id = q_data["queue_id"]

    # 2. Process message
    proc_res = client.post(f"/api/queue/process/{queue_id}")
    assert proc_res.status_code == 200
    p_data = proc_res.json()
    assert p_data["success"] is True
    assert p_data["status"] == "PROCESSED"
    assert p_data["canonical_event_id"] is not None

    # 3. Verify canonical event was generated
    events_res = client.get("/api/events?supplier_id=SUP-A")
    assert events_res.status_code == 200
    events = events_res.json()
    matched = next((e for e in events if e.get("order_id") == "ORD-Q-TEST-001"), None)
    assert matched is not None
    assert matched["priority"] == "PRIORITY_HIGH"


def test_delayed_message_buffering_and_drain(client):
    """Test that delayed data is gracefully buffered into the queue and can be drained."""
    # 1. Simulate ERP delay
    client.post("/api/systems/simulate", json={
        "system_name": "ERP",
        "target_status": "DELAYED"
    })

    # 2. Create order under delayed ERP status
    order_res = client.post("/api/orders", json={
        "supplier_id": "SUP-B",
        "product_id": "PROD-102",
        "quantity": 90,
        "unit": "EA",
        "is_urgent": False,
        "delivery_date": "2026-11-25",
        "source_system": "ERP"
    })
    assert order_res.status_code == 201
    order_data = order_res.json()
    assert order_data["status"] == "PENDING"
    order_id = order_data["order_id"]

    # 3. Verify message is buffered in queue
    q_res = client.get("/api/queue?topic=orders.buffered")
    assert q_res.status_code == 200
    buffered_items = q_res.json()
    matched_q = next((m for m in buffered_items if m["payload"].get("order_id") == order_id), None)
    assert matched_q is not None
    assert matched_q["status"] == "QUEUED"

    # 4. Drain queue via process-all
    drain_res = client.post("/api/queue/process-all")
    assert drain_res.status_code == 200
    drain_data = drain_res.json()
    assert drain_data["processed_count"] >= 1

    # 5. Restore ERP system
    client.post("/api/systems/recover-all")


def test_queue_retry_and_recovery(client):
    """Test that temporary processing failure triggers retry and subsequent recovery succeeds."""
    payload = {
        "topic": "orders.incoming",
        "payload": {
            "order_id": "ORD-RETRY-001",
            "supplier_id": "SUP-C",
            "product_id": "PROD-103",
            "quantity": 120,
            "unit": "EA",
            "is_urgent": False,
            "delivery_date": "2026-12-01"
        },
        "idempotency_key": "IDEMP-RETRY-001",
        "source_system": "ERP"
    }

    # 1. Enqueue
    enq_res = client.post("/api/queue/enqueue", json=payload)
    assert enq_res.status_code == 201
    queue_id = enq_res.json()["queue_id"]

    # 2. Trigger processing with simulated failure
    fail_res = client.post(f"/api/queue/process/{queue_id}?simulate_failure=true")
    assert fail_res.status_code == 200
    fail_data = fail_res.json()
    assert fail_data["success"] is False
    assert fail_data["status"] == "RETRYING"
    assert fail_data["attempt_count"] == 1

    # Verify failure is logged in Failure Center
    fail_center_res = client.get("/api/failures")
    assert fail_center_res.status_code == 200
    failures = fail_center_res.json()
    q_fail = next((f for f in failures if f.get("audit_reference") == queue_id), None)
    assert q_fail is not None
    assert q_fail["status"] == "OPEN"

    # 3. Recover the message via retry
    rec_res = client.post(f"/api/queue/retry/{queue_id}")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["success"] is True
    assert rec_data["status"] == "PROCESSED"


def test_queue_duplicate_message_idempotency(client):
    """Test that duplicate messages are blocked by idempotency."""
    key = "IDEMP-DUP-MSG-999"
    payload = {
        "topic": "orders.incoming",
        "payload": {
            "order_id": "ORD-DUP-01",
            "supplier_id": "SUP-A",
            "product_id": "PROD-101",
            "quantity": 100,
            "delivery_date": "2026-12-10"
        },
        "idempotency_key": key,
        "source_system": "ERP"
    }

    # First enqueue
    res1 = client.post("/api/queue/enqueue", json=payload)
    assert res1.status_code == 201
    q1 = res1.json()

    # Second enqueue of identical message
    res2 = client.post("/api/queue/enqueue", json=payload)
    assert res2.status_code == 201
    q2 = res2.json()

    # Must return the same queue item, avoiding duplicate record
    assert q2["queue_id"] == q1["queue_id"]

    # Check audit trail recorded DUPLICATE_DETECTED
    audit_res = client.get("/api/audit?action=DUPLICATE_DETECTED")
    assert audit_res.status_code == 200
    audits = audit_res.json()
    assert any(a["entity_id"] == q1["queue_id"] for a in audits)


def test_temporary_supplier_network_failure(client):
    """Test handling of temporary supplier network failure during adapter transmission."""
    # 1. Simulate target supplier offline
    client.post("/api/systems/simulate", json={
        "system_name": "SUP-C",
        "target_status": "OFFLINE"
    })

    payload = {
        "topic": "orders.incoming",
        "payload": {
            "order_id": "ORD-OFFLINE-001",
            "supplier_id": "SUP-C",
            "product_id": "PROD-103",
            "quantity": 135,
            "unit": "EA",
            "delivery_date": "2026-12-15"
        },
        "idempotency_key": "IDEMP-OFFLINE-001",
        "source_system": "ERP"
    }

    enq_res = client.post("/api/queue/enqueue", json=payload)
    assert enq_res.status_code == 201
    queue_id = enq_res.json()["queue_id"]

    # Process message - should fail cleanly because SUP-C is OFFLINE
    proc_res = client.post(f"/api/queue/process/{queue_id}")
    assert proc_res.status_code == 200
    p_data = proc_res.json()
    assert p_data["success"] is False
    assert p_data["status"] == "RETRYING"

    # Restore supplier online
    client.post("/api/systems/recover-all")

    # Retry should now succeed
    retry_res = client.post(f"/api/queue/retry/{queue_id}")
    assert retry_res.status_code == 200
    r_data = retry_res.json()
    assert r_data["success"] is True
    assert r_data["status"] == "PROCESSED"
