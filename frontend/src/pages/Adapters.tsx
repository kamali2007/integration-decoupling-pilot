import React, { useState, useEffect } from "react";
import { api, AdapterDelivery } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";
import { Modal } from "../components/Modal";

export const Adapters: React.FC = () => {
  const [deliveries, setDeliveries] = useState<AdapterDelivery[]>([]);
  const [comparisons, setComparisons] = useState<any>(null);
  const [selectedPayload, setSelectedPayload] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"comparison" | "history">("comparison");
  const [retryingId, setRetryingId] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [delivs, comp] = await Promise.all([
        api.getAdapterDeliveries(),
        api.getAdapterTransformations()
      ]);
      setDeliveries(delivs);
      setComparisons(comp);
    } catch (err) {
      console.error("Failed to load adapter data:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRetry = async (deliveryId: string) => {
    setRetryingId(deliveryId);
    try {
      await api.retryDelivery(deliveryId);
      loadData();
    } catch (err: any) {
      alert(`Retry error: ${err.message}`);
    } finally {
      setRetryingId(null);
    }
  };

  return (
    <div>
      <div className="panel-card">
        <div className="panel-header">
          <div>
            <div className="panel-title">Supplier Adapter Transformation Monitor</div>
            <div className="panel-subtitle">
              Demonstrating how the Canonical Event remains invariant while adapters translate schemas for each supplier
            </div>
          </div>
          <div style={{ display: "flex", gap: "8px" }}>
            <button
              className={`btn btn-sm ${activeTab === "comparison" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveTab("comparison")}
            >
              Side-by-Side Transformation
            </button>
            <button
              className={`btn btn-sm ${activeTab === "history" ? "btn-primary" : "btn-secondary"}`}
              onClick={() => setActiveTab("history")}
            >
              Delivery Transmission Log ({deliveries.length})
            </button>
          </div>
        </div>

        {activeTab === "comparison" && comparisons && (
          <div>
            {/* Source Canonical Event Box */}
            <div style={{
              background: "rgba(59, 130, 246, 0.08)",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              borderRadius: "10px",
              padding: "16px",
              marginBottom: "24px"
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                <span style={{ fontSize: "12px", color: "#60a5fa", fontWeight: 700, textTransform: "uppercase" }}>
                  INCOMING CANONICAL ORDER EVENT (Unmodified Source of Truth)
                </span>
                <span style={{ fontSize: "11px", color: "#94a3b8", fontFamily: "var(--font-mono)" }}>
                  Event: {comparisons.canonical_event.event_id || "EVT-10001"}
                </span>
              </div>
              <pre className="code-box" style={{ background: "#0b1329" }}>
                {JSON.stringify(comparisons.canonical_event, null, 2)}
              </pre>
            </div>

            {/* 3 Supplier Transformations Side-by-Side */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "18px" }}>
              {/* Supplier A */}
              <div style={{
                background: "#0d1424",
                border: "1px solid var(--border-subtle)",
                borderRadius: "10px",
                padding: "16px"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <div style={{ fontWeight: 700, color: "#fff", fontSize: "13.5px" }}>Alpha Components (SUP-A)</div>
                  <span style={{ fontSize: "10px", background: "rgba(16, 185, 129, 0.15)", color: "#34d399", padding: "2px 6px", borderRadius: "4px" }}>
                    REST JSON
                  </span>
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "10px" }}>
                  Mapping: <code style={{ color: "#60a5fa" }}>quantity &rarr; qty</code>, <code style={{ color: "#60a5fa" }}>priority &rarr; dispatchPriority</code>
                </div>
                <pre className="code-box" style={{ maxHeight: "280px" }}>
                  {JSON.stringify(comparisons.transformations.supplier_a.payload, null, 2)}
                </pre>
              </div>

              {/* Supplier B */}
              <div style={{
                background: "#0d1424",
                border: "1px solid var(--border-subtle)",
                borderRadius: "10px",
                padding: "16px"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <div style={{ fontWeight: 700, color: "#fff", fontSize: "13.5px" }}>Beta Manufacturing (SUP-B)</div>
                  <span style={{ fontSize: "10px", background: "rgba(59, 130, 246, 0.15)", color: "#60a5fa", padding: "2px 6px", borderRadius: "4px" }}>
                    SOAP / EDI
                  </span>
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "10px" }}>
                  Mapping: <code style={{ color: "#60a5fa" }}>quantity &rarr; orderedQuantity</code>, <code style={{ color: "#60a5fa" }}>priority &rarr; urgencyLevel</code>
                </div>
                <pre className="code-box" style={{ maxHeight: "280px" }}>
                  {JSON.stringify(comparisons.transformations.supplier_b.payload, null, 2)}
                </pre>
              </div>

              {/* Supplier C */}
              <div style={{
                background: "#0d1424",
                border: "1px solid var(--border-subtle)",
                borderRadius: "10px",
                padding: "16px"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <div style={{ fontWeight: 700, color: "#fff", fontSize: "13.5px" }}>Gamma Parts (SUP-C)</div>
                  <span style={{ fontSize: "10px", background: "rgba(245, 158, 11, 0.15)", color: "#fbbf24", padding: "2px 6px", borderRadius: "4px" }}>
                    SAP RFC
                  </span>
                </div>
                <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "10px" }}>
                  Mapping: <code style={{ color: "#60a5fa" }}>quantity &rarr; QTY</code>, <code style={{ color: "#60a5fa" }}>priority &rarr; EXPEDITE_FLAG</code>
                </div>
                <pre className="code-box" style={{ maxHeight: "280px" }}>
                  {JSON.stringify(comparisons.transformations.supplier_c.payload, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        )}

        {activeTab === "history" && (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Delivery ID</th>
                  <th>Event ID</th>
                  <th>Supplier Adapter</th>
                  <th>Delivery Status</th>
                  <th>Attempts</th>
                  <th>Latency</th>
                  <th>Error / Telemetry</th>
                  <th>Payload</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {deliveries.map((d) => (
                  <tr key={d.id}>
                    <td style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "#60a5fa" }}>
                      {d.delivery_id}
                    </td>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: "12px" }}>{d.event_id}</td>
                    <td>{d.adapter_name}</td>
                    <td><StatusBadge status={d.delivery_status} /></td>
                    <td style={{ fontWeight: 600 }}>{d.attempt_count}</td>
                    <td>{d.latency_ms} ms</td>
                    <td style={{ fontSize: "11.5px", color: d.error_message ? "#f87171" : "#64748b" }}>
                      {d.error_message || "Acknowledged 200 OK"}
                    </td>
                    <td>
                      <button className="btn btn-secondary btn-sm" onClick={() => setSelectedPayload(d.transformed_payload)}>
                        View
                      </button>
                    </td>
                    <td>
                      {d.delivery_status === "FAILED" ? (
                        <button
                          className="btn btn-warning btn-sm"
                          disabled={retryingId === d.delivery_id}
                          onClick={() => handleRetry(d.delivery_id)}
                        >
                          {retryingId === d.delivery_id ? "Retrying..." : "Retry"}
                        </button>
                      ) : (
                        <span style={{ color: "#34d399", fontSize: "11px" }}>Delivered</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal for viewing transformed payload */}
      <Modal
        isOpen={Boolean(selectedPayload)}
        title="Transformed Supplier Payload"
        onClose={() => setSelectedPayload(null)}
      >
        {selectedPayload && (
          <div>
            <pre className="code-box">{JSON.stringify(selectedPayload, null, 2)}</pre>
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
              <button className="btn btn-secondary" onClick={() => setSelectedPayload(null)}>
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
