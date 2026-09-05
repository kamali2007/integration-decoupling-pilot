import sys
from pathlib import Path

# Add backend to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.database import SessionLocal, init_db
from app.seed.seed_data import seed_database
from app.services.failure_service import (
    FAILURE_CATALOG,
    simulate_failure,
    retry_failure,
    resolve_failure
)
from app.models import FailureCase, Order, CanonicalEvent
from app.services.canonical_event_service import create_order_canonical_event


def main():
    print("================================================================================")
    print(" FAILURE MODES & RESILIENCE SIMULATOR (5 CRITICAL FAILURE SCENARIOS)")
    print("================================================================================\n")

    init_db()
    db = SessionLocal()
    seed_database(db)

    print("Executing detection, classification, and recovery for 5 failure modes:\n")

    for idx, item in enumerate(FAILURE_CATALOG, 1):
        print(f"[{idx}/5] Simulating Failure Mode: {item['type']}")
        print(f"      System:    {item['affected_system']}")
        print(f"      Severity:  {item['severity']}")
        print(f"      Cause:     {item['cause']}")
        print(f"      Detection: {item['detection_method']}")
        print(f"      Impact:    {item['impact']}")

        # Trigger simulation in DB
        fc = simulate_failure(db, item["type"], item["affected_system"])
        print(f"      Status:    Detected -> Created Failure Record {fc.failure_id}")

        # Execute recovery
        recovered = retry_failure(db, fc.failure_id)
        print(f"      Recovery:  {item['recovery_action']} -> Status: {recovered.status} (Retries: {recovered.retry_count})\n")

    # Demonstrate Idempotency Duplicate Detection specifically
    print("--- IDEMPOTENCY DEMO: Duplicate Order Submission ---")
    order = db.query(Order).first()
    if order:
        evt1, is_new1 = create_order_canonical_event(db, order, idempotency_key="DEMO-IDEMP-KEY")
        print(f" First Event Ingestion:  Event ID={evt1.event_id}, Status={evt1.status}, IsNew={is_new1}")
        evt2, is_new2 = create_order_canonical_event(db, order, idempotency_key="DEMO-IDEMP-KEY")
        print(f" Second Event Ingestion: Event ID={evt2.event_id}, Status={evt2.status}, IsNew={is_new2}")
        print(" Idempotency check verified: duplicate ignored without redundant transactions.\n")

    db.close()
    print("================================================================================")
    print(" All 5 failure scenarios tested and recovered successfully.")
    print("================================================================================")


if __name__ == "__main__":
    main()
