# Technical Documentation & Developer Guide

## 1. System Requirements & Technology Stack

- **Backend Runtime**: Python 3.11+ (Validated on Python 3.12.8)
- **Web Framework**: FastAPI (v0.110+)
- **Data Validation**: Pydantic v2
- **Persistence**: SQLAlchemy 2.0 ORM with SQLite (`integration_pilot.db`)
- **Frontend Runtime**: Node.js v18+ (Validated on Node v20.18.0)
- **Frontend Framework**: React 18 with TypeScript 5 and Vite 5
- **Testing**: pytest (v8+) with FastAPI `TestClient`
- **Data Science**: pandas, matplotlib

---

## 2. Project Directory Structure

```
integration-decoupling-pilot/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application assembly & CORS
│   │   ├── database.py                 # SQLAlchemy engine, session & init_db
│   │   ├── models.py                   # Domain models (Order, Event, Failure, Audit)
│   │   ├── schemas.py                  # Pydantic v2 validation contracts
│   │   ├── config.py                   # Pathlib paths, DB URL, rule constants
│   │   │
│   │   ├── api/                        # Modular REST API endpoints
│   │   │   ├── health.py               # GET /api/health
│   │   │   ├── orders.py               # GET, POST /api/orders
│   │   │   ├── forecasts.py            # GET, POST /api/forecasts
│   │   │   ├── events.py               # GET, POST /api/events/process
│   │   │   ├── adapters.py             # GET /api/adapters, retry, compare
│   │   │   ├── experiments.py          # GET, POST /api/experiments/run
│   │   │   ├── failures.py             # GET, POST /api/failures/simulate, retry
│   │   │   ├── changes.py              # GET, POST /api/changes, approve, deploy
│   │   │   ├── audit.py                # GET /api/audit
│   │   │   ├── rollback.py             # GET, POST /api/rollback
│   │   │   ├── systems.py              # GET, POST /api/systems/simulate
│   │   │   └── validation.py           # GET, POST /api/validation
│   │   │
│   │   ├── services/                   # Business logic layer
│   │   │   ├── canonical_event_service.py # Canonical event creation & idempotency
│   │   │   ├── adapter_service.py      # Multi-supplier routing & retries
│   │   │   ├── baseline_service.py     # 6-connector point-to-point simulator
│   │   │   ├── experiment_service.py   # Blast-radius calculation (83.3%)
│   │   │   ├── failure_service.py      # FMEA detection, simulation & recovery
│   │   │   ├── change_service.py       # CR-001 governance promotion
│   │   │   ├── audit_service.py        # Centralized append-only audit logger
│   │   │   └── rollback_service.py     # Audited rule version restoration
│   │   │
│   │   ├── adapters/                   # Supplier-specific adapters
│   │   │   ├── supplier_a.py           # Alpha Components (qty, itemCode)
│   │   │   ├── supplier_b.py           # Beta Manufacturing (orderedQuantity)
│   │   │   └── supplier_c.py           # Gamma Parts (QTY, EXPEDITE_FLAG)
│   │   │
│   │   └── seed/
│   │       └── seed_data.py            # Automated rich enterprise seeder
│   │
│   ├── tests/                          # Automated pytest suite (16 tests)
│   │   ├── conftest.py                 # StaticPool SQLite test fixture
│   │   ├── test_health.py
│   │   ├── test_orders.py
│   │   ├── test_forecasts.py
│   │   ├── test_events.py
│   │   ├── test_adapters.py
│   │   ├── test_failures.py
│   │   ├── test_experiments.py
│   │   └── test_rollback.py
│   │
│   ├── requirements.txt
│   ├── pytest.ini
│   └── run.py                          # Local backend launcher
│
├── frontend/
│   ├── src/
│   │   ├── components/                 # Reusable UI components
│   │   │   ├── MetricCard.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   ├── ProcessMap.tsx
│   │   │   └── Modal.tsx
│   │   ├── pages/                      # 12 Operational views
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Orders.tsx
│   │   │   ├── Forecasts.tsx
│   │   │   ├── Integrations.tsx
│   │   │   ├── Events.tsx
│   │   │   ├── Adapters.tsx
│   │   │   ├── Failures.tsx
│   │   │   ├── Experiments.tsx
│   │   │   ├── Changes.tsx
│   │   │   ├── Rollback.tsx
│   │   │   ├── AuditTrail.tsx
│   │   │   └── Validation.tsx
│   │   ├── services/
│   │   │   └── api.ts                  # Type-safe fetch API client
│   │   ├── App.tsx                     # Top-level shell and navigation
│   │   ├── main.tsx
│   │   └── styles.css                  # Enterprise Design System CSS
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts                  # Proxy to http://127.0.0.1:8000
│
├── data/
│   ├── generated_orders.json           # 100 realistic orders (seed=42)
│   ├── generated_forecasts.json        # 100 realistic forecasts (seed=42)
│   ├── message_samples/                # Supplier message JSON samples
│   ├── process_maps/                   # Baseline vs Decoupled JSON map
│   └── change_requests/                # CR-001 JSON specification
│
├── scripts/
│   ├── generate_data.py                # Deterministic data generator
│   ├── run_experiment.py               # Decoupling experiment CLI runner
│   ├── simulate_failures.py            # 5 failure modes CLI simulator
│   └── create_notebook.py              # Jupyter notebook generator
│
├── experiments/
│   └── integration_experiment.ipynb    # Pandas & Matplotlib analysis notebook
│
├── docs/                               # Complete project documentation suite
├── README.md                           # Master guide & VS Code instructions
├── start_backend.bat                   # Windows one-click backend runner
└── start_frontend.bat                  # Windows one-click frontend runner
```

---

## 3. Database Entity-Relationship Architecture

The platform uses 11 relational tables managed via SQLAlchemy ORM:
1. `manufacturers`: Corporate manufacturing entity metadata.
2. `suppliers`: Suppliers A, B, C registry, endpoint URLs, format specifications.
3. `orders`: Orders ingested from ERP (`order_id`, `quantity`, `is_urgent`, `delivery_date`).
4. `forecasts`: Planning forecasts (`forecast_id`, `quantity`, `period`, `confidence`).
5. `canonical_events`: Invariant canonical store (`event_id`, `priority`, `business_rule_version`, `idempotency_key`).
6. `adapter_deliveries`: Transformed supplier transmissions (`transformed_payload`, `latency_ms`, `delivery_status`).
7. `system_statuses`: Real-time endpoint health (`ONLINE`, `DEGRADED`, `DELAYED`, `OFFLINE`).
8. `failure_cases`: FMEA records with root causes and retry counts.
9. `change_requests`: CR-001 governance lifecycle states.
10. `rollback_actions`: Version restoration records.
11. `audit_entries`: Append-only audit trail.

---

## 4. REST API Endpoint Catalog

| Method | Path | Summary | Query / Body Params |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status | None |
| `GET` | `/api/orders` | List manufacturing orders | `supplier_id`, `limit` |
| `POST` | `/api/orders` | Ingest order from ERP | `OrderCreate` JSON |
| `GET` | `/api/forecasts` | List demand forecasts | `supplier_id`, `limit` |
| `POST` | `/api/forecasts` | Ingest demand forecast | `ForecastCreate` JSON |
| `GET` | `/api/events` | List canonical events | `supplier_id`, `status` |
| `POST` | `/api/events/process` | Batch-process pending events | None |
| `GET` | `/api/adapters` | List adapter deliveries | `supplier_id`, `status` |
| `GET` | `/api/adapters/compare-transformations` | Side-by-side format comparison | `event_id` |
| `POST` | `/api/adapters/retry/{id}` | Re-transmit failed delivery | `delivery_id` |
| `GET` | `/api/systems` | Integration monitor health | None |
| `POST` | `/api/systems/simulate` | Mutate system state (delay/fail) | `SystemSimulationRequest` |
| `POST` | `/api/systems/recover-all` | Recover all systems to ONLINE | None |
| `GET` | `/api/failures` | List failure cases | `status`, `severity` |
| `POST` | `/api/failures/simulate` | Inject one of 5 failure modes | `failure_type`, `target_system` |
| `POST` | `/api/failures/{id}/retry` | Recover failure case | `failure_id` |
| `GET` | `/api/experiments` | List experiment runs | None |
| `GET` | `/api/experiments/metrics` | Live KPI calculation | `threshold` |
| `POST` | `/api/experiments/run` | Execute decoupling experiment | `threshold` |
| `GET` | `/api/changes` | List change requests | None |
| `POST` | `/api/changes` | Draft new change request | `ChangeRequestCreate` |
| `POST` | `/api/changes/{id}/approve` | Approve change request | `approver` |
| `POST` | `/api/changes/{id}/deploy` | Deploy approved change | `deployer` |
| `POST` | `/api/changes/{id}/rollback`| Revert deployed change | `reason`, `initiated_by` |
| `GET` | `/api/audit` | Query immutable audit trail | `action`, `search`, `limit` |
| `GET` | `/api/validation/summary` | Stakeholder review summary | None |
| `POST` | `/api/validation` | Submit stakeholder review | `StakeholderValidationCreate` |
