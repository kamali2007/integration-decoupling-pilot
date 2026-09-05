import datetime
from typing import Dict, Any, Tuple


class SupplierBAdapter:
    """
    Adapter for Supplier B (Beta Manufacturing).
    Transforms canonical event into Beta Manufacturing proprietary format:
    - quantity -> orderedQuantity
    - product_id -> partNumber
    - order_id -> poRef
    - priority (PRIORITY_HIGH -> CRITICAL, NORMAL -> ROUTINE)
    - delivery_date -> requestedDate
    - partnerCode -> MFG-APEX
    """

    SUPPLIER_CODE = "SUP-B"
    SUPPLIER_NAME = "Beta Manufacturing"

    def validate(self, canonical_payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates canonical event against Beta Manufacturing requirements."""
        if not canonical_payload.get("order_id"):
            return False, "Missing required field 'order_id' for Supplier B"
        if not canonical_payload.get("product_id"):
            return False, "Missing required field 'product_id' for Supplier B"
        if int(canonical_payload.get("quantity", 0)) <= 0:
            return False, "orderedQuantity must be greater than zero"
        return True, "Valid"

    def transform(self, canonical_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transforms canonical event into Supplier B payload."""
        is_high = canonical_payload.get("priority") == "PRIORITY_HIGH"
        return {
            "poRef": canonical_payload.get("order_id", "N/A"),
            "partNumber": canonical_payload.get("product_id", "N/A"),
            "orderedQuantity": int(canonical_payload.get("quantity", 0)),
            "urgencyLevel": "CRITICAL" if is_high else "ROUTINE",
            "requestedDate": canonical_payload.get("delivery_date", datetime.date.today().isoformat()),
            "partnerCode": "MFG-APEX",
            "auditMeta": {
                "adapter": "Beta-SOAP/JSON-v2",
                "canonicalRef": canonical_payload.get("event_id"),
                "correlationId": canonical_payload.get("correlation_id")
            }
        }

    def send(self, transformed_payload: Dict[str, Any], simulate_delay: bool = False, simulate_failure: bool = False) -> Dict[str, Any]:
        """Simulates transmission to Supplier B endpoint."""
        if simulate_failure:
            raise ConnectionError("Beta Manufacturing gateway timeout: 504 Gateway Timeout")
        
        latency = 150 if simulate_delay else 42
        return {
            "status": "ACCEPTED",
            "responseCode": "BETA-200",
            "confirmationNumber": f"CONF-BETA-{transformed_payload['poRef']}",
            "latencyMs": latency,
            "processedAt": datetime.datetime.utcnow().isoformat() + "Z"
        }
