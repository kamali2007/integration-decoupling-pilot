import React, { useEffect, useState } from "react";
import { api, Order, Forecast, CanonicalEvent, FailureCase, SystemStatus, AuditEntry } from "../services/api";
import { MetricCard } from "../components/MetricCard";
import { StatusBadge } from "../components/StatusBadge";
import { ProcessMap } from "../components/ProcessMap";

export const Dashboard: React.FC<{ onNavigate: (page: string) => void }> = ({ onNavigate }) => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [forecasts, setForecasts] = useState<Forecast[]>([]);
  const [events, setEvents] = useState<CanonicalEvent[]>([]);
  const [failures, setFailures] = useState<FailureCase[]>([]);
  const [systems, setSystems] = useState<SystemStatus[]>([]);
  const [recentAudits, setRecentAudits] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      const [ord, fcst, evt, fail, sys, aud] = await Promise.all([
        api.getOrders(),
        api.getForecasts(),
        api.getEvents(),
        api.getFailures(),
        api.getSystems(),
        api.getAuditTrail()
      ]);
      setOrders(ord);
      setForecasts(fcst);
      setEvents(evt);
      setFailures(fail);
      setSystems(sys);
      setRecentAudits(aud.slice(0, 8));
    } catch (err) {
      console.error("Dashboard data load error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const processedCount = events.filter((e) => e.status === "PROCESSED").length;
  const failedCount = failures.filter((f) => f.status === "OPEN").length;
  const pendingCount = events.filter((e) => e.status === "PENDING" || e.status === "RETRYING").length;

  return (
    <div>
      {/* Top Banner KPI highlight */}
      <div className="kpi-banner">
        <div>
          <div style={{ fontSize: "11px", color: "#34d399", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Integration Decoupling Milestone
          </div>
          <div style={{ fontSize: "20px", fontWeight: 800, color: "#fff", marginTop: "4px" }}>
            83.3% Blast-Radius Reduction Achieved
          </div>
          <div style={{ fontSize: "13px", color: "#94a3b8", marginTop: "4px", maxWidth: "600px" }}>
            Moving from fragile point-to-point connections to the Canonical Event Layer reduces business-rule modification points from <strong>6 systems down to 1 component</strong>.
          </div>
        </div>
        <div style={{ display: "flex", gap: "28px" }}>
          <div className="kpi-stat">
            <div className="kpi-number" style={{ color: "#ef4444" }}>6</div>
            <div className="kpi-label">Baseline Touchpoints</div>
          </div>
          <div style={{ fontSize: "36px", color: "#64748b", alignSelf: "center" }}>&rarr;</div>
          <div className="kpi-stat">
            <div className="kpi-number" style={{ color: "#34d399" }}>1</div>
            <div className="kpi-label">Canonical Layer</div>
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="metrics-grid">
        <MetricCard label="Total Orders" value={orders.length} subtext="ERP Ingestion Stream" />
        <MetricCard label="Total Forecasts" value={forecasts.length} subtext="Multi-Period Projections" />
        <MetricCard label="Events Processed" value={processedCount} subtext="Transformed by Adapters" isHighlight />
        <MetricCard label="Open Failures" value={failedCount} subtext={failedCount > 0 ? "Requires Operator Attention" : "All Systems Nominal"} />
        <MetricCard label="Pending / Retrying" value={pendingCount} subtext="Async Queue Buffer" />
        <MetricCard label="Active Integrations" value={systems.length} subtext="5 Sources & Targets Online" />
      </div>

      {/* Process Map Component */}
      <ProcessMap />

      {/* Integration System Health & Recent Audits side-by-side */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        {/* Integration Status Monitor */}
        <div className="panel-card">
          <div className="panel-header">
            <div>
              <div className="panel-title">Integration Endpoints Health</div>
              <div className="panel-subtitle">Real-time status across ERP, Forecasts, and Suppliers</div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("integrations")}>
              Control Tower &rarr;
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {systems.map((sys) => (
              <div
                key={sys.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px 14px",
                  background: "#0d1424",
                  borderRadius: "8px",
                  border: "1px solid var(--border-subtle)"
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: "13.5px", color: "#fff" }}>{sys.display_name}</div>
                  <div style={{ fontSize: "11.5px", color: "#64748b" }}>
                    Latency: {sys.latency_ms}ms &bull; Error Rate: {(sys.error_rate * 100).toFixed(1)}%
                  </div>
                </div>
                <StatusBadge status={sys.status} />
              </div>
            ))}
          </div>
        </div>

        {/* Recent Audit Trail Feed */}
        <div className="panel-card">
          <div className="panel-header">
            <div>
              <div className="panel-title">Live Audit Trail Feed</div>
              <div className="panel-subtitle">Immutable chronological ledger of all events and state transitions</div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("audit")}>
              Full Audit Trail &rarr;
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {recentAudits.map((a) => (
              <div
                key={a.id}
                style={{
                  padding: "10px 14px",
                  background: "#0d1424",
                  borderRadius: "6px",
                  border: "1px solid var(--border-subtle)",
                  fontSize: "12px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between"
                }}
              >
                <div>
                  <span style={{ fontWeight: 700, color: "#60a5fa", marginRight: "8px" }}>[{a.action}]</span>
                  <span style={{ color: "#cbd5e1" }}>{a.entity_type}: {a.entity_id}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <StatusBadge status={a.status} />
                  <span style={{ color: "#64748b", fontSize: "11px" }}>
                    {new Date(a.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
