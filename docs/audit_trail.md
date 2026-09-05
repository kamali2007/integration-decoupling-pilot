# Enterprise Audit Trail Specification

## 1. Governance & Compliance Rationale
In regulated discrete manufacturing environments, every transaction affecting supplier delivery commitments, expedited freight costs, or purchase order statuses must provide complete forensic auditability. The platform implements an append-only audit trail guaranteeing end-to-end trace reconstruction.

---

## 2. Audit Entry Schema & Fields

| Field | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `audit_id` | `String` | Primary Key | Globally unique identifier (e.g. `AUD-10001`). |
| `timestamp` | `DateTime` | UTC | Exact millisecond timestamp of the audited action. |
| `actor` | `String` | Not Null | User, automated service, or gateway component initiating the action. |
| `action` | `String` | Indexed | Categorized event lifecycle action. |
| `entity_type`| `String` | Indexed | Subject domain entity (`ORDER`, `CANONICAL_EVENT`, `CHANGE_REQUEST`, etc.). |
| `entity_id` | `String` | Indexed | Unique business key of the entity (`ORD-1001`, `CR-001`, etc.). |
| `old_value` | `Text` | Nullable | State representation prior to the transition. |
| `new_value` | `Text` | Nullable | State representation after the transition. |
| `status` | `String` | Enum | Outcome of the action (`SUCCESS`, `WARNING`, `FAILED`). |
| `correlation_id` | `String` | Indexed | Distributed tracing UUID linking related cross-system events. |

---

## 3. Catalog of Audited Actions

1. **`ORDER_CREATED`**: Order ingested from ERP with initial volume and urgency tags.
2. **`EVENT_CREATED`**: Canonical order/forecast event created in gateway.
3. **`EVENT_VALIDATED`**: Canonical event successfully validated against strict Pydantic contract.
4. **`EVENT_TRANSFORMED`**: Canonical event transformed into supplier-specific schema.
5. **`EVENT_SENT`**: Transformed payload successfully transmitted to supplier endpoint.
6. **`EVENT_FAILED`**: Adapter transmission failure or schema rejection.
7. **`EVENT_RETRIED`**: Automated or manual replay of a previously failed delivery.
8. **`DUPLICATE_DETECTED`**: Idempotency key match identified; duplicate ignored.
9. **`CHANGE_CREATED`**: Change request draft submitted for business rule adjustment.
10. **`CHANGE_APPROVED`**: Change request approved by enterprise architect.
11. **`CHANGE_REJECTED`**: Change request rejected with reviewer justification.
12. **`CHANGE_DEPLOYED`**: Change request deployed, activating new rule version.
13. **`ROLLBACK_STARTED`**: Reversal of deployed rule version initiated.
14. **`ROLLBACK_COMPLETED`**: Previous rule version fully restored.

---

## 4. Distributed Tracing via `correlation_id`
Every event retains its originating `correlation_id` from initial ERP creation through canonical transformations, adapter packaging, and delivery receipts. Operators can trace any anomalous supplier delivery back to the exact ERP order submission in seconds via the UI search filter.
