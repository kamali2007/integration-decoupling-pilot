import React, { useState, useEffect } from "react";
import { api, AuditEntry } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";
import { Modal } from "../components/Modal";

export const AuditTrail: React.FC<{ initialSearch?: string }> = ({ initialSearch }) => {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null);
  const [filterAction, setFilterAction] = useState<string>("");
  const [searchTerm, setSearchTerm] = useState<string>(initialSearch || "");

  const loadAuditTrail = async () => {
    try {
      const data = await api.getAuditTrail(filterAction || undefined, searchTerm || undefined);
      setEntries(data);
    } catch (err) {
      console.error("Failed to load audit trail:", err);
    }
  };

  useEffect(() => {
    loadAuditTrail();
  }, [filterAction, searchTerm]);

  return (
    <div>
      <div className="panel-card">
        <div className="panel-header">
          <div>
            <div className="panel-title">Immutable Enterprise Audit Trail</div>
            <div className="panel-subtitle">
              Comprehensive chronological ledger tracking every ingestion, validation, adapter dispatch, failure, and rollback
            </div>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={loadAuditTrail}>
            🔄 Refresh Ledger
          </button>
        </div>

        {/* Filter & Search */}
        <div className="filter-bar">
          <input
            type="text"
            className="form-control search-input"
            placeholder="Search by Entity ID, Action, Actor..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />

          <select
            className="form-control search-input"
            value={filterAction}
            onChange={(e) => setFilterAction(e.target.value)}
          >
            <option value="">All Action Types</option>
            <option value="ORDER_CREATED">ORDER_CREATED</option>
            <option value="EVENT_CREATED">EVENT_CREATED</option>
            <option value="EVENT_VALIDATED">EVENT_VALIDATED</option>
            <option value="EVENT_TRANSFORMED">EVENT_TRANSFORMED</option>
            <option value="EVENT_SENT">EVENT_SENT</option>
            <option value="EVENT_FAILED">EVENT_FAILED</option>
            <option value="EVENT_RETRIED">EVENT_RETRIED</option>
            <option value="DUPLICATE_DETECTED">DUPLICATE_DETECTED</option>
            <option value="CHANGE_APPROVED">CHANGE_APPROVED</option>
            <option value="CHANGE_DEPLOYED">CHANGE_DEPLOYED</option>
            <option value="ROLLBACK_COMPLETED">ROLLBACK_COMPLETED</option>
          </select>

          <span style={{ fontSize: "12px", color: "var(--text-muted)", marginLeft: "auto" }}>
            Showing {entries.length} audited records
          </span>
        </div>

        {/* Table */}
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Audit ID</th>
                <th>Timestamp (UTC)</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity Target</th>
                <th>State Delta (Summary)</th>
                <th>Outcome</th>
                <th>Correlation Trace</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((a) => (
                <tr key={a.id}>
                  <td style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: "#60a5fa" }}>
                    {a.audit_id}
                  </td>
                  <td style={{ fontSize: "11.5px", color: "#94a3b8" }}>
                    {new Date(a.timestamp).toLocaleString()}
                  </td>
                  <td style={{ fontWeight: 600, color: "#cbd5e1" }}>{a.actor}</td>
                  <td>
                    <span style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      color: a.action.includes("FAILED") ? "#ef4444" : a.action.includes("ROLLBACK") ? "#c084fc" : "#38bdf8"
                    }}>
                      {a.action}
                    </span>
                  </td>
                  <td>
                    <span style={{ fontSize: "12px" }}>
                      {a.entity_type}: <strong style={{ color: "#fff" }}>{a.entity_id}</strong>
                    </span>
                  </td>
                  <td style={{ fontSize: "12px", maxWidth: "250px", color: "#cbd5e1" }}>
                    {a.new_value || a.old_value || "State logged"}
                  </td>
                  <td><StatusBadge status={a.status} /></td>
                  <td style={{ fontSize: "11px", color: "#64748b", fontFamily: "var(--font-mono)" }}>
                    {a.correlation_id || "N/A"}
                  </td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => setSelectedEntry(a)}>
                      Diff
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Entry Detail Modal */}
      <Modal
        isOpen={Boolean(selectedEntry)}
        title={`Audit Record Detail: ${selectedEntry?.audit_id}`}
        onClose={() => setSelectedEntry(null)}
      >
        {selectedEntry && (
          <div style={{ lineHeight: "1.7", fontSize: "13px" }}>
            <div><strong style={{ color: "#94a3b8" }}>Audit ID:</strong> {selectedEntry.audit_id}</div>
            <div><strong style={{ color: "#94a3b8" }}>Timestamp:</strong> {new Date(selectedEntry.timestamp).toISOString()}</div>
            <div><strong style={{ color: "#94a3b8" }}>Actor:</strong> {selectedEntry.actor}</div>
            <div><strong style={{ color: "#94a3b8" }}>Action:</strong> {selectedEntry.action}</div>
            <div><strong style={{ color: "#94a3b8" }}>Entity:</strong> {selectedEntry.entity_type} ({selectedEntry.entity_id})</div>
            <div><strong style={{ color: "#94a3b8" }}>Correlation ID:</strong> {selectedEntry.correlation_id || "N/A"}</div>
            
            <div style={{ marginTop: "12px", marginBottom: "8px", fontWeight: 700, color: "#fff" }}>State Before:</div>
            <pre className="code-box" style={{ color: "#fca5a5" }}>{selectedEntry.old_value || "None (Initial Creation)"}</pre>

            <div style={{ marginTop: "12px", marginBottom: "8px", fontWeight: 700, color: "#fff" }}>State After:</div>
            <pre className="code-box" style={{ color: "#6ee7b7" }}>{selectedEntry.new_value || "N/A"}</pre>

            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
              <button className="btn btn-secondary" onClick={() => setSelectedEntry(null)}>
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
