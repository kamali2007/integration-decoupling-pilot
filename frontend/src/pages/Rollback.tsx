import React, { useState, useEffect } from "react";
import { api, RollbackAction, ChangeRequest } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";
import { Modal } from "../components/Modal";

export const Rollback: React.FC = () => {
  const [rollbacks, setRollbacks] = useState<RollbackAction[]>([]);
  const [deployedChanges, setDeployedChanges] = useState<ChangeRequest[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedChangeId, setSelectedChangeId] = useState<string>("");
  const [reason, setReason] = useState("Downstream latency regression detected in supplier dispatch.");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [rbList, chList] = await Promise.all([
        api.getRollbacks(),
        api.getChanges()
      ]);
      setRollbacks(rbList);
      const activeDeployed = chList.filter((c) => c.status === "DEPLOYED");
      setDeployedChanges(activeDeployed);
      if (activeDeployed.length > 0) {
        setSelectedChangeId(activeDeployed[0].change_id);
      }
    } catch (err) {
      console.error("Failed to load rollback data:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRollback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedChangeId) {
      alert("Please select a deployed change request to roll back.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await api.rollbackChange(selectedChangeId);
      setMessage(`Rollback executed! Restored to rule version: ${res.restored_version}`);
      setIsModalOpen(false);
      loadData();
      setTimeout(() => setMessage(null), 5000);
    } catch (err: any) {
      alert(`Rollback failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

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

      {/* Safety Policy Banner */}
      <div className="panel-card" style={{ borderColor: "rgba(139, 92, 246, 0.4)" }}>
        <div className="panel-header">
          <div>
            <div className="panel-title">
              <span style={{ color: "#c084fc" }}>⏮️</span> Production Rollback Management
            </div>
            <div className="panel-subtitle">
              Instant business rule state reversal without restarting downstream adapter services or incurring downtime
            </div>
          </div>
          {deployedChanges.length > 0 ? (
            <button className="btn btn-warning" onClick={() => setIsModalOpen(true)}>
              ⚠️ Initiate Emergency Rollback
            </button>
          ) : (
            <span style={{ fontSize: "12px", color: "var(--text-muted)", alignSelf: "center" }}>
              No currently deployed changes eligible for rollback
            </span>
          )}
        </div>

        {/* Rule Version Visual Flow */}
        <div style={{
          background: "#0d1424",
          border: "1px solid var(--border-subtle)",
          borderRadius: "8px",
          padding: "20px",
          marginBottom: "24px"
        }}>
          <div style={{ fontSize: "12px", fontWeight: 700, color: "#94a3b8", marginBottom: "12px", textTransform: "uppercase" }}>
            Version Rollback Mechanism Flow
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
            <div style={{ background: "#1e293b", padding: "10px 16px", borderRadius: "6px", border: "1px solid #3b82f6" }}>
              <div style={{ fontSize: "11px", color: "#60a5fa" }}>Baseline Baseline</div>
              <div style={{ fontWeight: 700, color: "#fff" }}>BR-1.0 (Threshold: 100)</div>
            </div>
            <div style={{ color: "#64748b", fontSize: "18px" }}>&rarr;</div>
            <div style={{ background: "#1e293b", padding: "10px 16px", borderRadius: "6px", border: "1px solid #10b981" }}>
              <div style={{ fontSize: "11px", color: "#34d399" }}>Deployed Upgrade</div>
              <div style={{ fontWeight: 700, color: "#fff" }}>BR-2.0 (Threshold: 200)</div>
            </div>
            <div style={{ color: "#64748b", fontSize: "18px" }}>&rarr;</div>
            <div style={{ background: "#1e293b", padding: "10px 16px", borderRadius: "6px", border: "1px solid #c084fc" }}>
              <div style={{ fontSize: "11px", color: "#c084fc" }}>Rollback Reversion</div>
              <div style={{ fontWeight: 700, color: "#fff" }}>Restored BR-1.0 (Threshold: 100)</div>
            </div>
          </div>
        </div>

        {/* Historical Rollbacks Table */}
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Rollback ID</th>
                <th>Change Reference</th>
                <th>Reverted From</th>
                <th>Restored To</th>
                <th>Initiated By</th>
                <th>Rollback Justification</th>
                <th>Execution Status</th>
                <th>Timestamp (UTC)</th>
              </tr>
            </thead>
            <tbody>
              {rollbacks.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: "center", color: "#94a3b8", padding: "30px" }}>
                    No rollbacks have been executed yet. The active system is operating under validated business rules.
                  </td>
                </tr>
              ) : (
                rollbacks.map((rb) => (
                  <tr key={rb.id}>
                    <td style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "#c084fc" }}>
                      {rb.rollback_id}
                    </td>
                    <td style={{ fontFamily: "var(--font-mono)" }}>{rb.change_id}</td>
                    <td style={{ color: "#f87171", fontWeight: 600 }}>{rb.from_version}</td>
                    <td style={{ color: "#34d399", fontWeight: 700 }}>{rb.to_version}</td>
                    <td style={{ fontWeight: 600 }}>{rb.initiated_by}</td>
                    <td style={{ fontSize: "12px", color: "#cbd5e1" }}>{rb.reason}</td>
                    <td><StatusBadge status={rb.status} /></td>
                    <td style={{ fontSize: "11.5px", color: "#94a3b8" }}>
                      {new Date(rb.timestamp).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Rollback Confirmation Modal */}
      <Modal isOpen={isModalOpen} title="Execute Production Rule Rollback" onClose={() => setIsModalOpen(false)}>
        <form onSubmit={handleRollback}>
          <div style={{
            background: "rgba(239, 68, 68, 0.15)",
            border: "1px solid #ef4444",
            borderRadius: "6px",
            padding: "12px",
            marginBottom: "16px",
            color: "#fca5a5",
            fontSize: "12.5px"
          }}>
            <strong>Anti-Silent Rollback Warning:</strong> This action will immediately revert the active rule engine to its prior version. A mandatory audit log entry and justification record will be permanently etched in the audit trail.
          </div>

          <div className="form-group">
            <label className="form-label">Select Deployed Change Request</label>
            <select
              className="form-control"
              value={selectedChangeId}
              onChange={(e) => setSelectedChangeId(e.target.value)}
              required
            >
              {deployedChanges.map((c) => (
                <option key={c.id} value={c.change_id}>
                  {c.change_id}: {c.title} (Currently active: {c.proposed_rule_version})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Mandatory Rollback Justification</label>
            <textarea
              className="form-control"
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              required
            />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "16px" }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-danger" disabled={submitting}>
              {submitting ? "Reverting..." : "Confirm & Execute Rollback"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
