import React, { useState, useEffect } from "react";
import { api, Order } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";
import { Modal } from "../components/Modal";

export const Orders: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filterSupplier, setFilterSupplier] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  // Form fields
  const [supplierId, setSupplierId] = useState("SUP-A");
  const [productId, setProductId] = useState("PROD-101");
  const [quantity, setQuantity] = useState(120);
  const [isUrgent, setIsUrgent] = useState(true);
  const [deliveryDate, setDeliveryDate] = useState("2026-10-15");

  const loadOrders = async () => {
    try {
      const data = await api.getOrders(filterSupplier || undefined);
      setOrders(data);
    } catch (err) {
      console.error("Failed to load orders:", err);
    }
  };

  useEffect(() => {
    loadOrders();
  }, [filterSupplier]);

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const newOrder = await api.createOrder({
        supplier_id: supplierId,
        product_id: productId,
        quantity: Number(quantity),
        is_urgent: isUrgent,
        delivery_date: deliveryDate,
        source_system: "ERP"
      });
      setNotification(`Order ${newOrder.order_id} created & ingested into Canonical Event Layer!`);
      setIsModalOpen(false);
      loadOrders();
      setTimeout(() => setNotification(null), 5000);
    } catch (err: any) {
      alert(`Error creating order: ${err.message}`);
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
            <div className="panel-title">ERP Orders Ingestion Management</div>
            <div className="panel-subtitle">Orders originating from SAP ERP, canonicalized and dispatched to supplier adapters</div>
          </div>
          <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
            + Create New Order
          </button>
        </div>

        {/* Filter bar */}
        <div className="filter-bar">
          <select
            className="form-control search-input"
            value={filterSupplier}
            onChange={(e) => setFilterSupplier(e.target.value)}
          >
            <option value="">All Suppliers</option>
            <option value="SUP-A">Supplier A (Alpha Components)</option>
            <option value="SUP-B">Supplier B (Beta Manufacturing)</option>
            <option value="SUP-C">Supplier C (Gamma Parts)</option>
          </select>
          <span style={{ fontSize: "12px", color: "var(--text-muted)", marginLeft: "auto" }}>
            Showing {orders.length} total orders
          </span>
        </div>

        {/* Table */}
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Target Supplier</th>
                <th>Product SKU</th>
                <th>Quantity</th>
                <th>Urgency</th>
                <th>Delivery Date</th>
                <th>Status</th>
                <th>Correlation ID</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id}>
                  <td style={{ fontWeight: 700, color: "#60a5fa", fontFamily: "var(--font-mono)" }}>
                    {o.order_id}
                  </td>
                  <td>
                    {o.supplier_id === "SUP-A" && "Alpha Components (SUP-A)"}
                    {o.supplier_id === "SUP-B" && "Beta Mfg (SUP-B)"}
                    {o.supplier_id === "SUP-C" && "Gamma Parts (SUP-C)"}
                  </td>
                  <td style={{ fontFamily: "var(--font-mono)" }}>{o.product_id}</td>
                  <td style={{ fontWeight: 600 }}>{o.quantity} {o.unit}</td>
                  <td>
                    {o.is_urgent ? (
                      <span style={{ color: "#ef4444", fontWeight: 700, fontSize: "11px" }}>URGENT</span>
                    ) : (
                      <span style={{ color: "#94a3b8", fontSize: "11px" }}>STANDARD</span>
                    )}
                  </td>
                  <td>{o.delivery_date}</td>
                  <td><StatusBadge status={o.status} /></td>
                  <td style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono)" }}>
                    {o.correlation_id}
                  </td>
                  <td style={{ fontSize: "11px", color: "#94a3b8" }}>
                    {new Date(o.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Order Modal */}
      <Modal isOpen={isModalOpen} title="Create Manufacturing Order (ERP)" onClose={() => setIsModalOpen(false)}>
        <form onSubmit={handleCreateOrder}>
          <div className="form-group">
            <label className="form-label">Target Supplier</label>
            <select
              className="form-control"
              value={supplierId}
              onChange={(e) => setSupplierId(e.target.value)}
            >
              <option value="SUP-A">Supplier A - Alpha Components Ltd. (REST v1)</option>
              <option value="SUP-B">Supplier B - Beta Manufacturing Corp (SOAP/EDI)</option>
              <option value="SUP-C">Supplier C - Gamma Parts GmbH (SAP RFC)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Product SKU</label>
            <select
              className="form-control"
              value={productId}
              onChange={(e) => setProductId(e.target.value)}
            >
              <option value="PROD-101">PROD-101 - Titanium Spindle Assembly</option>
              <option value="PROD-102">PROD-102 - Precision Servo Actuator</option>
              <option value="PROD-103">PROD-103 - High-Pressure Hydraulic Valve</option>
              <option value="PROD-104">PROD-104 - Carbon Composite Bearing</option>
              <option value="PROD-105">PROD-105 - Optical Rotary Encoder</option>
            </select>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div className="form-group">
              <label className="form-label">Quantity (Units)</label>
              <input
                type="number"
                className="form-control"
                min="1"
                value={quantity}
                onChange={(e) => setQuantity(Number(e.target.value))}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Requested Delivery Date</label>
              <input
                type="date"
                className="form-control"
                value={deliveryDate}
                onChange={(e) => setDeliveryDate(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="form-group" style={{ display: "flex", alignItems: "center", gap: "10px", marginTop: "8px" }}>
            <input
              type="checkbox"
              id="urgentCheck"
              checked={isUrgent}
              onChange={(e) => setIsUrgent(e.target.checked)}
              style={{ width: "16px", height: "16px" }}
            />
            <label htmlFor="urgentCheck" style={{ fontSize: "13px", fontWeight: 600, color: "#fff", cursor: "pointer" }}>
              Mark as Urgent Order (Subject to CR-001 Priority Threshold Evaluation)
            </label>
          </div>

          <div style={{
            background: "rgba(59, 130, 246, 0.1)",
            border: "1px solid rgba(59, 130, 246, 0.3)",
            borderRadius: "6px",
            padding: "10px",
            fontSize: "12px",
            color: "#93c5fd",
            marginBottom: "16px"
          }}>
            Rule Engine Note: If urgent and quantity &gt;= active threshold (100 in BR-1.0, 200 in BR-2.0), the Canonical Layer will classify priority as <strong>PRIORITY_HIGH</strong>.
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px" }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              {submitting ? "Processing..." : "Submit Order to Gateway"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
