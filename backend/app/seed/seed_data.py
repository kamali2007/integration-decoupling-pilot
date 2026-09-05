import datetime
import uuid
from sqlalchemy.orm import Session
from app.models import (
    Manufacturer,
    Supplier,
    Order,
    Forecast,
    SystemStatus,
    ChangeRequest,
    ExperimentRun,
    StakeholderValidation
)
from app.services.canonical_event_service import (
    create_order_canonical_event,
    create_forecast_canonical_event
)
from app.services.adapter_service import dispatch_event_to_adapter
from app.services.failure_service import initialize_default_failures


def seed_database(db: Session):
    """Populates database with rich enterprise seed data."""
    # 1. Manufacturer
    if db.query(Manufacturer).count() == 0:
        mfg = Manufacturer(
            name="Apex Industrial Machinery Corp",
            code="MFG-APEX",
            erp_system_name="SAP S/4HANA Enterprise ERP",
            forecast_system_name="BlueYonder Supply Chain Planning",
            location="Industrial District Plant 01, Sector 4"
        )
        db.add(mfg)

    # 2. Suppliers
    suppliers_data = [
        {"code": "SUP-A", "name": "Alpha Components Ltd.", "endpoint_url": "https://api.alphacomponents.internal/v1/orders", "format_type": "FORMAT_A"},
        {"code": "SUP-B", "name": "Beta Manufacturing Corp", "endpoint_url": "https://edi.betamfg.internal/gateway/po", "format_type": "FORMAT_B"},
        {"code": "SUP-C", "name": "Gamma Parts GmbH", "endpoint_url": "https://rfc.gammaparts.internal/sap/orders", "format_type": "FORMAT_C"}
    ]
    for s_data in suppliers_data:
        if not db.query(Supplier).filter(Supplier.code == s_data["code"]).first():
            db.add(Supplier(**s_data))
    db.commit()

    # 3. System Statuses
    systems = [
        {"system_name": "ERP", "display_name": "SAP S/4HANA ERP (Order Source)", "system_type": "SOURCE", "status": "ONLINE", "latency_ms": 28, "error_rate": 0.01, "details": "Core manufacturing orders pipeline running normally."},
        {"system_name": "FORECAST", "display_name": "Forecast Planning System", "system_type": "SOURCE", "status": "ONLINE", "latency_ms": 45, "error_rate": 0.02, "details": "Weekly demand planning models active."},
        {"system_name": "SUP-A", "display_name": "Supplier A (Alpha Components)", "system_type": "TARGET", "status": "ONLINE", "latency_ms": 35, "error_rate": 0.00, "details": "Alpha Components REST v1 endpoint healthy."},
        {"system_name": "SUP-B", "display_name": "Supplier B (Beta Manufacturing)", "system_type": "TARGET", "status": "ONLINE", "latency_ms": 42, "error_rate": 0.01, "details": "Beta Manufacturing SOAP/JSON gateway connected."},
        {"system_name": "SUP-C", "display_name": "Supplier C (Gamma Parts)", "system_type": "TARGET", "status": "ONLINE", "latency_ms": 55, "error_rate": 0.03, "details": "Gamma Parts RFC gateway responsive."}
    ]
    for sys in systems:
        existing = db.query(SystemStatus).filter(SystemStatus.system_name == sys["system_name"]).first()
        if not existing:
            db.add(SystemStatus(**sys))
    db.commit()

    # 4. Initialize Failure Cases
    initialize_default_failures(db)

    # 5. Change Request CR-001
    if db.query(ChangeRequest).count() == 0:
        cr1 = ChangeRequest(
            change_id="CR-001",
            title="Urgent Order Threshold Realignment",
            description="All urgent orders with quantity >= 100 must be marked as PRIORITY_HIGH before being sent to suppliers. Proposed update raises threshold to 200.",
            rule_key="URGENT_ORDER_THRESHOLD",
            current_rule_version="BR-1.0",
            proposed_rule_version="BR-2.0",
            previous_threshold=100,
            new_threshold=200,
            status="UNDER_REVIEW",
            submitted_by="Senior Supply Chain Architect",
            baseline_systems_changed=6,
            decoupled_systems_changed=1,
            notes="CR-001 represents the core benchmark change evaluated in the decoupling experiment."
        )
        db.add(cr1)
        db.commit()

    # 6. Seed Orders (20 initial realistic orders)
    products = ["PROD-101", "PROD-102", "PROD-103", "PROD-104", "PROD-105"]
    supplier_keys = ["SUP-A", "SUP-B", "SUP-C"]
    
    if db.query(Order).count() == 0:
        today = datetime.date.today()
        for i in range(1, 21):
            supplier_code = supplier_keys[(i - 1) % 3]
            prod_id = products[(i - 1) % len(products)]
            qty = 50 + (i * 15)  # e.g. 65, 80, 95, 110, 125, etc.
            is_urg = (i % 2 == 0)
            delivery_date = (today + datetime.timedelta(days=7 + i)).isoformat()
            
            order = Order(
                order_id=f"ORD-100{i:02d}",
                supplier_id=supplier_code,
                product_id=prod_id,
                quantity=qty,
                unit="EA",
                is_urgent=is_urg,
                delivery_date=delivery_date,
                source_system="ERP",
                status="PROCESSED",
                correlation_id=f"CORR-ORD-{i:03d}"
            )
            db.add(order)
            db.commit()
            db.refresh(order)

            # Generate canonical event and adapter delivery for first 15 orders
            if i <= 15:
                evt, is_new = create_order_canonical_event(db, order)
                if is_new:
                    dispatch_event_to_adapter(db, evt)

    # 7. Seed Forecasts (15 forecasts)
    if db.query(Forecast).count() == 0:
        periods = ["2026-Q3", "2026-Q4", "2026-M07", "2026-M08", "2026-M09"]
        for i in range(1, 16):
            supplier_code = supplier_keys[(i - 1) % 3]
            prod_id = products[(i - 1) % len(products)]
            qty = 500 + (i * 120)
            period = periods[(i - 1) % len(periods)]

            fcst = Forecast(
                forecast_id=f"FCST-200{i:02d}",
                supplier_id=supplier_code,
                product_id=prod_id,
                forecast_quantity=qty,
                forecast_period=period,
                source_system="FORECAST_SYSTEM",
                confidence_level=round(0.85 + (i % 10) * 0.01, 2),
                status="PROCESSED" if i <= 10 else "AVAILABLE",
                correlation_id=f"CORR-FCST-{i:03d}"
            )
            db.add(fcst)
            db.commit()
            db.refresh(fcst)

            if i <= 10:
                create_forecast_canonical_event(db, fcst)

    # 8. Seed Baseline Experiment Run
    if db.query(ExperimentRun).count() == 0:
        exp = ExperimentRun(
            run_id="EXP-1001",
            timestamp=datetime.datetime.utcnow(),
            rule_change_name="CR-001 Urgent Order Threshold (100 -> 200)",
            baseline_systems_changed=6,
            decoupled_systems_changed=1,
            baseline_effort_hours=48.0,
            decoupled_effort_hours=8.0,
            tests_required_baseline=18,
            tests_required_decoupled=3,
            risk_score_baseline="HIGH",
            risk_score_decoupled="LOW",
            improvement_pct=83.3,
            notes="Initial baseline benchmark established during architecture audit."
        )
        db.add(exp)
        db.commit()

    # 9. Seed Stakeholder Validations (Simulated feedback labeled clearly)
    if db.query(StakeholderValidation).count() == 0:
        sample_feedback = [
            {
                "respondent_name": "Elena Rostova",
                "respondent_role": "Director of Supply Chain Architecture",
                "score_flow": 5,
                "score_health": 5,
                "score_recovery": 4,
                "score_change": 5,
                "score_rollback": 5,
                "score_decoupling": 5,
                "comments": "The 83.3% reduction in systems touched is an executive-level proof of value. Decoupling rule logic from supplier transport fixes our biggest operational headache."
            },
            {
                "respondent_name": "Marcus Vance",
                "respondent_role": "Lead Integration Engineer",
                "score_flow": 5,
                "score_health": 4,
                "score_recovery": 5,
                "score_change": 5,
                "score_rollback": 5,
                "score_decoupling": 5,
                "comments": "Having supplier adapters stay completely untouched when we change business thresholds eliminates the regression testing nightmare we faced every quarter."
            }
        ]
        for item in sample_feedback:
            db.add(StakeholderValidation(**item, is_simulated=True))
        db.commit()
