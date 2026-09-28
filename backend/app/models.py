import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Manufacturer(Base):
    __tablename__ = "manufacturers"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    erp_system_name = Column(String, default="SAP S/4HANA ERP")
    forecast_system_name = Column(String, default="BlueYonder Forecast Planning")
    location = Column(String, default="Industrial District Plant 01")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, nullable=False)  # SUP-A, SUP-B, SUP-C
    name = Column(String, nullable=False)  # Alpha Components, Beta Manufacturing, Gamma Parts
    endpoint_url = Column(String, nullable=False)
    format_type = Column(String, nullable=False)  # FORMAT_A, FORMAT_B, FORMAT_C
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    orders = relationship("Order", back_populates="supplier")
    forecasts = relationship("Forecast", back_populates="supplier")


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, unique=True, nullable=False)  # ORD-1001
    supplier_id = Column(String, ForeignKey("suppliers.code"), nullable=False)
    product_id = Column(String, nullable=False)  # PROD-101
    quantity = Column(Integer, nullable=False)
    unit = Column(String, default="EA")
    is_urgent = Column(Boolean, default=False)
    delivery_date = Column(String, nullable=False)
    source_system = Column(String, default="ERP")
    status = Column(String, default="CREATED")  # CREATED, VALIDATED, PROCESSED, FAILED
    correlation_id = Column(String, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    supplier = relationship("Supplier", back_populates="orders")


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(String, primary_key=True, default=generate_uuid)
    forecast_id = Column(String, unique=True, nullable=False)  # FCST-2001
    supplier_id = Column(String, ForeignKey("suppliers.code"), nullable=False)
    product_id = Column(String, nullable=False)
    forecast_quantity = Column(Integer, nullable=False)
    forecast_period = Column(String, nullable=False)  # 2026-Q2, 2026-M06
    source_system = Column(String, default="FORECAST_SYSTEM")
    confidence_level = Column(Float, default=0.92)
    status = Column(String, default="AVAILABLE")  # AVAILABLE, DELAYED, PROCESSED
    correlation_id = Column(String, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    supplier = relationship("Supplier", back_populates="forecasts")


class CanonicalEvent(Base):
    __tablename__ = "canonical_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    event_id = Column(String, unique=True, nullable=False)  # EVT-10001
    event_type = Column(String, nullable=False)  # ORDER_CREATED, FORECAST_PUBLISHED
    event_version = Column(String, default="1.0")
    source_system = Column(String, nullable=False)  # ERP, FORECAST_SYSTEM
    order_id = Column(String, nullable=True)
    forecast_id = Column(String, nullable=True)
    supplier_id = Column(String, nullable=False)
    product_id = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String, default="EA")
    priority = Column(String, default="NORMAL")  # NORMAL, PRIORITY_HIGH
    delivery_date = Column(String, nullable=True)
    forecast_period = Column(String, nullable=True)
    business_rule_version = Column(String, default="BR-1.0")
    correlation_id = Column(String, nullable=False)
    idempotency_key = Column(String, unique=True, nullable=False)
    status = Column(String, default="PROCESSED")  # PROCESSED, DUPLICATE_IGNORED, PENDING, FAILED, RETRYING
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    deliveries = relationship("AdapterDelivery", back_populates="canonical_event")


class AdapterDelivery(Base):
    __tablename__ = "adapter_deliveries"

    id = Column(String, primary_key=True, default=generate_uuid)
    delivery_id = Column(String, unique=True, default=generate_uuid)
    event_id = Column(String, ForeignKey("canonical_events.event_id"), nullable=False)
    supplier_id = Column(String, nullable=False)  # SUP-A, SUP-B, SUP-C
    adapter_name = Column(String, nullable=False)  # Supplier A Adapter
    transformed_payload = Column(JSON, nullable=False)
    delivery_status = Column(String, default="PROCESSED")  # PENDING, PROCESSED, FAILED, RETRYING
    attempt_count = Column(Integer, default=1)
    last_attempt = Column(DateTime, default=datetime.datetime.utcnow)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, default=45)
    retry_status = Column(String, nullable=True)  # NONE, SCHEDULED, RECOVERED, EXHAUSTED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    canonical_event = relationship("CanonicalEvent", back_populates="deliveries")


class SystemStatus(Base):
    __tablename__ = "system_statuses"

    id = Column(String, primary_key=True, default=generate_uuid)
    system_name = Column(String, unique=True, nullable=False)  # ERP, FORECAST, SUP-A, SUP-B, SUP-C
    display_name = Column(String, nullable=False)
    system_type = Column(String, nullable=False)  # SOURCE, TARGET, MIDDLEWARE
    status = Column(String, default="ONLINE")  # ONLINE, DEGRADED, DELAYED, OFFLINE
    latency_ms = Column(Integer, default=35)
    error_rate = Column(Float, default=0.0)
    last_heartbeat = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(String, nullable=True)


class FailureCase(Base):
    __tablename__ = "failure_cases"

    id = Column(String, primary_key=True, default=generate_uuid)
    failure_id = Column(String, unique=True, nullable=False)  # FAIL-001
    failure_type = Column(String, nullable=False)  # MISSING_DATA, DELAYED_DATA, SCHEMA_VIOLATION, ENDPOINT_UNAVAILABLE, DUPLICATE_EVENT
    affected_system = Column(String, nullable=False)
    severity = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    cause = Column(Text, nullable=False)
    impact = Column(Text, nullable=False)
    detection_method = Column(String, nullable=False)
    recovery_action = Column(String, nullable=False)
    status = Column(String, default="OPEN")  # OPEN, RETRYING, RESOLVED, SUPPRESSED
    retry_count = Column(Integer, default=0)
    audit_reference = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class ChangeRequest(Base):
    __tablename__ = "change_requests"

    id = Column(String, primary_key=True, default=generate_uuid)
    change_id = Column(String, unique=True, nullable=False)  # CR-001
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    rule_key = Column(String, default="URGENT_ORDER_THRESHOLD")
    current_rule_version = Column(String, default="BR-1.0")
    proposed_rule_version = Column(String, default="BR-2.0")
    previous_threshold = Column(Integer, default=100)
    new_threshold = Column(Integer, default=200)
    status = Column(String, default="DRAFT")  # DRAFT, UNDER_REVIEW, APPROVED, REJECTED, DEPLOYED, ROLLED_BACK
    submitted_by = Column(String, default="Supply Chain Architect")
    approved_by = Column(String, nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    rolled_back_at = Column(DateTime, nullable=True)
    baseline_systems_changed = Column(Integer, default=6)
    decoupled_systems_changed = Column(Integer, default=1)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class AuditEntry(Base):
    __tablename__ = "audit_entries"

    id = Column(String, primary_key=True, default=generate_uuid)
    audit_id = Column(String, unique=True, nullable=False)  # AUD-10001
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    actor = Column(String, default="SYSTEM")
    action = Column(String, nullable=False)  # ORDER_CREATED, EVENT_CREATED, EVENT_VALIDATED, EVENT_TRANSFORMED, etc.
    entity_type = Column(String, nullable=False)  # ORDER, FORECAST, CANONICAL_EVENT, CHANGE_REQUEST, SYSTEM
    entity_id = Column(String, nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    status = Column(String, default="SUCCESS")  # SUCCESS, WARNING, FAILED, IGNORED
    correlation_id = Column(String, nullable=True)


class RollbackAction(Base):
    __tablename__ = "rollback_actions"

    id = Column(String, primary_key=True, default=generate_uuid)
    rollback_id = Column(String, unique=True, nullable=False)  # RB-001
    change_id = Column(String, ForeignKey("change_requests.change_id"), nullable=False)
    from_version = Column(String, nullable=False)  # BR-2.0
    to_version = Column(String, nullable=False)  # BR-1.0
    initiated_by = Column(String, default="Release Manager")
    reason = Column(Text, nullable=False)
    status = Column(String, default="COMPLETED")  # PENDING, COMPLETED, FAILED
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(String, primary_key=True, default=generate_uuid)
    run_id = Column(String, unique=True, nullable=False)  # EXP-1001
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    rule_change_name = Column(String, nullable=False)
    baseline_systems_changed = Column(Integer, default=6)
    decoupled_systems_changed = Column(Integer, default=1)
    baseline_effort_hours = Column(Float, default=48.0)
    decoupled_effort_hours = Column(Float, default=8.0)
    tests_required_baseline = Column(Integer, default=18)
    tests_required_decoupled = Column(Integer, default=3)
    risk_score_baseline = Column(String, default="HIGH")
    risk_score_decoupled = Column(String, default="LOW")
    improvement_pct = Column(Float, default=83.3)
    notes = Column(Text, nullable=True)


class StakeholderValidation(Base):
    __tablename__ = "stakeholder_validations"

    id = Column(String, primary_key=True, default=generate_uuid)
    respondent_name = Column(String, default="Enterprise Architect")
    respondent_role = Column(String, default="Supply Chain Architect")
    score_flow = Column(Integer, default=5)          # 1. Is the event flow understandable?
    score_health = Column(Integer, default=5)        # 2. Does the dashboard make integration health clear?
    score_recovery = Column(Integer, default=5)      # 3. Is failure recovery understandable?
    score_change = Column(Integer, default=5)        # 4. Does the change workflow provide enough control?
    score_rollback = Column(Integer, default=5)      # 5. Is rollback clear?
    score_decoupling = Column(Integer, default=5)    # 6. Does the decoupled approach appear easier to change?
    comments = Column(Text, default="Exemplary reduction in integration blast radius.")
    is_simulated = Column(Boolean, default=True)     # "Prototype Validation – Sample/Simulated"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class MessageQueueItem(Base):
    __tablename__ = "message_queue"

    id = Column(String, primary_key=True, default=generate_uuid)
    queue_id = Column(String, unique=True, nullable=False)  # MSG-10001
    topic = Column(String, nullable=False)  # orders.incoming, forecasts.incoming, events.dispatch
    payload = Column(JSON, nullable=False)
    idempotency_key = Column(String, nullable=True, index=True)
    status = Column(String, default="QUEUED")  # QUEUED, PROCESSING, PROCESSED, RETRYING, FAILED, DEAD_LETTER
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    source_system = Column(String, default="ERP")
    correlation_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

