# Supplier Adapter Contract Specification

## 1. Architectural Role
The Supplier Adapter layer isolates supplier-specific protocol choices, transport handshakes, and property names from the internal canonical event model.

---

## 2. Invariant Conceptual Interface

Every adapter implements the three fundamental lifecycle methods:

```python
class SupplierAdapterInterface:
    def validate(self, canonical_payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Verifies presence and typing of prerequisites before attempting transformation."""
        ...

    def transform(self, canonical_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Translates canonical model into supplier proprietary wire payload."""
        ...

    def send(self, transformed_payload: Dict[str, Any], simulate_delay: bool = False, simulate_failure: bool = False) -> Dict[str, Any]:
        """Transmits payload across wire protocol to supplier endpoint."""
        ...
```

---

## 3. Supplier A Adapter: Alpha Components Ltd.

- **Adapter Class**: `SupplierAAdapter` (`supplier_a.py`)
- **Protocol**: HTTP/1.1 REST JSON (`POST /v1/orders`)
- **Target Schema**:
```json
{
  "orderNumber": "ORD-1001",
  "itemCode": "PROD-101",
  "qty": 150,
  "dispatchPriority": "EXPEDITED",
  "targetDelivery": "2026-09-25",
  "receivedTimestamp": "2026-09-05T08:00:00Z",
  "metadata": {
    "sourceAdapter": "Alpha-REST-v1",
    "canonicalEventId": "EVT-ORD-A10101",
    "correlationId": "CORR-ORD-001"
  }
}
```

---

## 4. Supplier B Adapter: Beta Manufacturing Corp

- **Adapter Class**: `SupplierBAdapter` (`supplier_b.py`)
- **Protocol**: SOAP / EDI-over-HTTPS (`POST /gateway/po`)
- **Target Schema**:
```json
{
  "poRef": "ORD-1002",
  "partNumber": "PROD-102",
  "orderedQuantity": 180,
  "urgencyLevel": "CRITICAL",
  "requestedDate": "2026-09-28",
  "partnerCode": "MFG-APEX",
  "auditMeta": {
    "adapter": "Beta-SOAP/JSON-v2",
    "canonicalRef": "EVT-ORD-B20202",
    "correlationId": "CORR-ORD-002"
  }
}
```

---

## 5. Supplier C Adapter: Gamma Parts GmbH

- **Adapter Class**: `SupplierCAdapter` (`supplier_c.py`)
- **Protocol**: SAP RFC / IDoc JSON Gateway (`POST /sap/orders`)
- **Target Schema**:
```json
{
  "ORDER_NO": "ORD-1003",
  "SKU": "PROD-103",
  "QTY": 90,
  "EXPEDITE_FLAG": false,
  "SCHEDULE_DATE": "2026-10-02",
  "SYSTEM_ORIGIN": "CANONICAL_GATEWAY",
  "GATEWAY_HEADER": {
    "EVT_ID": "EVT-ORD-C30303",
    "CORR_ID": "CORR-ORD-003",
    "TS": "2026-09-05T08:00:00Z"
  }
}
```

---

## 6. Explicit Schema Contracts & Inbound Validation (Qbee Review 1)

Each supplier adapter provides strict, explicit Pydantic schema contracts (`SupplierAInboundOrder`, `SupplierBInboundOrder`, `SupplierCInboundOrder`):

- **Validation Interface**: `validate_inbound_message(message: Dict[str, Any]) -> Tuple[bool, str, Optional[Model], List[str]]`
  - Validates inbound messages against strict field types, positive numeric quantities, and non-empty strings.
  - Returns explicit, understandable validation error lists when contracts are violated.
- **Transformation to Canonical**: `transform_to_canonical(inbound_model) -> Dict[str, Any]`
  - Encapsulates supplier-specific transformation logic inside the adapter.
  - Emits standard canonical order representation for ingestion into the Canonical Event Layer.
- **Contract Metadata Exposure**:
  - `GET /api/adapters/contracts` publishes live contract specifications, required/optional fields, and field mappings.
  - `POST /api/adapters/validate` performs pre-flight contract validation without side effects.
  - `POST /api/adapters/{supplier_code}/ingest` accepts valid messages, rejects invalid messages with HTTP 422, and dispatches through the Canonical Event Layer.

---

## 7. Stability Guarantee
When internal business policies change (e.g. CR-001 raising urgent order threshold to 200), **all 3 adapters remain completely untouched**. The canonical priority is resolved upstream in the Canonical Event Layer, and adapters merely format the resulting boolean/enum representation.

