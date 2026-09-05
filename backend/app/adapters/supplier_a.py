import datetime
from typing import Dict, Any, Tuple


class SupplierAAdapter:
    """
    Adapter for Supplier A (Alpha Components).
    Transforms canonical event into Alpha Components proprietary format:
    - quantity -> qty
    - product_id -> itemCode
    - order_id -> orderNumber
    - priority (PRIORITY_HIGH -> EXPEDITED, NORMAL -> STANDARD)
    - delivery_date -> targetDelivery
    """

    SUPPLIER_CODE = "SUP-A"
    SUPPLIER_NAME = "Alpha Components"

    def validate(self, canonical_payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates canonical order event against Alpha schema prerequisites."""
        required = ["order_id", "product_id", "quantity", "priority"]
        for field in required:
            if field not in canonical_payload or canonical_payload[field] is None:
                return False, f"Missing required canonical field '{field}' for Supplier A"
        if canonical_payload["quantity"] <= 0:
            return False, "Quantity must be greater than zero"
        return True, "Valid"

    def transform(self, canonical_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transforms canonical event into Supplier A payload."""
        is_high = canonical_payload.get("priority") == "PRIORITY_HIGH"
        return {
            "orderNumber": canonical_payload.get("order_id", "N/A"),
            "itemCode": canonical_payload.get("product_id", "N/A"),
            "qty": int(canonical_payload.get("quantity", 0)),
            "dispatchPriority": "EXPEDITED" if is_high else "STANDARD",
            "targetDelivery": canonical_payload.get("delivery_date", datetime.date.today().isoformat()),
            "receivedTimestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "sourceAdapter": "Alpha-REST-v1",
                "canonicalEventId": canonical_payload.get("event_id"),
                "correlationId": canonical_payload.get("correlation_id")
            }
        }

    def send(self, transformed_payload: Dict[str, Any], simulate_delay: bool = False, simulate_failure: bool = False) -> Dict[str, Any]:
        """Simulates transmission to Supplier A endpoint."""
        if simulate_failure:
            raise ConnectionError("Alpha Components API returned 503 Service Unavailable")
        
        latency = 120 if simulate_delay else 35
        return {
            "status": "DELIVERED",
            "statusCode": 200,
            "remoteAckId": f"ACK-ALPHA-{transformed_payload['orderNumber']}",
            "latencyMs": latency,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
