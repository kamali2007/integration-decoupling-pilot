import datetime
from typing import Dict, Any, Tuple, Optional, List
from pydantic import ValidationError
from app.schemas import SupplierBInboundOrder, SupplierPayloadB


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

    Also provides explicit schema contract validation for Supplier B messages.
    """

    SUPPLIER_CODE = "SUP-B"
    SUPPLIER_NAME = "Beta Manufacturing"
    FORMAT_SPEC = "Beta SOAP/JSON EDI v2"

    def validate(self, canonical_payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates canonical event against Beta Manufacturing requirements."""
        if not canonical_payload.get("order_id"):
            return False, "Missing required field 'order_id' for Supplier B"
        if not canonical_payload.get("product_id"):
            return False, "Missing required field 'product_id' for Supplier B"
        if int(canonical_payload.get("quantity", 0)) <= 0:
            return False, "orderedQuantity must be greater than zero"
        return True, "Valid"

    def validate_inbound_message(self, message: Dict[str, Any]) -> Tuple[bool, str, Optional[SupplierBInboundOrder], List[str]]:
        """
        Validates raw supplier input message against explicit Supplier B schema contract.
        Returns (is_valid, summary_message, parsed_model, list_of_error_strings).
        """
        try:
            parsed = SupplierBInboundOrder(**message)
            return True, "Message conforms to Supplier B (Beta) schema contract", parsed, []
        except ValidationError as err:
            errors = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
            return False, f"Supplier B contract validation failed: {len(errors)} error(s)", None, errors

    def transform_to_canonical(self, inbound: SupplierBInboundOrder) -> Dict[str, Any]:
        """
        Supplier-specific transformation: translates Supplier B payload into canonical representation.
        Supplier-specific logic remains encapsulated within the adapter.
        """
        is_critical = inbound.urgencyLevel.upper() == "CRITICAL"
        return {
            "order_id": inbound.poRef,
            "product_id": inbound.partNumber,
            "quantity": inbound.orderedQuantity,
            "supplier_id": self.SUPPLIER_CODE,
            "unit": "EA",
            "priority": "PRIORITY_HIGH" if is_critical else "NORMAL",
            "delivery_date": inbound.requestedDate,
            "source_system": "SUPPLIER_B",
            "is_urgent": is_critical
        }

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

    def get_contract_spec(self) -> Dict[str, Any]:
        """Returns the explicit contract specification for API documentation."""
        return {
            "supplier_code": self.SUPPLIER_CODE,
            "supplier_name": self.SUPPLIER_NAME,
            "format_spec": self.FORMAT_SPEC,
            "schema_model": "SupplierBInboundOrder",
            "required_fields": ["poRef", "partNumber", "orderedQuantity", "requestedDate"],
            "optional_fields": ["urgencyLevel", "partnerCode"],
            "field_mapping": {
                "poRef": "order_id",
                "partNumber": "product_id",
                "orderedQuantity": "quantity",
                "urgencyLevel": "priority (CRITICAL -> PRIORITY_HIGH)",
                "requestedDate": "delivery_date"
            }
        }

