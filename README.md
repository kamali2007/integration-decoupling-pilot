# Integration Control Tower: Decoupled Manufacturing Gateway

> **Empirical Architecture Prototype**: Manufacturer Exchanging Orders and Forecasts with Multi-Supplier Adapters.  
> **Core Metric**: Demonstrating an **83.3% blast-radius reduction** (from 6 systems down to 1 component) for representative business-rule updates.

---

## 1. Project Overview & Business Problem

A discrete manufacturing enterprise produces high-precision mechanical assemblies and exchanges high-volume Purchase Orders and Demand Forecasts with three major component suppliers:
- **Supplier A (Alpha Components Ltd.)**: Fasteners & Spindle Hardware (REST JSON)
- **Supplier B (Beta Manufacturing Corp)**: Servo Motors & Housings (SOAP / EDI JSON)
- **Supplier C (Gamma Parts GmbH)**: Hydraulic Valves & Precision Seals (SAP RFC Gateway)

### The Operational Pain: Fragile Point-to-Point Baseline
Previously, the manufacturer's core systems (**SAP ERP** and **BlueYonder Forecast Planning**) interfaced directly with each supplier across 6 separate point-to-point connections:
```
ERP  --> Supplier A (Alpha)
ERP  --> Supplier B (Beta)
ERP  --> Supplier C (Gamma)

Forecast  --> Supplier A (Alpha)
Forecast  --> Supplier B (Beta)
Forecast  --> Supplier C (Gamma)
```

**The Change Explosion Problem**:
When a business rule changed—such as **CR-001**: *"All urgent orders with quantity &ge; 100 must be marked as PRIORITY_HIGH before being sent to suppliers"*—the logic had to be independently modified, tested, and released across **all 6 integration codebases**. If one connector failed or lagged in deployment, inconsistent rules were applied across supplier production floors.

---

## 2. Target Decoupled Architecture

The **Integration Control Tower** introduces a **Canonical Event Layer** between internal enterprise systems and external suppliers:

```
Source Systems (ERP, Forecast Planning)
                 |
                 v
       Canonical Event Layer (FastAPI)
  - Pydantic Validation & Normalization
  - Central Business Rule Engine (CR-001)
  - Idempotency & Deduplication Engine
  - Append-Only Audit Trail Ledger
                 |
                 +----> Supplier Adapter A (Alpha Components)
                 +----> Supplier Adapter B (Beta Manufacturing)
                 +----> Supplier Adapter C (Gamma Parts)
                 |
                 v
          Supplier Systems
```

### Core Value Proposition
The business meaning (priority, quantity, delivery window) is owned and evaluated **exclusively inside the Canonical Layer**. Supplier adapters remain strictly responsible for wire-format serialization (`validate`, `transform`, `send`). When the urgent threshold moves from 100 to 200 units, **only 1 central canonical component changes**. Supplier adapters remain 100% stable and untouched.

---

## 3. Technology Stack

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, SQLite (Zero external databases required)
- **Frontend**: React 18, TypeScript 5, Vite 5, Vanilla CSS Enterprise Design System, Lucide Icons
- **Testing**: pytest (16 automated tests covering all lifecycle scenarios), FastAPI TestClient
- **Data Science**: pandas, matplotlib, Jupyter Notebook
- **Portability**: Completely offline-capable, zero paid APIs, zero Docker requirements, Windows/VS Code native.

---

## 4. Empirical Experiment Results (CR-001 Benchmark)

| Dimension / Metric | Baseline (Point-to-Point) | Decoupled (Canonical Gateway) | Quantitative Improvement |
| :--- | :--- | :--- | :--- |
| **Systems / Adapters Changed** | **6 systems** | **1 component** | **83.3% blast-radius reduction** |
| **Integration Files Modified** | 6 connector scripts | 1 rule service file | 83.3% reduction |
| **Regression Tests Required** | 18 test suites | 3 test suites | 83.3% reduction |
| **Engineering Effort (Dev + QA)**| ~48.0 Hours | ~8.0 Hours | **40 Hours Saved (83.3%)** |
| **Risk of Logic Drift** | High (Multi-repo desync) | Zero (Single source of truth)| Eliminated |
| **Rollback Capability** | High-risk multi-release | 1 Instant API call | Zero Downtime |

---

## 5. Quick Start Guide (Windows / VS Code)

### Prerequisites
- Python 3.11+ (Python 3.12 verified)
- Node.js 18+ (Portable Node.js installed in user AppData)

### Option A: One-Click Windows Launchers
1. Start Backend:
   Double-click `start_backend.bat` (or run in terminal: `.\start_backend.bat`)
   - Initializes virtual environment
   - Installs dependencies from `requirements.txt`
   - Initializes SQLite database & seeds 20 realistic orders and 15 forecasts
   - Starts FastAPI on `http://127.0.0.1:8000` (Docs: `http://127.0.0.1:8000/docs`)
2. Start Frontend:
   Double-click `start_frontend.bat` (or run in terminal: `.\start_frontend.bat`)
   - Installs npm dependencies if missing
   - Starts Vite development server on `http://localhost:5173`

---

### Option B: Manual Command Line Instructions

#### 1. Backend Setup & Test Execution
```powershell
# Navigate to backend directory
cd backend

# Create and activate virtual environment (optional)
python -m venv venv
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Run automated test suite (16 tests)
pytest -v

# Start FastAPI Gateway
python run.py
```

#### 2. Frontend Setup & Build
```powershell
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Build production bundle
npm run build

# Start Vite development server
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

## 6. CLI Simulation Scripts & Notebook

### 1. Generate Realistic Sample Data (Seed=42)
Generates 100 realistic orders, 100 forecasts, and supplier message samples:
```powershell
python scripts/generate_data.py
```

### 2. Run Decoupling Experiment Benchmark
Calculates the exact baseline vs decoupled metrics:
```powershell
python scripts/run_experiment.py
```

### 3. Run Failure Mode Simulator
Demonstrates detection, classification, and recovery for all 5 failure modes:
```powershell
python scripts/simulate_failures.py
```

### 4. Interactive Jupyter Notebook
Open `experiments/integration_experiment.ipynb` in VS Code or Jupyter to inspect dataframes, metrics, and the 4 Matplotlib validation charts:
- Chart 1: Systems Changed Comparison
- Chart 2: Failure Recovery MTTR Comparison
- Chart 3: Throughput Success Rate under Delayed Upstream Feeds
- Chart 4: Canonical Event Status Distribution

---

## 7. Interactive Demonstration Flow in the UI

1. **Dashboard (`/`)**:
   - Inspect the high-level KPI banner showing **83.3% blast-radius reduction**.
   - Review live metrics: Total Orders, Forecasts, Processed Events, Open Failures.
   - Toggle the **Process Map** between *Baseline (Point-to-Point)* and *Target (Decoupled Layer)*.
2. **ERP Orders (`/orders`)**:
   - Click **+ Create New Order**.
   - Choose Supplier A, enter Quantity `150`, and check **Urgent Order**.
   - Submit and observe priority automatically resolved as `PRIORITY_HIGH` (under BR-1.0 threshold 100).
3. **Canonical Events (`/events`)**:
   - View the generated canonical event. Click **JSON** to inspect the strict schema and correlation trace.
4. **Adapter Monitor (`/adapters`)**:
   - Inspect the **Side-by-Side Transformation** tab to see how the single canonical event is mapped differently into Alpha (`qty`), Beta (`orderedQuantity`), and Gamma (`QTY`) schemas.
5. **Integration Monitor & Simulator (`/integrations`)**:
   - Click **Simulate ERP Delay** or **Simulate Supplier C Failure**.
   - Notice that the application does not crash. Orders remain buffered in `DELAYED` or `FAILED` state.
   - Click **Recover All Systems** to restore nominal health.
6. **Failure Center (`/failures`)**:
   - View the FMEA table. Click **Retry** on an open failure and verify its recovery to `RESOLVED`.
7. **Change Requests (`/changes`)**:
   - Inspect **CR-001** (raising threshold from 100 to 200).
   - Click **Approve** (Governance Gate) &rarr; Click **Deploy to Prod**.
   - Create a new urgent order with quantity `150`: observe that under `BR-2.0`, priority is now `NORMAL` (150 < 200)!
8. **Rollback Management (`/rollback`)**:
   - Click **Initiate Emergency Rollback** for CR-001.
   - Enter justification: *"Downstream latency regression detected"*.
   - Confirm rollback and observe instant reversion to `BR-1.0` (threshold 100 restored).
9. **Audit Trail (`/audit`)**:
   - Search the chronological ledger for `ROLLBACK_COMPLETED` or trace actions by `correlation_id`.
10. **Stakeholder Review (`/validation`)**:
    - Review the 6-question architectural scorecard labeled *"Prototype Validation &ndash; Sample/Simulated"*.

---

## 8. Complete Documentation Index

- [`docs/architecture.md`](docs/architecture.md): Deep architectural blueprint and sequence diagrams.
- [`docs/field_workflow.md`](docs/field_workflow.md): Complete field-level mapping across ERP, Canonical, and Adapters.
- [`docs/baseline.md`](docs/baseline.md): Detailed analysis of the point-to-point change explosion.
- [`docs/canonical_event_contract.md`](docs/canonical_event_contract.md): Formal JSON schemas and Pydantic models.
- [`docs/adapter_contract.md`](docs/adapter_contract.md): Interface definition (`validate`, `transform`, `send`).
- [`docs/failure_mode_analysis.md`](docs/failure_mode_analysis.md): FMEA table covering 5 failure modes and recovery procedures.
- [`docs/change_management.md`](docs/change_management.md): Formal governance promotion from Draft to Production.
- [`docs/rollback_plan.md`](docs/rollback_plan.md): Anti-silent rollback specification and audit verification.
- [`docs/audit_trail.md`](docs/audit_trail.md): Immutable audit trail schema and tracing.
- [`docs/experiment_results.md`](docs/experiment_results.md): Empirical 83.3% blast-radius reduction results.
- [`docs/user_validation.md`](docs/user_validation.md): Stakeholder review framework and simulated feedback.
- [`docs/technical_documentation.md`](docs/technical_documentation.md): Developer guide, ERD, and REST API catalog.

---

## 9. Limitations & Future Roadmap

1. **Enterprise Message Broker**: Current prototype uses SQLite as an embedded event store; for 100,000+ msg/sec production scale, transition to Apache Kafka or AWS SQS.
2. **Automated Webhook Dispatch**: Integrate outgoing webhooks to notify external alerting tools (PagerDuty, Slack) upon retry exhaustion.
3. **Self-Service Adapter Studio**: Visual drag-and-drop schema mapping interface for supply chain business analysts.
