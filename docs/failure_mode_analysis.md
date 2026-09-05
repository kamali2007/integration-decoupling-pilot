# Failure Mode & Effects Analysis (FMEA)

## 1. Overview
The Integration Control Tower includes an automated resilience engine designed to withstand operational anomalies without crashing or corrupting transactional state. Five representative failure modes are actively cataloged, detected, classified, and recovered.

---

## 2. Comprehensive FMEA Table

| Failure ID | Failure Mode | Root Cause | Impact | Detection Method | Recovery Procedure | Severity | Initial Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FAIL-001** | Missing ERP Data | Incomplete ERP extraction payload missing `product_id` or `quantity`. | Order cannot be validated; risk of corrupt data downstream. | Pydantic model validation rejecting schema with HTTP 422. | Transaction rejected with explicit error; logged in audit ledger; ERP prompted for correction. | **HIGH** | RESOLVED |
| **FAIL-002** | Delayed Forecast Data | Batch forecasting ETL delay due to nightly model recalculation. | Upstream forecast stream lagging behind realtime orders. | SLA heartbeat timer exceeding 120s latency threshold. | Non-blocking asynchronous decoupling; orders continue uninterrupted; forecasts queued until feed catches up. | **MEDIUM** | RESOLVED |
| **FAIL-003** | Invalid Supplier Message | Legacy string formatting in quantity violating supplier adapter schema. | Transformation fails for one specific supplier; others unaffected. | Adapter `validate()` returning explicit validation error tuple. | Adapter payload sanitizer coerces numeric typing; operator retries via UI. | **HIGH** | OPEN |
| **FAIL-004** | Endpoint Unavailable | Gamma Parts gateway returns HTTP 503 Service Unavailable. | Order transmission blocked for Supplier C; Alpha & Beta continue. | Connection socket timeout / HTTP 5xx error in adapter `send()`. | Automated exponential backoff retry; held in retry queue; manual trigger available. | **CRITICAL** | OPEN |
| **FAIL-005** | Duplicate Event | ERP network retry transmits identical order with same `order_id`. | Risk of duplicate purchase commitment and duplicate manufacturing. | SQLite unique constraint on `idempotency_key`. | Identified as duplicate; flagged as `DUPLICATE_IGNORED`; warning audit logged; duplicate delivery suppressed. | **LOW** | RESOLVED |

---

## 3. Resilience Scenarios Verification

### Scenario 1: ERP Order Data Available, Forecast Data Delayed
- **Test Case**: `test_forecast_delay_does_not_crash_system` in `test_forecasts.py`
- **Result**: Order pipeline executes at 100% throughput. Forecast records transition to `DELAYED` without locking the process.

### Scenario 2: Forecast Data Available, ERP Order Data Delayed
- **Behavior**: Forecast ingestion and adapter transmission proceed independently. No shared thread lock exists between ERP and forecast routes.

### Scenario 3: Supplier Endpoint Outage
- **Test Case**: `test_simulate_and_retry_failure` in `test_failures.py`
- **Result**: Failed adapter delivery records error message, sets status to `FAILED`, increments `attempt_count`, and enables instant recovery upon operator or scheduled retry.
