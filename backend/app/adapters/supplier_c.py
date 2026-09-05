import datetime
from typing import Dict, Any, Tuple


class SupplierCAdapter:
    """
    Adapter for Supplier C (Gamma Parts).
    Transforms canonical event into Gamma Parts proprietary format:
    - quantity -> QTY
    - product_id -> SKU
    - order_id -> ORDER_NO
    - priority (PRIORITY_HIGH -> True, NORMAL -> False) -> EXPEDITE_FLAG
    - delivery_date -> SCHEDULE_DATE
    - SYSTEM_ORIGIN -> CANONICAL_GATEWAY
    """

    SUPPLIER_CODE = "SUP-C"
    SUPPLIER_NAME = "Gamma Parts"

    def validate(self, canonical_payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates canonical event against Gamma Parts strict validation."""
        if not canonical_payload.get("order_id"):
            return False, "Missing ORDER_NO (order_id) for Gamma Parts"
        if not canonical_payload.get("product_id"):
            return False, "Missing SKU (product_id) for Gamma Parts"
        if int(canonical_payload.get("quantity", 0)) <= 0:
            return False, "QTY must be greater than zero"
        return True, "Valid"

    def transform(self, canonical_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transforms canonical event into Supplier C payload."""
        is_high = canonical_payload.get("priority") == "PRIORITY_HIGH"
        return {
            "ORDER_NO": canonical_payload.get("order_id", "N/A"),
            "SKU": canonical_payload.get("product_id", "N/A"),
            "QTY": int(canonical_payload.get("quantity", 0)),
            "EXPEDITE_FLAG": is_high,
            "SCHEDULE_DATE": canonical_payload.get("delivery_date", datetime.date.today().isoformat()),
            "SYSTEM_ORIGIN": "CANONICAL_GATEWAY",
            "GATEWAY_HEADER": {
                "EVT_ID": canonical_payload.get("event_id"),
                "CORR_ID": canonical_payload.get("correlation_id"),
                "TS": datetime.datetime.utcnow().isoformat() + "Z"
            }
        }

    def send(self, transformed_payload: Dict[str, Any], simulate_delay: bool = False, simulate_failure: bool = False) -> Dict[str, Any]:
        """Simulates transmission to Supplier C endpoint."""
        if simulate_failure:
            raise ConnectionError("Gamma Parts ERP rejected connection: 500 Internal Server Error")
        
        latency = 180 if simulate_delay else 55
        return {
            "GAMMA_ACK": True,
            "DOC_NUM": f"GAMMA-DOC-{transformed_payload['ORDER_NO']}",
            "STATUS": "QUEUED_FOR_PRODUCTION",
            "LATENCY_MS": latency,
            "TIMESTAMP": datetime.datetime.utcnow().isoformat() + "Z"
        }
