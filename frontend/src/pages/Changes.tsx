import React, { useState, useEffect } from "react";
import { api, ChangeRequest } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";
import { Modal } from "../components/Modal";

export const Changes: React.FC = () => {
  const [changes, setChanges] = useState<ChangeRequest[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // Form state
  const [title, setTitle] = useState("Urgent Order Quantity Threshold Realignment");
  const [description, setDescription] = useState("Raise urgent order volume threshold from 100 to 200 EA to restrict priority air freight.");
  const [newThreshold, setNewThreshold] = useState(200);

  const loadChanges = async () => {
    try {
      const data = await api.getChanges();
      setChanges(data);
    } catch (err) {
      console.error("Failed to load changes:", err);
    }
  };

  useEffect(() => {
    loadChanges();
  }, []);

  const handleCreateChange = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const cr = await api.createChange({
        title,
        description,
        new_threshold: Number(newThreshold),
        submitted_by: "Senior Supply Chain Architect"
      });
      setMessage(`Change Request ${cr.change_id} created in DRAFT state.`);
      setIsModalOpen(false);
      loadChanges();
      setTimeout(() => setMessage(null), 4000);
    } catch (err: any) {
      alert(`Error creating change: ${err.message}`);
    }
  };

  const handleAction = async (id: string, action: "submit" | "approve" | "reject" | "deploy" | "rollback") => {
    setActionLoading(id);
    try {
      if (action === "submit") await api.submitChange(id);
      if (action === "approve") await api.approveChange(id);
      if (action === "reject") await api.rejectChange(id);
      if (action === "deploy") await api.deployChange(id);
      if (action === "rollback") await api.rollbackChange(id);
      setMessage(`Change request ${id} successfully transitioned via '${action.toUpperCase()}'.`);
      loadChanges();
      setTimeout(() => setMessage(null), 4000);
    } catch (err: any) {
      alert(`Action error: ${err.message}`);
    } finally {
      setActionLoading(null);
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

      <div className="panel-card">
        <div className="panel-header">
          <div>
            <div className="panel-title">Change Management & Governance Workflow</div>
            <div className="panel-subtitle">
              Formal audit-backed promotion lifecycle: DRAFT &rarr; UNDER_REVIEW &rarr; APPROVED &rarr; DEPLOYED &rarr; ROLLED_BACK
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
            + Propose Business Rule Change
          </button>
        </div>

        <div style={{
          background: "rgba(59, 130, 246, 0.08)",
          border: "1px solid rgba(59, 130, 246, 0.3)",
          borderRadius: "8px",
          padding: "14px",
          marginBottom: "20px",
          fontSize: "12.5px",
          color: "#93c5fd"
        }}>
          <strong>Governance Policy:</strong> High-impact business rule modifications require explicit review and approval by an authorized architect before deployment. Direct deployment of unapproved drafts is strictly blocked by the backend.
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Change ID</th>
                <th>Title / Description</th>
                <th>Rule Version Transition</th>
                <th>Threshold Shift</th>
                <th>Systems Blast Radius</th>
                <th>Status</th>
                <th>Approver</th>
                <th>Lifecycle Action</th>
              </tr>
            </thead>
            <tbody>
              {changes.map((c) => (
                <tr key={c.id}>
                  <td style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "#60a5fa" }}>
                    {c.change_id}
                  </td>
                  <td style={{ maxWidth: "260px" }}>
                    <div style={{ fontWeight: 600, color: "#fff" }}>{c.title}</div>
                    <div style={{ fontSize: "11.5px", color: "#94a3b8" }}>{c.description}</div>
                  </td>
                  <td>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "11.5px" }}>
                      {c.current_rule_version} &rarr;{" "}
                      <strong style={{ color: "#34d399" }}>{c.proposed_rule_version}</strong>
                    </span>
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {c.previous_threshold} EA &rarr;{" "}
                    <span style={{ color: "#fbbf24" }}>{c.new_threshold} EA</span>
                  </td>
                  <td>
                    <span style={{ color: "#ef4444", fontWeight: 700 }}>{c.baseline_systems_changed} Baseline</span> &rarr;{" "}
                    <span style={{ color: "#10b981", fontWeight: 800 }}>{c.decoupled_systems_changed} Decoupled</span>
                  </td>
                  <td><StatusBadge status={c.status} /></td>
                  <td style={{ fontSize: "12px", color: "#cbd5e1" }}>{c.approved_by || "Pending"}</td>
                  <td>
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                      {c.status === "DRAFT" && (
                        <button
                          className="btn btn-secondary btn-sm"
                          disabled={actionLoading === c.change_id}
                          onClick={() => handleAction(c.change_id, "submit")}
                        >
                          Submit Review
                        </button>
                      )}

                      {c.status === "UNDER_REVIEW" && (
                        <>
                          <button
                            className="btn btn-success btn-sm"
                            disabled={actionLoading === c.change_id}
                            onClick={() => handleAction(c.change_id, "approve")}
                          >
                            Approve
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            disabled={actionLoading === c.change_id}
                            onClick={() => handleAction(c.change_id, "reject")}
                          >
                            Reject
                          </button>
                        </>
                      )}

                      {c.status === "APPROVED" && (
                        <button
                          className="btn btn-primary btn-sm"
                          disabled={actionLoading === c.change_id}
                          onClick={() => handleAction(c.change_id, "deploy")}
                        >
                          🚀 Deploy to Prod
                        </button>
                      )}

                      {c.status === "DEPLOYED" && (
                        <button
                          className="btn btn-warning btn-sm"
                          disabled={actionLoading === c.change_id}
                          onClick={() => handleAction(c.change_id, "rollback")}
                        >
                          ⏮️ Rollback
                        </button>
                      )}

                      {c.status === "ROLLED_BACK" && (
                        <span style={{ color: "#c084fc", fontSize: "11px", fontWeight: 700 }}>
                          ROLLED BACK
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create Change Request Modal */}
      <Modal isOpen={isModalOpen} title="Draft Business Rule Change Request" onClose={() => setIsModalOpen(false)}>
        <form onSubmit={handleCreateChange}>
          <div className="form-group">
            <label className="form-label">Change Request Title</label>
            <input
              type="text"
              className="form-control"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Business Justification & Description</label>
            <textarea
              className="form-control"
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div className="form-group">
              <label className="form-label">Baseline Threshold (BR-1.0)</label>
              <input type="text" className="form-control" value="100 Units" disabled />
            </div>
            <div className="form-group">
              <label className="form-label">New Proposed Threshold (BR-2.0)</label>
              <input
                type="number"
                className="form-control"
                min="50"
                max="1000"
                value={newThreshold}
                onChange={(e) => setNewThreshold(Number(e.target.value))}
                required
              />
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "16px" }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Create Draft Change Request
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
