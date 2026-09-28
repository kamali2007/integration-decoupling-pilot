import datetime
from typing import Dict, Any, Tuple, Optional, List
from pydantic import ValidationError
from app.schemas import SupplierAInboundOrder, SupplierPayloadA


class SupplierAAdapter:
    """
    Adapter for Supplier A (Alpha Components).
    Transforms canonical event into Alpha Components proprietary format:
    - quantity -> qty
    - product_id -> itemCode
    - order_id -> orderNumber
    - priority (PRIORITY_HIGH -> EXPEDITED, NORMAL -> STANDARD)
    - delivery_date -> targetDelivery

    Also provides explicit schema contract validation for Supplier A messages.
    """

    SUPPLIER_CODE = "SUP-A"
    SUPPLIER_NAME = "Alpha Components"
    FORMAT_SPEC = "Alpha REST v1 JSON"

    def validate(self, canonical_payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates canonical order event against Alpha schema prerequisites."""
        required = ["order_id", "product_id", "quantity", "priority"]
        for field in required:
            if field not in canonical_payload or canonical_payload[field] is None:
                return False, f"Missing required canonical field '{field}' for Supplier A"
        if canonical_payload["quantity"] <= 0:
            return False, "Quantity must be greater than zero"
        return True, "Valid"

    def validate_inbound_message(self, message: Dict[str, Any]) -> Tuple[bool, str, Optional[SupplierAInboundOrder], List[str]]:
        """
        Validates raw supplier input message against explicit Supplier A schema contract.
        Returns (is_valid, summary_message, parsed_model, list_of_error_strings).

        Error Boundary Guarantee:
        Catches Pydantic ValidationError and formats it into understandable, actionable
        field-level messages so invalid external payloads are safely rejected before reaching
        the canonical domain logic.
        """
        try:
            parsed = SupplierAInboundOrder(**message)
            return True, "Message conforms to Supplier A (Alpha) schema contract", parsed, []
        except ValidationError as err:
            errors = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
            return False, f"Supplier A contract validation failed: {len(errors)} error(s)", None, errors

    def transform_to_canonical(self, inbound: SupplierAInboundOrder) -> Dict[str, Any]:
        """
        Supplier-specific transformation: translates Supplier A payload into canonical representation.
        Supplier-specific logic remains encapsulated within the adapter.
        """
        is_expedited = inbound.dispatchPriority.upper() == "EXPEDITED"
        return {
            "order_id": inbound.orderNumber,
            "product_id": inbound.itemCode,
            "quantity": inbound.qty,
            "supplier_id": self.SUPPLIER_CODE,
            "unit": "EA",
            "priority": "PRIORITY_HIGH" if is_expedited else "NORMAL",
            "delivery_date": inbound.targetDelivery,
            "source_system": "SUPPLIER_A",
            "is_urgent": is_expedited
        }

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

    def get_contract_spec(self) -> Dict[str, Any]:
        """Returns the explicit contract specification for API documentation."""
        return {
            "supplier_code": self.SUPPLIER_CODE,
            "supplier_name": self.SUPPLIER_NAME,
            "format_spec": self.FORMAT_SPEC,
            "schema_model": "SupplierAInboundOrder",
            "required_fields": ["orderNumber", "itemCode", "qty", "targetDelivery"],
            "optional_fields": ["dispatchPriority", "receivedTimestamp"],
            "field_mapping": {
                "orderNumber": "order_id",
                "itemCode": "product_id",
                "qty": "quantity",
                "dispatchPriority": "priority (EXPEDITED -> PRIORITY_HIGH)",
                "targetDelivery": "delivery_date"
            }
        }

