import random
import json
import datetime
from pathlib import Path

# Fixed random seed for complete reproducibility
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = DATA_DIR / "message_samples"

SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

SUPPLIERS = [
    {"code": "SUP-A", "name": "Alpha Components Ltd.", "format": "FORMAT_A"},
    {"code": "SUP-B", "name": "Beta Manufacturing Corp", "format": "FORMAT_B"},
    {"code": "SUP-C", "name": "Gamma Parts GmbH", "format": "FORMAT_C"}
]

PRODUCTS = [
    {"id": "PROD-101", "name": "Titanium Spindle Assembly", "unit": "EA", "base_price": 420.0},
    {"id": "PROD-102", "name": "Precision Servo Actuator", "unit": "EA", "base_price": 890.0},
    {"id": "PROD-103", "name": "High-Pressure Hydraulic Valve", "unit": "EA", "base_price": 275.0},
    {"id": "PROD-104", "name": "Carbon Composite Bearing", "unit": "EA", "base_price": 145.0},
    {"id": "PROD-105", "name": "Optical Rotary Encoder", "unit": "EA", "base_price": 310.0},
    {"id": "PROD-106", "name": "High-Torque Stepper Motor", "unit": "EA", "base_price": 540.0},
    {"id": "PROD-107", "name": "Silicon Carbide Seal Kit", "unit": "SET", "base_price": 185.0},
    {"id": "PROD-108", "name": "Micro-Controller PCB Module", "unit": "EA", "base_price": 630.0},
    {"id": "PROD-109", "name": "Pneumatic Pressure Sensor", "unit": "EA", "base_price": 95.0},
    {"id": "PROD-110", "name": "Reinforced Fluoropolymer O-Ring", "unit": "PK", "base_price": 48.0}
]

PERIODS = ["2026-Q3", "2026-Q4", "2027-Q1", "2027-Q2", "2026-M07", "2026-M08", "2026-M09", "2026-M10"]


def generate_orders(count=100):
    orders = []
    base_date = datetime.date(2026, 9, 15)
    for i in range(1, count + 1):
        supplier = random.choice(SUPPLIERS)
        product = random.choice(PRODUCTS)
        qty = random.randint(20, 350)
        is_urgent = random.random() < 0.35
        # Standard business rule threshold is 100
        priority = "PRIORITY_HIGH" if (is_urgent and qty >= 100) else "NORMAL"
        lead_days = random.randint(3, 30)
        delivery_date = (base_date + datetime.timedelta(days=lead_days)).isoformat()

        order = {
            "order_id": f"ORD-{1000 + i}",
            "supplier_id": supplier["code"],
            "supplier_name": supplier["name"],
            "product_id": product["id"],
            "product_name": product["name"],
            "quantity": qty,
            "unit": product["unit"],
            "is_urgent": is_urgent,
            "canonical_priority": priority,
            "delivery_date": delivery_date,
            "source_system": "ERP",
            "correlation_id": f"CORR-ORD-{1000 + i}"
        }
        orders.append(order)
    return orders


def generate_forecasts(count=100):
    forecasts = []
    for i in range(1, count + 1):
        supplier = random.choice(SUPPLIERS)
        product = random.choice(PRODUCTS)
        qty = random.randint(200, 2500)
        period = random.choice(PERIODS)
        confidence = round(random.uniform(0.82, 0.98), 2)

        fcst = {
            "forecast_id": f"FCST-{2000 + i}",
            "supplier_id": supplier["code"],
            "supplier_name": supplier["name"],
            "product_id": product["id"],
            "product_name": product["name"],
            "forecast_quantity": qty,
            "forecast_period": period,
            "confidence_level": confidence,
            "source_system": "FORECAST_SYSTEM",
            "status": "AVAILABLE" if random.random() > 0.1 else "DELAYED",
            "correlation_id": f"CORR-FCST-{2000 + i}"
        }
        forecasts.append(fcst)
    return forecasts


def main():
    print("Generating deterministic sample manufacturing dataset (seed=42)...")
    orders = generate_orders(100)
    forecasts = generate_forecasts(100)

    orders_file = DATA_DIR / "generated_orders.json"
    forecasts_file = DATA_DIR / "generated_forecasts.json"

    with open(orders_file, "w", encoding="utf-8") as f:
        json.dump(orders, f, indent=2)

    with open(forecasts_file, "w", encoding="utf-8") as f:
        json.dump(forecasts, f, indent=2)

    print(f"Generated {len(orders)} orders saved to {orders_file}")
    print(f"Generated {len(forecasts)} forecasts saved to {forecasts_file}")

    # Generate sample adapter outputs for first order
    sample_ord = orders[0]
    sample_a = {
        "orderNumber": sample_ord["order_id"],
        "itemCode": sample_ord["product_id"],
        "qty": sample_ord["quantity"],
        "dispatchPriority": "EXPEDITED" if sample_ord["canonical_priority"] == "PRIORITY_HIGH" else "STANDARD",
        "targetDelivery": sample_ord["delivery_date"]
    }
    sample_b = {
        "poRef": sample_ord["order_id"],
        "partNumber": sample_ord["product_id"],
        "orderedQuantity": sample_ord["quantity"],
        "urgencyLevel": "CRITICAL" if sample_ord["canonical_priority"] == "PRIORITY_HIGH" else "ROUTINE",
        "requestedDate": sample_ord["delivery_date"],
        "partnerCode": "MFG-APEX"
    }
    sample_c = {
        "ORDER_NO": sample_ord["order_id"],
        "SKU": sample_ord["product_id"],
        "QTY": sample_ord["quantity"],
        "EXPEDITE_FLAG": sample_ord["canonical_priority"] == "PRIORITY_HIGH",
        "SCHEDULE_DATE": sample_ord["delivery_date"],
        "SYSTEM_ORIGIN": "CANONICAL_GATEWAY"
    }

    with open(SAMPLES_DIR / "generated_sample_adapter_a.json", "w", encoding="utf-8") as f:
        json.dump(sample_a, f, indent=2)
    with open(SAMPLES_DIR / "generated_sample_adapter_b.json", "w", encoding="utf-8") as f:
        json.dump(sample_b, f, indent=2)
    with open(SAMPLES_DIR / "generated_sample_adapter_c.json", "w", encoding="utf-8") as f:
        json.dump(sample_c, f, indent=2)

    print("Sample supplier-specific message formats saved to message_samples directory.")


if __name__ == "__main__":
    main()
