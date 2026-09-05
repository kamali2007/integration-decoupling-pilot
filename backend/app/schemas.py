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
