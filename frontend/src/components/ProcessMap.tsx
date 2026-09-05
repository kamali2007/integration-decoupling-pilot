import React, { useState } from "react";

export const ProcessMap: React.FC = () => {
  const [view, setView] = useState<"target" | "baseline">("target");

  return (
    <div className="panel-card" style={{ background: "#0c1322" }}>
      <div className="panel-header">
        <div>
          <div className="panel-title">
            <span style={{ color: "#3b82f6" }}>⚡</span> Enterprise Architecture Process Map
          </div>
          <div className="panel-subtitle">
            Visualizing the integration blast radius: 6 point-to-point connections vs 1 Canonical Event Layer
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button
            className={`btn btn-sm ${view === "target" ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setView("target")}
          >
            Target Decoupled Layer (1 Component)
          </button>
          <button
            className={`btn btn-sm ${view === "baseline" ? "btn-danger" : "btn-secondary"}`}
            onClick={() => setView("baseline")}
          >
            Baseline Point-to-Point (6 Fragile Links)
          </button>
        </div>
      </div>

      {view === "baseline" ? (
        <div style={{ padding: "20px 10px" }}>
          <div style={{
            background: "rgba(239, 68, 68, 0.08)",
            border: "1px dashed rgba(239, 68, 68, 0.4)",
            borderRadius: "10px",
            padding: "16px",
            marginBottom: "20px",
            fontSize: "13px",
            color: "#fca5a5"
          }}>
            <strong>Baseline Operational Pain:</strong> Every business-rule change (e.g. CR-001 Urgent Threshold) requires modifying <strong>6 separate integration codebases</strong>. If one supplier connection fails, tight coupling risks cascading batch failures.
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", position: "relative" }}>
            {/* Source Systems */}
            <div style={{ display: "flex", flexDirection: "column", gap: "30px", width: "220px" }}>
              <div style={{
                background: "#1e293b",
                border: "2px solid #ef4444",
                borderRadius: "8px",
                padding: "14px",
                boxShadow: "0 4px 10px rgba(0,0,0,0.4)"
              }}>
                <div style={{ fontSize: "11px", color: "#f87171", fontWeight: 700 }}>SOURCE SYSTEM 1</div>
                <div style={{ fontWeight: 700, fontSize: "14px", color: "#fff" }}>SAP S/4HANA ERP</div>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>Order Ingestion Engine</div>
              </div>

              <div style={{
                background: "#1e293b",
                border: "2px solid #ef4444",
                borderRadius: "8px",
                padding: "14px",
                boxShadow: "0 4px 10px rgba(0,0,0,0.4)"
              }}>
                <div style={{ fontSize: "11px", color: "#f87171", fontWeight: 700 }}>SOURCE SYSTEM 2</div>
                <div style={{ fontWeight: 700, fontSize: "14px", color: "#fff" }}>Forecast Planning</div>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>Demand Model Feed</div>
              </div>
            </div>

            {/* Direct P2P Lines Visual */}
            <div style={{ flex: 1, padding: "0 30px", textAlign: "center" }}>
              <div style={{
                background: "rgba(239, 68, 68, 0.15)",
                border: "1px solid #ef4444",
                borderRadius: "8px",
                padding: "16px",
                color: "#fca5a5",
                fontSize: "12px",
                lineHeight: "1.8"
              }}>
                <div style={{ fontWeight: 700, color: "#f87171", fontSize: "13px" }}>Direct Point-to-Point Couplings (6 Modification Points)</div>
                <div>ERP &rarr; Alpha Adapter [erp_alpha_connector.py]</div>
                <div>ERP &rarr; Beta Adapter [erp_beta_connector.py]</div>
                <div>ERP &rarr; Gamma Adapter [erp_gamma_connector.py]</div>
                <div>Forecast &rarr; Alpha Connector [fcst_alpha_connector.py]</div>
                <div>Forecast &rarr; Beta Connector [fcst_beta_connector.py]</div>
                <div>Forecast &rarr; Gamma Connector [fcst_gamma_connector.py]</div>
              </div>
            </div>

            {/* Suppliers */}
            <div style={{ display: "flex", flexDirection: "column", gap: "16px", width: "230px" }}>
              <div style={{ background: "#131c31", border: "1px solid #334155", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>SUPPLIER A</div>
                <div style={{ fontWeight: 700, color: "#fff" }}>Alpha Components</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Format: qty, itemCode</div>
              </div>
              <div style={{ background: "#131c31", border: "1px solid #334155", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>SUPPLIER B</div>
                <div style={{ fontWeight: 700, color: "#fff" }}>Beta Manufacturing</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Format: orderedQuantity</div>
              </div>
              <div style={{ background: "#131c31", border: "1px solid #334155", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>SUPPLIER C</div>
                <div style={{ fontWeight: 700, color: "#fff" }}>Gamma Parts</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Format: QTY, EXPEDITE</div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ padding: "20px 10px" }}>
          <div style={{
            background: "rgba(16, 185, 129, 0.08)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            borderRadius: "10px",
            padding: "16px",
            marginBottom: "20px",
            fontSize: "13px",
            color: "#6ee7b7"
          }}>
            <strong>Target Decoupled Value:</strong> Business rules (priority evaluation, idempotency, audit trail) are evaluated <strong>once in the Canonical Event Layer</strong>. Supplier Adapters remain 100% stable and unchanged. <strong>Blast radius = 1 component (83.3% reduction)</strong>.
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            {/* Sources */}
            <div style={{ display: "flex", flexDirection: "column", gap: "24px", width: "200px" }}>
              <div style={{ background: "#131b2e", border: "1px solid #3b82f6", borderRadius: "8px", padding: "14px" }}>
                <div style={{ fontSize: "11px", color: "#60a5fa", fontWeight: 700 }}>ORDER SOURCE</div>
                <div style={{ fontWeight: 700, fontSize: "14px", color: "#fff" }}>ERP System</div>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>Order Generation</div>
              </div>
              <div style={{ background: "#131b2e", border: "1px solid #3b82f6", borderRadius: "8px", padding: "14px" }}>
                <div style={{ fontSize: "11px", color: "#60a5fa", fontWeight: 700 }}>FORECAST SOURCE</div>
                <div style={{ fontWeight: 700, fontSize: "14px", color: "#fff" }}>Planning System</div>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>Demand Forecasting</div>
              </div>
            </div>

            <div style={{ color: "#3b82f6", fontSize: "24px", fontWeight: 700 }}>&rarr;</div>

            {/* Central Canonical Event Layer */}
            <div style={{
              background: "linear-gradient(135deg, rgba(30, 58, 138, 0.5) 0%, rgba(15, 23, 42, 0.8) 100%)",
              border: "2px solid #3b82f6",
              borderRadius: "12px",
              padding: "20px",
              width: "280px",
              boxShadow: "0 0 25px rgba(59, 130, 246, 0.25)"
            }}>
              <div style={{ fontSize: "11px", color: "#93c5fd", fontWeight: 800, textTransform: "uppercase" }}>
                Single Source of Business Truth
              </div>
              <div style={{ fontWeight: 800, fontSize: "16px", color: "#fff", marginTop: "2px" }}>
                Canonical Event Layer
              </div>
              <div style={{ marginTop: "12px", fontSize: "12px", color: "#cbd5e1", lineHeight: "1.7" }}>
                <div>&bull; <strong>Pydantic Pre-Validation</strong></div>
                <div>&bull; <strong>CR-001 Rule Engine (1 Change)</strong></div>
                <div>&bull; <strong>Idempotency Deduplication</strong></div>
                <div>&bull; <strong>Append-Only Audit Trail</strong></div>
                <div>&bull; <strong>Asynchronous Delay Buffering</strong></div>
              </div>
            </div>

            <div style={{ color: "#10b981", fontSize: "24px", fontWeight: 700 }}>&rarr;</div>

            {/* Supplier Adapters */}
            <div style={{ display: "flex", flexDirection: "column", gap: "14px", width: "240px" }}>
              <div style={{ background: "#131c31", border: "1px solid #10b981", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 700 }}>SUPPLIER ADAPTER A</div>
                <div style={{ fontWeight: 700, color: "#fff" }}>Alpha Components</div>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>validate &rarr; transform &rarr; send</div>
              </div>
              <div style={{ background: "#131c31", border: "1px solid #10b981", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 700 }}>SUPPLIER ADAPTER B</div>
                <div style={{ fontWeight: 700, color: "#fff" }}>Beta Manufacturing</div>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>validate &rarr; transform &rarr; send</div>
              </div>
              <div style={{ background: "#131c31", border: "1px solid #10b981", borderRadius: "8px", padding: "12px" }}>
                <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 700 }}>SUPPLIER ADAPTER C</div>
                <div style={{ fontWeight: 700, color: "#fff" }}>Gamma Parts</div>
                <div style={{ fontSize: "11px", color: "#94a3b8" }}>validate &rarr; transform &rarr; send</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
