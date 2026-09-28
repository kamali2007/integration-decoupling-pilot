import datetime
from typing import Dict, Any, Tuple, Optional, List
from pydantic import ValidationError
from app.schemas import SupplierCInboundOrder, SupplierPayloadC


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

    Also provides explicit schema contract validation for Supplier C messages.
    """

    SUPPLIER_CODE = "SUP-C"
    SUPPLIER_NAME = "Gamma Parts"
    FORMAT_SPEC = "Gamma SAP/RFC Gateway JSON"

    def validate(self, canonical_payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validates canonical event against Gamma Parts strict validation."""
        if not canonical_payload.get("order_id"):
            return False, "Missing ORDER_NO (order_id) for Gamma Parts"
        if not canonical_payload.get("product_id"):
            return False, "Missing SKU (product_id) for Gamma Parts"
        if int(canonical_payload.get("quantity", 0)) <= 0:
            return False, "QTY must be greater than zero"
        return True, "Valid"

    def validate_inbound_message(self, message: Dict[str, Any]) -> Tuple[bool, str, Optional[SupplierCInboundOrder], List[str]]:
        """
        Validates raw supplier input message against explicit Supplier C schema contract.
        Returns (is_valid, summary_message, parsed_model, list_of_error_strings).
        """
        try:
            parsed = SupplierCInboundOrder(**message)
            return True, "Message conforms to Supplier C (Gamma) schema contract", parsed, []
        except ValidationError as err:
            errors = [f"{e['loc'][0]}: {e['msg']}" for e in err.errors()]
            return False, f"Supplier C contract validation failed: {len(errors)} error(s)", None, errors

    def transform_to_canonical(self, inbound: SupplierCInboundOrder) -> Dict[str, Any]:
        """
        Supplier-specific transformation: translates Supplier C payload into canonical representation.
        Supplier-specific logic remains encapsulated within the adapter.
        """
        return {
            "order_id": inbound.ORDER_NO,
            "product_id": inbound.SKU,
            "quantity": inbound.QTY,
            "supplier_id": self.SUPPLIER_CODE,
            "unit": "EA",
            "priority": "PRIORITY_HIGH" if inbound.EXPEDITE_FLAG else "NORMAL",
            "delivery_date": inbound.SCHEDULE_DATE,
            "source_system": "SUPPLIER_C",
            "is_urgent": inbound.EXPEDITE_FLAG
        }

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

    def get_contract_spec(self) -> Dict[str, Any]:
        """Returns the explicit contract specification for API documentation."""
        return {
            "supplier_code": self.SUPPLIER_CODE,
            "supplier_name": self.SUPPLIER_NAME,
            "format_spec": self.FORMAT_SPEC,
            "schema_model": "SupplierCInboundOrder",
            "required_fields": ["ORDER_NO", "SKU", "QTY", "SCHEDULE_DATE"],
            "optional_fields": ["EXPEDITE_FLAG", "SYSTEM_ORIGIN"],
            "field_mapping": {
                "ORDER_NO": "order_id",
                "SKU": "product_id",
                "QTY": "quantity",
                "EXPEDITE_FLAG": "priority (True -> PRIORITY_HIGH)",
                "SCHEDULE_DATE": "delivery_date"
            }
        }

