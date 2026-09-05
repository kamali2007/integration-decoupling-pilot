import React, { useState, useEffect } from "react";
import { api, CanonicalEvent } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";
import { Modal } from "../components/Modal";

export const Events: React.FC = () => {
  const [events, setEvents] = useState<CanonicalEvent[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<CanonicalEvent | null>(null);
  const [filterType, setFilterType] = useState<string>("");
  const [filterSupplier, setFilterSupplier] = useState<string>("");
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadEvents = async () => {
    try {
      const data = await api.getEvents(filterSupplier || undefined);
      setEvents(data);
    } catch (err) {
      console.error("Failed to load events:", err);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [filterSupplier]);

  const handleProcessEvents = async () => {
    setProcessing(true);
    try {
      const res = await api.processEvents();
      setMessage(res.message);
      loadEvents();
      setTimeout(() => setMessage(null), 4000);
    } catch (err: any) {
      alert(`Processing error: ${err.message}`);
    } finally {
      setProcessing(false);
    }
  };

  const filtered = events.filter((e) => !filterType || e.event_type === filterType);

  return (
    <div>
      {message && (
        <div style={{
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid #10b981",
          borderRadius: "8px",
          padding: "12px 16px",
          marginBottom: "20px",
          color: "#34d399",
          fontWeight: 600
        }}>
          {message}
        </div>
      )}

      <div className="panel-card">
        <div className="panel-header">
          <div>
            <div className="panel-title">Canonical Event Layer Store</div>
            <div className="panel-subtitle">Normalized business events holding pure domain meaning independent of supplier transport</div>
          </div>
          <button className="btn btn-primary" onClick={handleProcessEvents} disabled={processing}>
            {processing ? "Processing Queue..." : "⚡ Process Pending Events"}
          </button>
        </div>

        {/* Filter bar */}
        <div className="filter-bar">
          <select
            className="form-control search-input"
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
          >
            <option value="">All Event Types</option>
            <option value="ORDER_CREATED">ORDER_CREATED</option>
            <option value="FORECAST_PUBLISHED">FORECAST_PUBLISHED</option>
          </select>

          <select
            className="form-control search-input"
            value={filterSupplier}
            onChange={(e) => setFilterSupplier(e.target.value)}
          >
            <option value="">All Suppliers</option>
            <option value="SUP-A">Supplier A (Alpha)</option>
            <option value="SUP-B">Supplier B (Beta)</option>
            <option value="SUP-C">Supplier C (Gamma)</option>
          </select>

          <span style={{ fontSize: "12px", color: "var(--text-muted)", marginLeft: "auto" }}>
            Showing {filtered.length} canonical events
          </span>
        </div>

        {/* Table */}
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Event ID</th>
                <th>Type</th>
                <th>Source</th>
                <th>Supplier Target</th>
                <th>Product SKU</th>
                <th>Quantity</th>
                <th>Canonical Priority</th>
                <th>Rule Version</th>
                <th>Idempotency Key</th>
                <th>Status</th>
                <th>Inspect</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((e) => (
                <tr key={e.id}>
                  <td style={{ fontWeight: 700, color: "#60a5fa", fontFamily: "var(--font-mono)" }}>
                    {e.event_id}
                  </td>
                  <td>
                    <span style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      color: e.event_type === "ORDER_CREATED" ? "#38bdf8" : "#c084fc"
                    }}>
                      {e.event_type}
                    </span>
                  </td>
                  <td style={{ fontSize: "12px", color: "#94a3b8" }}>{e.source_system}</td>
                  <td>{e.supplier_id}</td>
                  <td style={{ fontFamily: "var(--font-mono)" }}>{e.product_id}</td>
                  <td style={{ fontWeight: 600 }}>{e.quantity} {e.unit}</td>
                  <td>
                    {e.priority === "PRIORITY_HIGH" ? (
                      <span style={{
                        background: "rgba(239, 68, 68, 0.2)",
                        color: "#f87171",
                        border: "1px solid rgba(239, 68, 68, 0.4)",
                        padding: "2px 8px",
                        borderRadius: "4px",
                        fontWeight: 700,
                        fontSize: "11px"
                      }}>
                        PRIORITY_HIGH
                      </span>
                    ) : (
                      <span style={{ color: "#94a3b8", fontSize: "11px" }}>NORMAL</span>
                    )}
                  </td>
                  <td>
                    <span style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "11px",
                      color: e.business_rule_version === "BR-2.0" ? "#34d399" : "#60a5fa"
                    }}>
                      {e.business_rule_version}
                    </span>
                  </td>
                  <td style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono)" }}>
                    {e.idempotency_key}
                  </td>
                  <td><StatusBadge status={e.status} /></td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => setSelectedEvent(e)}>
                      JSON
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Raw JSON Modal */}
      <Modal
        isOpen={Boolean(selectedEvent)}
        title={`Canonical Event Payload: ${selectedEvent?.event_id}`}
        onClose={() => setSelectedEvent(null)}
      >
        {selectedEvent && (
          <div>
            <div style={{ marginBottom: "12px", fontSize: "12.5px", color: "#94a3b8" }}>
              Strictly validated against Pydantic canonical schema before adapter transformation:
            </div>
            <pre className="code-box">
              {JSON.stringify(selectedEvent.raw_payload || selectedEvent, null, 2)}
            </pre>
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
              <button className="btn btn-secondary" onClick={() => setSelectedEvent(null)}>
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
