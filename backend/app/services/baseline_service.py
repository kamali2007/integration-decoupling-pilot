from typing import Dict, Any, List


class BaselinePointToPointModel:
    """
    Models the legacy point-to-point architecture.
    Six direct connections exist between source systems and suppliers:
    1. ERP -> Supplier A (Alpha)
    2. ERP -> Supplier B (Beta)
    3. ERP -> Supplier C (Gamma)
    4. Forecast System -> Supplier A (Alpha)
    5. Forecast System -> Supplier B (Beta)
    6. Forecast System -> Supplier C (Gamma)
    """

    BASELINE_INTEGRATIONS = [
        {"id": "P2P-01", "source": "ERP", "target": "Supplier A (Alpha)", "code_location": "erp_alpha_connector.py", "test_suite": "test_erp_alpha.py"},
        {"id": "P2P-02", "source": "ERP", "target": "Supplier B (Beta)", "code_location": "erp_beta_connector.py", "test_suite": "test_erp_beta.py"},
        {"id": "P2P-03", "source": "ERP", "target": "Supplier C (Gamma)", "code_location": "erp_gamma_connector.py", "test_suite": "test_erp_gamma.py"},
        {"id": "P2P-04", "source": "Forecast System", "target": "Supplier A (Alpha)", "code_location": "fcst_alpha_connector.py", "test_suite": "test_fcst_alpha.py"},
        {"id": "P2P-05", "source": "Forecast System", "target": "Supplier B (Beta)", "code_location": "fcst_beta_connector.py", "test_suite": "test_fcst_beta.py"},
        {"id": "P2P-06", "source": "Forecast System", "target": "Supplier C (Gamma)", "code_location": "fcst_gamma_connector.py", "test_suite": "test_fcst_gamma.py"},
    ]

    @classmethod
    def simulate_business_rule_change(cls, new_threshold: int = 200) -> Dict[str, Any]:
        """
        Calculates the exact change impact across the 6 point-to-point connections.
        Each integration script must be individually updated with the new threshold logic.
        """
        affected = []
        for conn in cls.BASELINE_INTEGRATIONS:
            affected.append({
                "connection_id": conn["id"],
                "source": conn["source"],
                "target": conn["target"],
                "file_modified": conn["code_location"],
                "tests_required": 3,
                "change_type": f"Update threshold logic >= {new_threshold} in direct sender",
                "risk": "HIGH - Uncoordinated schema drift / deployment desync"
            })

        return {
            "architecture_type": "POINT_TO_POINT_BASELINE",
            "systems_changed_count": len(cls.BASELINE_INTEGRATIONS),
            "affected_components": affected,
            "total_files_modified": 6,
            "total_tests_required": 18,
            "estimated_dev_hours": 48.0,
            "risk_profile": "HIGH",
            "coordination_overhead": "Requires synchronized release windows across 6 teams/pipelines."
        }


class DecoupledArchitectureModel:
    """
    Models the target Canonical Event Layer architecture.
    Source systems publish to the Canonical Event Layer.
    Business rules are evaluated ONCE in the Canonical Event Service.
    Supplier adapters consume canonical events and format for each supplier.
    """

    @classmethod
    def simulate_business_rule_change(cls, new_threshold: int = 200) -> Dict[str, Any]:
        """
        Calculates the change impact in the decoupled model.
        Only the central Canonical Business Rule component is modified.
        """
        return {
            "architecture_type": "DECOUPLED_CANONICAL_EVENT_LAYER",
            "systems_changed_count": 1,
            "affected_components": [
                {
                    "component_id": "CANONICAL-RULE-ENGINE",
                    "source": "Canonical Event Layer",
                    "target": "All Downstream Adapters",
                    "file_modified": "canonical_event_service.py",
                    "tests_required": 3,
                    "change_type": f"Update canonical business rule threshold to {new_threshold}",
                    "risk": "LOW - Encapsulated within canonical event layer"
                }
            ],
            "total_files_modified": 1,
            "total_tests_required": 3,
            "estimated_dev_hours": 8.0,
            "risk_profile": "LOW",
            "coordination_overhead": "Zero supplier adapter modifications needed. Adapters remain completely agnostic."
        }


def compare_architectures(new_threshold: int = 200) -> Dict[str, Any]:
    """Generates the side-by-side comparison metrics."""
    baseline = BaselinePointToPointModel.simulate_business_rule_change(new_threshold)
    decoupled = DecoupledArchitectureModel.simulate_business_rule_change(new_threshold)

    b_systems = baseline["systems_changed_count"]
    d_systems = decoupled["systems_changed_count"]
    improvement_pct = round(((b_systems - d_systems) / b_systems) * 100.0, 1)

    return {
        "metric": "Number of systems changed for representative business-rule update",
        "baseline_systems_changed": b_systems,
        "decoupled_systems_changed": d_systems,
        "reduction_count": b_systems - d_systems,
        "improvement_pct": improvement_pct,
        "effort_reduction_hours": baseline["estimated_dev_hours"] - decoupled["estimated_dev_hours"],
        "tests_reduction_count": baseline["total_tests_required"] - decoupled["total_tests_required"],
        "baseline_details": baseline,
        "decoupled_details": decoupled
    }
