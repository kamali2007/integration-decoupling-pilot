# Unit Testing & Error Boundaries Technical Guide

This document provides a granular technical explanation of the automated test suite (26 tests) and the system-wide error boundaries implemented in the **Integration Decoupling Pilot**.

---

## 1. Automated Test Suite Overview

The test suite is built on **pytest** and FastAPI's `TestClient` with an in-memory SQLite `StaticPool` database fixture (`backend/tests/conftest.py`). Every test execution runs in an isolated, transactional environment with database schema creation and sample seeds initialized per session.

**Execution Command**:
```powershell
cd backend
.\.venv\Scripts\pytest -v
```

**Verified Test Result**:
- **Total Tests**: 26
- **Status**: 100% Passed (26 passed in ~5.2s)
- **Regressions**: 0

---

## 2. Granular Unit Test Breakdown by Test File

### 2.1. `test_health.py` (1 Test)
- `test_health_check_endpoint`:
  - **Purpose**: Verifies that the FastAPI gateway is alive and reporting nominal status.
  - **Method/Route**: `GET /api/health`
  - **Expected Behavior**: Returns HTTP 200 with `status="HEALTHY"`, `version="1.0.0"`, and healthy subsystem statuses for Database, Canonical Engine, and Supplier Adapters.

### 2.2. `test_orders.py` (3 Tests)
- `test_create_order_and_canonical_event`:
  - **Purpose**: Verifies end-to-end ERP order ingestion and automatic canonical event promotion.
  - **Scenario**: Order with `quantity=150`, `is_urgent=True` under active rule `BR-1.0` (urgent threshold = 100).
  - **Expected Behavior**: Order created with HTTP 201; canonical event generated with `priority="PRIORITY_HIGH"` because `150 >= 100`.
- `test_create_urgent_order_below_threshold`:
  - **Purpose**: Verifies boundary evaluation when an urgent order's quantity is strictly below the business rule threshold.
  - **Scenario**: Order with `quantity=80`, `is_urgent=True` under `BR-1.0` (threshold = 100).
  - **Expected Behavior**: Order created with HTTP 201; canonical event evaluated with `priority="NORMAL"` because `80 < 100`.
- `test_order_validation_failure`:
  - **Purpose**: Verifies the input schema error boundary on order creation.
  - **Scenario**: Order payload with non-positive quantity (`quantity=-5`).
  - **Expected Behavior**: Pydantic schema validation rejects the request immediately with **HTTP 422 Unprocessable Entity**, preventing corrupt data from entering the database.

### 2.3. `test_forecasts.py` (2 Tests)
- `test_create_forecast`:
  - **Purpose**: Verifies demand forecast creation from the planning system and canonical event publishing.
  - **Expected Behavior**: Returns HTTP 201 with assigned `forecast_id`, `forecast_quantity=750`, and `confidence_level=0.94`.
- `test_forecast_delay_does_not_crash_system`:
  - **Purpose**: Verifies blast-radius containment and non-blocking failure isolation.
  - **Scenario**: `SystemStatus` for "FORECAST" is set to `DELAYED`.
  - **Expected Behavior**: Order creation (`POST /api/orders`) succeeds with HTTP 201 without degradation. Forecast creation (`POST /api/forecasts`) records status as `DELAYED` and buffers into the queue without crashing the system.

### 2.4. `test_events.py` (1 Test)
- `test_idempotency_duplicate_event_handling`:
  - **Purpose**: Verifies canonical event idempotency protection against duplicate network transmissions.
  - **Scenario**: Ingests identical order event twice using the same `idempotency_key="UNIQUE-KEY-001"`.
  - **Expected Behavior**: First call creates canonical event with status `PROCESSED` (`is_new=True`). Second call returns existing record (`is_new=False`), avoids duplicate insertion, and logs an audited `DUPLICATE_DETECTED` warning.

### 2.5. `test_adapters.py` (4 Tests)
- `test_supplier_a_adapter_transformation`:
  - **Purpose**: Tests Supplier A (Alpha Components) proprietary serialization.
  - **Expected Behavior**: Translates canonical format into Alpha REST v1 JSON (`qty=140`, `itemCode="PROD-201"`, `dispatchPriority="EXPEDITED"`).
- `test_supplier_b_adapter_transformation`:
  - **Purpose**: Tests Supplier B (Beta Manufacturing) proprietary serialization.
  - **Expected Behavior**: Translates canonical format into Beta SOAP/EDI JSON (`orderedQuantity=180`, `partNumber="PROD-202"`, `urgencyLevel="CRITICAL"`).
- `test_supplier_c_adapter_transformation`:
  - **Purpose**: Tests Supplier C (Gamma Parts) proprietary serialization.
  - **Expected Behavior**: Translates canonical format into Gamma SAP RFC JSON (`QTY=90`, `SKU="PROD-203"`, `EXPEDITE_FLAG=False`).
- `test_adapter_compare_endpoint`:
  - **Purpose**: Verifies side-by-side adapter transformation comparison.
  - **Route**: `GET /api/adapters/compare-transformations`
  - **Expected Behavior**: Returns the single canonical order event mapped into all 3 supplier formats simultaneously.

### 2.6. `test_failures.py` (2 Tests)
- `test_list_failures`:
  - **Purpose**: Verifies Failure Mode and Effects Analysis (FMEA) catalog.
  - **Expected Behavior**: Populates and returns all 5 baseline failure modes: `MISSING_DATA`, `DELAYED_DATA`, `SCHEMA_VIOLATION`, `ENDPOINT_UNAVAILABLE`, `DUPLICATE_EVENT`.
- `test_simulate_and_retry_failure`:
  - **Purpose**: Verifies dynamic failure simulation and operator retry recovery.
  - **Scenario**: Simulates `ENDPOINT_UNAVAILABLE` on Supplier C (`status="OPEN"`), followed by `POST /api/failures/{id}/retry`.
  - **Expected Behavior**: Failure transitions to `status="RESOLVED"` with `retry_count >= 1` and audit log entry.

### 2.7. `test_experiments.py` (2 Tests)
- `test_decoupling_kpi_calculation`:
  - **Purpose**: Verifies algorithmic blast-radius reduction calculation.
  - **Expected Behavior**: Compares 6 point-to-point connectors against 1 central canonical component, proving exactly **83.3% blast-radius reduction**.
- `test_run_experiment_endpoint`:
  - **Purpose**: Verifies benchmark execution endpoint (`POST /api/experiments/run`).
  - **Expected Behavior**: Persists benchmark run in SQLite `ExperimentRun` table with effort hours and risk metrics.

### 2.8. `test_rollback.py` (1 Test)
- `test_change_approval_deploy_and_rollback_flow`:
  - **Purpose**: Verifies the complete audited Change Request and Rollback governance lifecycle.
  - **Scenario**:
    1. Create Change Request CR-001 (proposing threshold 200).
    2. Submit &rarr; Approve &rarr; Deploy to production (`BR-2.0`, threshold 200).
    3. Verify rule change: urgent order of 150 units now yields `NORMAL` priority (`150 < 200`).
    4. Execute Emergency Rollback (`POST /api/rollback` or `/api/changes/{id}/rollback`).
    5. Verify instant reversion to `BR-1.0` (threshold 100): urgent order of 150 units reverts to `PRIORITY_HIGH` (`150 >= 100`).
    6. Verify complete audit trail entries for deployment and rollback.

### 2.9. `test_queue.py` (5 Tests — Qbee Review 1)
- `test_queued_message_enqueue_and_process`:
  - **Purpose**: Verifies basic queue ingestion and consumer processing flow.
  - **Route**: `POST /api/queue/enqueue` &rarr; `POST /api/queue/process/{id}`
  - **Expected Behavior**: Message enters queue as `QUEUED`, transitions to `PROCESSING` then `PROCESSED`, generating a `CanonicalEvent`.
- `test_delayed_message_buffering_and_drain`:
  - **Purpose**: Verifies resilience buffering during upstream delay.
  - **Scenario**: ERP system status simulated as `DELAYED`. Order creation places message into `orders.buffered` queue topic without crashing.
  - **Expected Behavior**: Calling `POST /api/queue/process-all` drains the buffered messages in FIFO order and marks them `PROCESSED`.
- `test_queue_retry_and_recovery`:
  - **Purpose**: Verifies transient fault handling, retry state machine, and self-healing recovery.
  - **Scenario**: Processes message with `simulate_failure=true`, causing temporary `ConnectionError`.
  - **Expected Behavior**: Message status transitions to `RETRYING` with `attempt_count=1`. An open `FailureCase` is automatically logged in the Failure Center. Calling `POST /api/queue/retry/{id}` completes processing and auto-resolves the failure case.
- `test_queue_duplicate_message_idempotency`:
  - **Purpose**: Verifies queue deduplication.
  - **Scenario**: Submits duplicate message payload with identical `idempotency_key="IDEMP-DUP-MSG-999"`.
  - **Expected Behavior**: Returns existing `queue_id` without creating duplicate record; audit log records `DUPLICATE_DETECTED`.
- `test_temporary_supplier_network_failure`:
  - **Purpose**: Verifies queue resilience when destination supplier is OFFLINE.
  - **Scenario**: Supplier C simulated as `OFFLINE`. Message processing fails into `RETRYING`.
  - **Expected Behavior**: Once Supplier C is recovered, calling retry successfully delivers the payload to Supplier C.

### 2.10. `test_supplier_contracts.py` (5 Tests — Qbee Review 1)
- `test_supplier_contracts_metadata_endpoint`:
  - **Purpose**: Verifies public contract exposure endpoint.
  - **Route**: `GET /api/adapters/contracts`
  - **Expected Behavior**: Exposes explicit schema specifications, required fields, and mapping rules for all 3 suppliers (`SUP-A`, `SUP-B`, `SUP-C`).
- `test_valid_supplier_a_schema_contract`:
  - **Purpose**: Verifies valid Supplier A payload validation and direct ingestion.
  - **Routes**: `POST /api/adapters/validate` and `POST /api/adapters/SUP-A/ingest`
  - **Expected Behavior**: Pre-flight validation confirms `valid=True`; ingestion returns `ACCEPTED` with assigned `canonical_event_id`.
- `test_invalid_supplier_a_schema_contract`:
  - **Purpose**: Verifies adapter error boundary rejection of malformed Supplier A payloads.
  - **Scenario**: Payload with negative quantity (`qty=-10`) and missing required `targetDelivery`.
  - **Expected Behavior**: Ingestion rejects request with **HTTP 422**, returning detailed error descriptions identifying the invalid fields.
- `test_valid_and_invalid_supplier_b_schema_contract`:
  - **Purpose**: Verifies Supplier B contract validation.
  - **Expected Behavior**: Valid Beta payload (`poRef`, `partNumber`, `orderedQuantity`, `requestedDate`) succeeds (HTTP 200); invalid payload (missing `partNumber`, non-positive quantity) is rejected with HTTP 422.
- `test_valid_and_invalid_supplier_c_schema_contract`:
  - **Purpose**: Verifies Supplier C contract validation.
  - **Expected Behavior**: Valid Gamma payload (`ORDER_NO`, `SKU`, `QTY`, `SCHEDULE_DATE`) succeeds (HTTP 200); invalid payload (missing `ORDER_NO`) is rejected with HTTP 422.

---

## 3. Error Boundaries Architecture

The application implements a multi-tier error boundary architecture to isolate faults and prevent system crashes:

```
[ External Wire / HTTP Requests ]
               │
               ▼
┌──────────────────────────────────────────────┐
│ Tier 1: Schema Ingestion Boundary            │
│ - Pydantic v2 Models                         │
│ - HTTP 422 Unprocessable Entity Rejections   │
│ - Actionable field-level validation errors   │
└──────────────────────────────────────────────┘
               │ (Valid payloads only)
               ▼
┌──────────────────────────────────────────────┐
│ Tier 2: Asynchronous Buffer & Shock Absorber │
│ - SQLite message_queue Table                 │
│ - Upstream DELAYED state interception        │
│ - Non-blocking order/forecast execution      │
└──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ Tier 3: Idempotency & Deduplication Boundary │
│ - Unique constraint on idempotency_key       │
│ - Duplicate detection suppresses re-exec     │
│ - Immutable WARNING audit entries logged     │
└──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ Tier 4: Canonical Domain Logic Boundary      │
│ - Centralized Business Rule Engine (CR-001)  │
│ - Blast radius isolated to single component  │
└──────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│ Tier 5: Supplier Adapter Outbound Boundary   │
│ - Adapter validate() prerequisites check     │
│ - Transient ConnectionError trapping         │
│ - Bounded Retry State Machine (max_retries=3)│
│ - Failure Center & Open FailureCase linkage  │
└──────────────────────────────────────────────┘
```

### Key Error Boundary Guarantees
1. **Zero Uncaught Exceptions**: All adapter and queue worker operations are wrapped in structured exception handlers that convert raw exceptions into auditable state transitions (`RETRYING` or `FAILED`).
2. **Failure Center Synchronization**: Any queue processing exception automatically generates or links an open `FailureCase` record in SQLite, giving operators immediate visibility.
3. **Self-Healing Resolution**: When an operator triggers a retry or systems recover, the system automatically resolves associated open failures, updating `resolved_at` timestamps and audit ledgers.
4. **Idempotency Assurance**: Repeated deliveries or network duplicate packets can never create duplicate orders or double-dispatch adapter transmissions.
