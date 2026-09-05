import React, { useState, useEffect } from "react";
import { api, Forecast } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";
import { Modal } from "../components/Modal";

export const Forecasts: React.FC = () => {
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // Form state
  const [supplierId, setSupplierId] = useState("SUP-A");
  const [productId, setProductId] = useState("PROD-101");
  const [quantity, setQuantity] = useState(850);
  const [period, setPeriod] = useState("2026-Q4");
  const [confidence, setConfidence] = useState(0.92);

  const loadForecasts = async () => {
    try {
      const data = await api.getForecasts();
      setForecasts(data);
    } catch (err) {
      console.error("Failed to load forecasts:", err);
    }
  };

  useEffect(() => {
    loadForecasts();
  }, []);

  const handleCreateForecast = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const fcst = await api.createForecast({
        supplier_id: supplierId,
        product_id: productId,
        forecast_quantity: Number(quantity),
        forecast_period: period,
        confidence_level: Number(confidence),
        source_system: "FORECAST_SYSTEM"
      });
      setNotification(`Forecast ${fcst.forecast_id} created for ${fcst.forecast_period}!`);
      setIsModalOpen(false);
      loadForecasts();
      setTimeout(() => setNotification(null), 5000);
    } catch (err: any) {
      alert(`Error creating forecast: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      {notification && (
        <div style={{
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid #10b981",
          borderRadius: "8px",
          padding: "12px 16px",
          marginBottom: "20px",
          color: "#34d399",
          fontWeight: 600
        }}>
          {notification}
        </div>
      )}

      <div className="panel-card">
        <div className="panel-header">
          <div>
            <div className="panel-title">Demand Forecast Planning Feed</div>
            <div className="panel-subtitle">Multi-period supply chain forecasts ingested and decoupled from order pipelines</div>
          </div>
          <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
            + Create Demand Forecast
          </button>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Forecast ID</th>
                <th>Supplier Allocation</th>
                <th>Product SKU</th>
                <th>Forecast Volume</th>
                <th>Planning Period</th>
                <th>Confidence</th>
                <th>Status</th>
                <th>Correlation Key</th>
                <th>Created At</th>
              </tr>
            </thead>
            <tbody>
              {forecasts.map((f) => (
                <tr key={f.id}>
                  <td style={{ fontWeight: 700, color: "#8b5cf6", fontFamily: "var(--font-mono)" }}>
                    {f.forecast_id}
                  </td>
                  <td>
                    {f.supplier_id === "SUP-A" && "Alpha Components (SUP-A)"}
                    {f.supplier_id === "SUP-B" && "Beta Mfg (SUP-B)"}
                    {f.supplier_id === "SUP-C" && "Gamma Parts (SUP-C)"}
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)" }}>{f.product_id}</td>
                  <td style={{ fontWeight: 600 }}>{f.forecast_quantity.toLocaleString()} EA</td>
                  <td>
                    <span style={{
                      background: "rgba(59, 130, 246, 0.15)",
                      color: "#60a5fa",
                      padding: "3px 8px",
                      borderRadius: "4px",
                      fontWeight: 600,
                      fontSize: "12px"
                    }}>
                      {f.forecast_period}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600, color: f.confidence_level >= 0.9 ? "#34d399" : "#fbbf24" }}>
                    {(f.confidence_level * 100).toFixed(0)}%
                  </td>
                  <td><StatusBadge status={f.status} /></td>
                  <td style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono)" }}>
                    {f.correlation_id}
                  </td>
                  <td style={{ fontSize: "11px", color: "#94a3b8" }}>
                    {new Date(f.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      <Modal isOpen={isModalOpen} title="Create Demand Forecast Feed" onClose={() => setIsModalOpen(false)}>
        <form onSubmit={handleCreateForecast}>
          <div className="form-group">
            <label className="form-label">Target Supplier</label>
            <select className="form-control" value={supplierId} onChange={(e) => setSupplierId(e.target.value)}>
              <option value="SUP-A">Supplier A - Alpha Components Ltd.</option>
              <option value="SUP-B">Supplier B - Beta Manufacturing Corp</option>
              <option value="SUP-C">Supplier C - Gamma Parts GmbH</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Product SKU</label>
            <select className="form-control" value={productId} onChange={(e) => setProductId(e.target.value)}>
              <option value="PROD-101">PROD-101 - Titanium Spindle Assembly</option>
              <option value="PROD-102">PROD-102 - Precision Servo Actuator</option>
              <option value="PROD-103">PROD-103 - High-Pressure Hydraulic Valve</option>
              <option value="PROD-104">PROD-104 - Carbon Composite Bearing</option>
              <option value="PROD-105">PROD-105 - Optical Rotary Encoder</option>
            </select>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div className="form-group">
              <label className="form-label">Projected Quantity (Units)</label>
              <input
                type="number"
                className="form-control"
                min="10"
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Planning Period</label>
              <select className="form-control" value={period} onChange={(e) => setPeriod(e.target.value)}>
                <option value="2026-Q3">2026-Q3 (Quarterly)</option>
                <option value="2026-Q4">2026-Q4 (Quarterly)</option>
                <option value="2027-Q1">2027-Q1 (Quarterly)</option>
                <option value="2026-M09">2026-M09 (Monthly)</option>
                <option value="2026-M10">2026-M10 (Monthly)</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Model Confidence Score (0.0 - 1.0)</label>
            <input
              type="number"
              step="0.01"
              min="0.5"
              max="1.0"
              className="form-control"
              value={confidence}
              onChange={(e) => setConfidence(Number(e.target.value))}
              required
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "16px" }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Publishing..." : "Publish Forecast"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
