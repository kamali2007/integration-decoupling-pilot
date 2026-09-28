import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Order Schemas
class OrderCreate(BaseModel):
    order_id: Optional[str] = None
    supplier_id: str = Field(..., description="Target supplier code e.g. SUP-A, SUP-B, SUP-C")
    product_id: str = Field(..., description="Product SKU e.g. PROD-101")
    quantity: int = Field(..., gt=0, description="Order quantity")
    unit: str = Field(default="EA")
    is_urgent: bool = Field(default=False)
    delivery_date: str = Field(..., description="ISO or YYYY-MM-DD format")
    source_system: str = Field(default="ERP")


class OrderResponse(BaseModel):
    id: str
    order_id: str
    supplier_id: str
    product_id: str
    quantity: int
    unit: str
    is_urgent: bool
    delivery_date: str
    source_system: str
    status: str
    correlation_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Forecast Schemas
class ForecastCreate(BaseModel):
    forecast_id: Optional[str] = None
    supplier_id: str = Field(..., description="Target supplier code")
    product_id: str = Field(..., description="Product SKU")
    forecast_quantity: int = Field(..., gt=0)
    forecast_period: str = Field(..., description="e.g. 2026-Q3 or 2026-M07")
    source_system: str = Field(default="FORECAST_SYSTEM")
    confidence_level: float = Field(default=0.90, ge=0.0, le=1.0)


class ForecastResponse(BaseModel):
    id: str
    forecast_id: str
    supplier_id: str
    product_id: str
    forecast_quantity: int
    forecast_period: str
    source_system: str
    confidence_level: float
    status: str
    correlation_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Canonical Event Schemas
class CanonicalOrderEvent(BaseModel):
    event_id: str
    event_type: str = "ORDER_CREATED"
    event_version: str = "1.0"
    timestamp: str
    source_system: str = "ERP"
    order_id: str
    supplier_id: str
    product_id: str
    quantity: int
    unit: str = "EA"
    priority: str = "NORMAL"
    delivery_date: str
    business_rule_version: str = "BR-1.0"
    correlation_id: str
    idempotency_key: str


class CanonicalForecastEvent(BaseModel):
    event_id: str
    event_type: str = "FORECAST_PUBLISHED"
    event_version: str = "1.0"
    timestamp: str
    source_system: str = "FORECAST_SYSTEM"
    forecast_id: str
    supplier_id: str
    product_id: str
    forecast_quantity: int
    forecast_period: str
    business_rule_version: str = "BR-1.0"
    correlation_id: str
    idempotency_key: str


class CanonicalEventResponse(BaseModel):
    id: str
    event_id: str
    event_type: str
    event_version: str
    source_system: str
    order_id: Optional[str] = None
    forecast_id: Optional[str] = None
    supplier_id: str
    product_id: str
    quantity: int
    unit: str
    priority: str
    delivery_date: Optional[str] = None
    forecast_period: Optional[str] = None
    business_rule_version: str
    correlation_id: str
    idempotency_key: str
    status: str
    raw_payload: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# Supplier Specific Adapter Payloads
class SupplierPayloadA(BaseModel):
    """Supplier A (Alpha Components) proprietary format"""
    orderNumber: str
    itemCode: str
    qty: int
    dispatchPriority: str
    targetDelivery: str
    receivedTimestamp: str


class SupplierPayloadB(BaseModel):
    """Supplier B (Beta Manufacturing) proprietary format"""
    poRef: str
    partNumber: str
    orderedQuantity: int
    urgencyLevel: str
    requestedDate: str
    partnerCode: str = "MFG-APEX"


class SupplierPayloadC(BaseModel):
    """Supplier C (Gamma Parts) proprietary format"""
    ORDER_NO: str
    SKU: str
    QTY: int
    EXPEDITE_FLAG: bool
    SCHEDULE_DATE: str
    SYSTEM_ORIGIN: str = "CANONICAL_GATEWAY"


class AdapterDeliveryResponse(BaseModel):
    id: str
    delivery_id: str
    event_id: str
    supplier_id: str
    adapter_name: str
    transformed_payload: Dict[str, Any]
    delivery_status: str
    attempt_count: int
    last_attempt: datetime.datetime
    error_message: Optional[str] = None
    latency_ms: int
    retry_status: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# System Status & Simulation
class SystemStatusResponse(BaseModel):
    id: str
    system_name: str
    display_name: str
    system_type: str
    status: str
    latency_ms: int
    error_rate: float
    last_heartbeat: datetime.datetime
    details: Optional[str] = None

    class Config:
        from_attributes = True


class SystemSimulationRequest(BaseModel):
    system_name: str
    target_status: str = Field(..., description="ONLINE, DEGRADED, DELAYED, OFFLINE")
    latency_ms: Optional[int] = None
    error_rate: Optional[float] = None
    details: Optional[str] = None


# Failure Case Schemas
class FailureCaseResponse(BaseModel):
    id: str
    failure_id: str
    failure_type: str
    affected_system: str
    severity: str
    cause: str
    impact: str
    detection_method: str
    recovery_action: str
    status: str
    retry_count: int
    audit_reference: Optional[str] = None
    created_at: datetime.datetime
    resolved_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class FailureSimulateRequest(BaseModel):
    failure_type: str = Field(..., description="MISSING_DATA, DELAYED_DATA, SCHEMA_VIOLATION, ENDPOINT_UNAVAILABLE, DUPLICATE_EVENT")
    target_system: Optional[str] = "ERP"


# Change Request & Rollback Schemas
class ChangeRequestCreate(BaseModel):
    title: str
    description: str
    new_threshold: int = 200
    submitted_by: str = "Supply Chain Architect"
    notes: Optional[str] = None


class ChangeRequestResponse(BaseModel):
    id: str
    change_id: str
    title: str
    description: str
    rule_key: str
    current_rule_version: str
    proposed_rule_version: str
    previous_threshold: int
    new_threshold: int
    status: str
    submitted_by: str
    approved_by: Optional[str] = None
    deployed_at: Optional[datetime.datetime] = None
    rolled_back_at: Optional[datetime.datetime] = None
    baseline_systems_changed: int
    decoupled_systems_changed: int
    notes: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class RollbackRequest(BaseModel):
    change_id: str
    initiated_by: str = "Release Manager"
    reason: str


class RollbackResponse(BaseModel):
    id: str
    rollback_id: str
    change_id: str
    from_version: str
    to_version: str
    initiated_by: str
    reason: str
    status: str
    timestamp: datetime.datetime

    class Config:
        from_attributes = True


# Experiment Schemas
class ExperimentRunResponse(BaseModel):
    id: str
    run_id: str
    timestamp: datetime.datetime
    rule_change_name: str
    baseline_systems_changed: int
    decoupled_systems_changed: int
    baseline_effort_hours: float
    decoupled_effort_hours: float
    tests_required_baseline: int
    tests_required_decoupled: int
    risk_score_baseline: str
    risk_score_decoupled: str
    improvement_pct: float
    notes: Optional[str] = None

    class Config:
        from_attributes = True


# Audit Trail Schemas
class AuditEntryResponse(BaseModel):
    id: str
    audit_id: str
    timestamp: datetime.datetime
    actor: str
    action: str
    entity_type: str
    entity_id: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    status: str
    correlation_id: Optional[str] = None

    class Config:
        from_attributes = True


# Stakeholder Validation Schemas
class StakeholderValidationCreate(BaseModel):
    respondent_name: str
    respondent_role: str
    score_flow: int = Field(..., ge=1, le=5)
    score_health: int = Field(..., ge=1, le=5)
    score_recovery: int = Field(..., ge=1, le=5)
    score_change: int = Field(..., ge=1, le=5)
    score_rollback: int = Field(..., ge=1, le=5)
    score_decoupling: int = Field(..., ge=1, le=5)
    comments: Optional[str] = None


class StakeholderValidationResponse(BaseModel):
    id: str
    respondent_name: str
    respondent_role: str
    score_flow: int
    score_health: int
    score_recovery: int
    score_change: int
    score_rollback: int
    score_decoupling: int
    comments: Optional[str] = None
    is_simulated: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# =========================================================
# Asynchronous Message Queue / Buffer Schemas
# =========================================================
class QueuedMessageCreate(BaseModel):
    topic: str = Field(..., description="Message topic e.g. orders.incoming, forecasts.incoming, events.dispatch")
    payload: Dict[str, Any] = Field(..., description="Raw message payload dictionary")
    idempotency_key: Optional[str] = Field(None, description="Optional unique key to prevent duplicate processing")
    source_system: str = Field(default="ERP", description="Originating source system")
    correlation_id: Optional[str] = Field(None, description="End-to-end tracing correlation identifier")


class QueuedMessageResponse(BaseModel):
    id: str
    queue_id: str
    topic: str
    payload: Dict[str, Any]
    idempotency_key: Optional[str] = None
    status: str
    retry_count: int
    max_retries: int
    error_message: Optional[str] = None
    source_system: str
    correlation_id: Optional[str] = None
    created_at: datetime.datetime
    processed_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class QueueProcessResponse(BaseModel):
    success: bool
    queue_id: str
    status: str
    detail: str
    attempt_count: int
    canonical_event_id: Optional[str] = None


class QueueStatsResponse(BaseModel):
    total: int
    queued: int
    processing: int
    processed: int
    retrying: int
    failed: int
    dead_letter: int


# =========================================================
# Supplier Adapter Explicit Schema Contracts
# =========================================================
class SupplierAInboundOrder(BaseModel):
    """Explicit Schema Contract for Supplier A (Alpha Components)."""
    orderNumber: str = Field(..., min_length=1, description="Supplier PO reference (e.g. ORD-1001)")
    itemCode: str = Field(..., min_length=1, description="Alpha part code (e.g. PROD-101)")
    qty: int = Field(..., gt=0, description="Order quantity, must be strictly positive")
    dispatchPriority: str = Field(default="STANDARD", description="EXPEDITED or STANDARD")
    targetDelivery: str = Field(..., description="Target delivery date in ISO format YYYY-MM-DD")
    receivedTimestamp: Optional[str] = Field(None, description="Transmission timestamp ISO string")


class SupplierBInboundOrder(BaseModel):
    """Explicit Schema Contract for Supplier B (Beta Manufacturing)."""
    poRef: str = Field(..., min_length=1, description="Beta PO reference (e.g. ORD-1002)")
    partNumber: str = Field(..., min_length=1, description="Beta component part number (e.g. PROD-102)")
    orderedQuantity: int = Field(..., gt=0, description="Order quantity, must be strictly positive")
    urgencyLevel: str = Field(default="ROUTINE", description="CRITICAL or ROUTINE")
    requestedDate: str = Field(..., description="Requested delivery date in ISO format YYYY-MM-DD")
    partnerCode: str = Field(default="MFG-APEX", description="Partner identification code")


class SupplierCInboundOrder(BaseModel):
    """Explicit Schema Contract for Supplier C (Gamma Parts)."""
    ORDER_NO: str = Field(..., min_length=1, description="Gamma order reference (e.g. ORD-1003)")
    SKU: str = Field(..., min_length=1, description="Gamma SKU code (e.g. PROD-103)")
    QTY: int = Field(..., gt=0, description="Order quantity, must be strictly positive")
    EXPEDITE_FLAG: bool = Field(default=False, description="True for expedited dispatch")
    SCHEDULE_DATE: str = Field(..., description="Scheduled date in ISO format YYYY-MM-DD")
    SYSTEM_ORIGIN: str = Field(default="CANONICAL_GATEWAY", description="Origin system code")


class SupplierValidationRequest(BaseModel):
    supplier_code: str = Field(..., description="SUP-A, SUP-B, or SUP-C")
    payload: Dict[str, Any] = Field(..., description="Supplier message payload to validate against contract")


class SupplierValidationResponse(BaseModel):
    valid: bool
    supplier_code: str
    adapter_name: str
    message: str
    errors: Optional[List[str]] = None
    canonical_preview: Optional[Dict[str, Any]] = None


class SupplierIngestResponse(BaseModel):
    status: str
    supplier_code: str
    canonical_event_id: str
    order_id: str
    business_rule_version: str
    priority: str
    detail: str

