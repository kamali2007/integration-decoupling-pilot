import React, { useState, useEffect } from "react";
import { api, FailureCase } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";
import { Modal } from "../components/Modal";

export const Failures: React.FC<{ onNavigateToAudit?: (search: string) => void }> = ({ onNavigateToAudit }) => {
  const [failures, setFailures] = useState<FailureCase[]>([]);
  const [selectedFailure, setSelectedFailure] = useState<FailureCase | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [simulating, setSimulating] = useState(false);

  const loadFailures = async () => {
    try {
      const data = await api.getFailures();
      setFailures(data);
    } catch (err) {
      console.error("Failed to load failures:", err);
    }
  };

  useEffect(() => {
    loadFailures();
  }, []);

  const handleSimulate = async (type: string, system: string) => {
    setSimulating(true);
    try {
      const res = await api.simulateFailure(type, system);
      setActionMessage(`Injected Failure: ${res.failure_id} (${type}) detected on ${system}.`);
      loadFailures();
      setTimeout(() => setActionMessage(null), 4000);
    } catch (err: any) {
      alert(`Simulation error: ${err.message}`);
    } finally {
      setSimulating(false);
    }
  };

  const handleRetry = async (failureId: string) => {
    try {
      const res = await api.retryFailure(failureId);
      setActionMessage(`Failure ${res.failure_id} retried successfully! Status: ${res.status}`);
      loadFailures();
      setTimeout(() => setActionMessage(null), 4000);
    } catch (err: any) {
      alert(`Retry error: ${err.message}`);
    }
  };

  const handleResolve = async (failureId: string) => {
    try {
      const res = await api.resolveFailure(failureId);
      setActionMessage(`Failure ${res.failure_id} marked as RESOLVED.`);
      loadFailures();
      setTimeout(() => setActionMessage(null), 4000);
    } catch (err: any) {
      alert(`Resolve error: ${err.message}`);
    }
  };

  return (
    <div>
      {actionMessage && (
        <div style={{
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid #10b981",
          borderRadius: "8px",
          padding: "12px 16px",
          marginBottom: "20px",
          color: "#34d399",
          fontWeight: 600
        }}>
          {actionMessage}
        </div>
      )}

      {/* Failure Injection Quick Bar */}
      <div className="panel-card" style={{ borderColor: "rgba(239, 68, 68, 0.3)" }}>
        <div className="panel-header">
          <div>
            <div className="panel-title">
              <span style={{ color: "#ef4444" }}>⚠️</span> Failure Injection & Recovery Simulation
            </div>
            <div className="panel-subtitle">
              Trigger any of the 5 industry failure modes to test gateway isolation and automated recovery
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => handleSimulate("MISSING_DATA", "ERP System")}
            disabled={simulating}
          >
            1. Missing ERP Data
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => handleSimulate("DELAYED_DATA", "Forecast System")}
            disabled={simulating}
          >
            2. Delayed Forecast Data
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => handleSimulate("SCHEMA_VIOLATION", "Supplier B Adapter")}
            disabled={simulating}
          >
            3. Invalid Supplier Message
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => handleSimulate("ENDPOINT_UNAVAILABLE", "Supplier C Endpoint")}
            disabled={simulating}
          >
            4. Supplier Endpoint 503
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={() => handleSimulate("DUPLICATE_EVENT", "Ingestion Gateway")}
            disabled={simulating}
          >
            5. Duplicate Event (Idempotency)
          </button>
        </div>
      </div>

      {/* Failure Mode Analysis Table */}
      <div className="panel-card">
        <div className="panel-header">
          <div>
            <div className="panel-title">Failure Mode & Effects Analysis (FMEA) Table</div>
            <div className="panel-subtitle">Active and historical failure cases, root cause detection, and recovery actions</div>
          </div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Failure ID</th>
                <th>Failure Type</th>
                <th>Affected System</th>
                <th>Severity</th>
                <th>Root Cause</th>
                <th>Detection Method</th>
                <th>Status</th>
                <th>Retries</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {failures.map((f) => (
                <tr key={f.id}>
                  <td style={{ fontWeight: 700, color: "#f87171", fontFamily: "var(--font-mono)" }}>
                    {f.failure_id}
                  </td>
                  <td>
                    <span style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      color: "#fbbf24",
                      background: "rgba(245, 158, 11, 0.15)",
                      padding: "2px 6px",
                      borderRadius: "4px"
                    }}>
                      {f.failure_type}
                    </span>
                  </td>
                  <td style={{ fontWeight: 600, color: "#fff" }}>{f.affected_system}</td>
                  <td>
                    <span style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      color: f.severity === "CRITICAL" || f.severity === "HIGH" ? "#ef4444" : "#fbbf24"
                    }}>
                      {f.severity}
                    </span>
                  </td>
                  <td style={{ fontSize: "12px", color: "#cbd5e1", maxWidth: "240px" }}>{f.cause}</td>
                  <td style={{ fontSize: "11.5px", color: "#94a3b8" }}>{f.detection_method}</td>
                  <td><StatusBadge status={f.status} /></td>
                  <td style={{ fontWeight: 600 }}>{f.retry_count}</td>
                  <td>
                    <div style={{ display: "flex", gap: "6px" }}>
                      {f.status !== "RESOLVED" && (
                        <>
                          <button className="btn btn-warning btn-sm" onClick={() => handleRetry(f.failure_id)}>
                            Retry
                          </button>
                          <button className="btn btn-success btn-sm" onClick={() => handleResolve(f.failure_id)}>
                            Resolve
                          </button>
                        </>
                      )}
                      <button className="btn btn-secondary btn-sm" onClick={() => setSelectedFailure(f)}>
                        Details
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Failure Detail Modal */}
      <Modal
        isOpen={Boolean(selectedFailure)}
        title={`Failure Mode Analysis: ${selectedFailure?.failure_id}`}
        onClose={() => setSelectedFailure(null)}
      >
        {selectedFailure && (
          <div style={{ lineHeight: "1.7", fontSize: "13px" }}>
            <div style={{ marginBottom: "10px" }}>
              <strong style={{ color: "#94a3b8" }}>Failure Type:</strong>{" "}
              <span style={{ color: "#fbbf24", fontWeight: 700 }}>{selectedFailure.failure_type}</span>
            </div>
            <div style={{ marginBottom: "10px" }}>
              <strong style={{ color: "#94a3b8" }}>Affected System:</strong> {selectedFailure.affected_system}
            </div>
            <div style={{ marginBottom: "10px" }}>
              <strong style={{ color: "#94a3b8" }}>Root Cause:</strong> {selectedFailure.cause}
            </div>
            <div style={{ marginBottom: "10px" }}>
              <strong style={{ color: "#94a3b8" }}>Business Impact:</strong> {selectedFailure.impact}
            </div>
            <div style={{ marginBottom: "10px" }}>
              <strong style={{ color: "#94a3b8" }}>Detection Mechanism:</strong> {selectedFailure.detection_method}
            </div>
            <div style={{ marginBottom: "10px" }}>
              <strong style={{ color: "#94a3b8" }}>Recovery Action:</strong> {selectedFailure.recovery_action}
            </div>
            <div style={{ marginBottom: "10px" }}>
              <strong style={{ color: "#94a3b8" }}>Audit Reference:</strong>{" "}
              <code style={{ color: "#60a5fa" }}>{selectedFailure.audit_reference || "N/A"}</code>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
              <button className="btn btn-secondary" onClick={() => setSelectedFailure(null)}>
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
