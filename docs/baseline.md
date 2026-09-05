# Baseline Point-to-Point Architecture & Pain Points Analysis

## 1. Context & Business Domain
Prior to the decoupling initiative, the manufacturing enterprise managed order replenishment and demand forecasting via dedicated point-to-point connections. As the enterprise expanded to partner with multiple component suppliers (Alpha Components, Beta Manufacturing, Gamma Parts), this architecture exhibited exponential complexity and operational fragility.

---

## 2. Legacy Point-to-Point Inventory

Six distinct integration channels operated in parallel:

1. **ERP &rarr; Supplier A (Alpha Components)**: Direct HTTP REST JSON client formatted to Alpha's proprietary schema (`qty`, `itemCode`).
2. **ERP &rarr; Supplier B (Beta Manufacturing)**: Custom SOAP/XML connector sending purchase orders (`orderedQuantity`, `partNumber`).
3. **ERP &rarr; Supplier C (Gamma Parts)**: SAP RFC socket client interfacing with Gamma's German production gateway (`QTY`, `SKU`).
4. **Forecast &rarr; Supplier A (Alpha Components)**: Nightly batch export script generating custom Alpha forecast records.
5. **Forecast &rarr; Supplier B (Beta Manufacturing)**: EDI 830 Planning Schedule translator.
6. **Forecast &rarr; Supplier C (Gamma Parts)**: Direct database staging table replication.

---

## 3. The Representative Business Rule Change: CR-001
The manufacturer established a critical business rule:
> *"All urgent orders with quantity &ge; 100 must be marked as PRIORITY_HIGH before being sent to suppliers."*

Subsequently, supply chain economics required adjusting this threshold from 100 to 200 units.

### The Point-to-Point Change Explosion
Because no shared domain layer existed, the rule was implemented independently inside each connector:
- `erp_alpha_connector.py` had an `if order.qty >= 100` condition.
- `erp_beta_connector.py` had an `if order.orderedQuantity >= 100` condition.
- `erp_gamma_connector.py` had an `if order.QTY >= 100` condition.
- `fcst_alpha_connector.py` had an independent threshold check.
- `fcst_beta_connector.py` had an independent threshold check.
- `fcst_gamma_connector.py` had an independent threshold check.

### Quantitative Burden
- **Systems / Codebases Changed**: **6 separate integration points**
- **Test Suites Requiring Execution**: **18 test suites** (Unit, Integration, and UAT across all 6 channels)
- **Deployment Windows**: Required 6 coordinated deployment tickets
- **Risk of Desynchronization**: High. If one connector deployment failed or was delayed, orders routed through it adhered to the old rule, creating production discrepancies on the supplier floor.

---

## 4. Operational Pain Summary

| Characteristic | Point-to-Point Baseline | Impact on Operations |
| :--- | :--- | :--- |
| **Coupling Complexity** | $O(N \times M)$ | Connectors scale multiplicatively with new systems. |
| **Rule Consistency** | Fragmented | High probability of logic drift across connectors. |
| **Testing Effort** | $3 \times \text{Integrations}$ | Full regression testing needed on all endpoints. |
| **Error Containment** | Poor | Downstream supplier timeout halts batch upstream. |
| **Observability** | Siloed logs | No centralized audit trail linking orders to deliveries. |
| **Idempotency** | Absent | Duplicate network calls risk duplicate manufacturing. |
