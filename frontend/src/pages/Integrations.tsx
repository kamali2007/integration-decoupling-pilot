import React, { useState, useEffect } from "react";
import { api, SystemStatus } from "../services/api";
import { StatusBadge } from "../components/StatusBadge";

export const Integrations: React.FC = () => {
  const [systems, setSystems] = useState<SystemStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadSystems = async () => {
    try {
      const data = await api.getSystems();
      setSystems(data);
    } catch (err) {
      console.error("Failed to load systems:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSystems();
    const interval = setInterval(loadSystems, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleSimulate = async (systemName: string, targetStatus: string, label: string) => {
    try {
      await api.simulateSystemStatus({ system_name: systemName, target_status: targetStatus });
      setStatusMessage(`State Updated: ${systemName} marked as ${targetStatus} (${label}).`);
      loadSystems();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      alert(`Simulation error: ${err.message}`);
    }
  };

  const handleRecoverAll = async () => {
    try {
      await api.recoverAllSystems();
      setStatusMessage("All integration systems recovered to ONLINE nominal status.");
      loadSystems();
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      alert(`Recovery error: ${err.message}`);
    }
  };

  return (
    <div>
      {statusMessage && (
        <div style={{
          background: "rgba(59, 130, 246, 0.15)",
          border: "1px solid #3b82f6",
          borderRadius: "8px",
          padding: "12px 16px",
          marginBottom: "20px",
          color: "#93c5fd",
          fontWeight: 600
        }}>
          {statusMessage}
        </div>
      )}

      {/* Simulation Controls Panel */}
      <div className="panel-card" style={{ borderColor: "rgba(59, 130, 246, 0.4)" }}>
        <div className="panel-header">
          <div>
            <div className="panel-title">
              <span style={{ color: "#3b82f6" }}>🕹️</span> Live Resilience & Simulation Controls
            </div>
            <div className="panel-subtitle">
              Trigger live upstream delays and downstream endpoint failures to verify non-blocking decoupled resilience
            </div>
          </div>
          <button className="btn btn-success" onClick={handleRecoverAll}>
            &check; Recover All Systems to ONLINE
          </button>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
          <button
            className="btn btn-warning btn-sm"
            style={{ justifyContent: "flex-start", padding: "12px" }}
            onClick={() => handleSimulate("ERP", "DELAYED", "Simulate ERP Delay")}
          >
            ⏱️ Simulate ERP Delay (4500ms)
          </button>

          <button
            className="btn btn-warning btn-sm"
            style={{ justifyContent: "flex-start", padding: "12px" }}
            onClick={() => handleSimulate("FORECAST", "DELAYED", "Simulate Forecast Delay")}
          >
            ⏱️ Simulate Forecast Delay (Batch lag)
          </button>

          <button
            className="btn btn-danger btn-sm"
            style={{ justifyContent: "flex-start", padding: "12px" }}
            onClick={() => handleSimulate("SUP-C", "OFFLINE", "Simulate Supplier C Failure")}
          >
            💥 Simulate Supplier C Failure (503)
          </button>

          <button
            className="btn btn-secondary btn-sm"
            style={{ justifyContent: "flex-start", padding: "12px" }}
            onClick={() => handleSimulate("SUP-C", "ONLINE", "Recover Supplier C")}
          >
            🔄 Recover Supplier C
          </button>
        </div>
      </div>

      {/* System Status Table */}
      <div className="panel-card">
        <div className="panel-header">
          <div>
            <div className="panel-title">Integrated Systems & Endpoints Monitor</div>
            <div className="panel-subtitle">Current health telemetry, latency, error rate, and heartbeat monitoring</div>
          </div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>System Name</th>
                <th>System Role</th>
                <th>Status</th>
                <th>Latency (Round-Trip)</th>
                <th>Error Rate</th>
                <th>Last Heartbeat</th>
                <th>Operational Telemetry</th>
                <th>Manual Override</th>
              </tr>
            </thead>
            <tbody>
              {systems.map((s) => (
                <tr key={s.id}>
                  <td style={{ fontWeight: 700, color: "#fff" }}>{s.display_name}</td>
                  <td>
                    <span style={{
                      fontSize: "11px",
                      fontWeight: 700,
                      color: s.system_type === "SOURCE" ? "#60a5fa" : "#34d399",
                      background: s.system_type === "SOURCE" ? "rgba(59, 130, 246, 0.15)" : "rgba(16, 185, 129, 0.15)",
                      padding: "3px 8px",
                      borderRadius: "4px"
                    }}>
                      {s.system_type}
                    </span>
                  </td>
                  <td><StatusBadge status={s.status} /></td>
                  <td style={{ fontWeight: 600, color: s.latency_ms > 1000 ? "#fbbf24" : "#fff" }}>
                    {s.latency_ms} ms
                  </td>
                  <td style={{ fontWeight: 600, color: s.error_rate > 0 ? "#f87171" : "#34d399" }}>
                    {(s.error_rate * 100).toFixed(1)}%
                  </td>
                  <td style={{ fontSize: "11.5px", color: "#94a3b8" }}>
                    {new Date(s.last_heartbeat).toLocaleTimeString()}
                  </td>
                  <td style={{ fontSize: "12px", color: "#cbd5e1" }}>{s.details || "Nominal telemetry"}</td>
                  <td>
                    <div style={{ display: "flex", gap: "6px" }}>
                      {s.status !== "ONLINE" ? (
                        <button
                          className="btn btn-success btn-sm"
                          onClick={() => handleSimulate(s.system_name, "ONLINE", "Online Override")}
                        >
                          Restore
                        </button>
                      ) : (
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => handleSimulate(s.system_name, "DEGRADED", "Degrade")}
                        >
                          Degrade
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
