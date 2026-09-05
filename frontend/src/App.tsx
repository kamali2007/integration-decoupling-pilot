import React, { useState, useEffect } from "react";
import { Dashboard } from "./pages/Dashboard";
import { Orders } from "./pages/Orders";
import { Forecasts } from "./pages/Forecasts";
import { Integrations } from "./pages/Integrations";
import { Events } from "./pages/Events";
import { Adapters } from "./pages/Adapters";
import { Failures } from "./pages/Failures";
import { Experiments } from "./pages/Experiments";
import { Changes } from "./pages/Changes";
import { Rollback } from "./pages/Rollback";
import { AuditTrail } from "./pages/AuditTrail";
import { Validation } from "./pages/Validation";
import { api } from "./services/api";

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<string>("dashboard");
  const [backendStatus, setBackendStatus] = useState<"ONLINE" | "OFFLINE">("ONLINE");
  const [openFailuresCount, setOpenFailuresCount] = useState<number>(0);

  const checkHealth = async () => {
    try {
      const res = await api.getHealth();
      setBackendStatus(res.status === "UP" ? "ONLINE" : "ONLINE");
      const failures = await api.getFailures();
      setOpenFailuresCount(failures.filter((f) => f.status === "OPEN").length);
    } catch {
      setBackendStatus("OFFLINE");
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: "📊" },
    { id: "orders", label: "ERP Orders", icon: "📦" },
    { id: "forecasts", label: "Demand Forecasts", icon: "📈" },
    { id: "integrations", label: "Integration Monitor", icon: "🌐" },
    { id: "events", label: "Canonical Events", icon: "⚡" },
    { id: "adapters", label: "Adapter Monitor", icon: "🔌" },
    { id: "failures", label: "Failure Center", icon: "🚨", badge: openFailuresCount > 0 ? openFailuresCount : undefined },
    { id: "experiments", label: "Decoupling Benchmark", icon: "🧪" },
    { id: "changes", label: "Change Requests (CR-001)", icon: "📝" },
    { id: "rollback", label: "Rollback Center", icon: "⏮️" },
    { id: "audit", label: "Audit Trail", icon: "🛡️" },
    { id: "validation", label: "Stakeholder Review", icon: "⭐" },
  ];

  const getPageMeta = () => {
    switch (currentPage) {
      case "dashboard":
        return { title: "Executive Control Tower", subtitle: "End-to-End Enterprise Ingestion and Canonical Decoupling Architecture" };
      case "orders":
        return { title: "Manufacturing Orders Ingestion", subtitle: "SAP ERP Order Feed Canonicalization and Priority Routing" };
      case "forecasts":
        return { title: "Demand Forecast Planning", subtitle: "Multi-Period Projections Ingested and Resilient to Pipeline Delays" };
      case "integrations":
        return { title: "Integration Monitor & Simulator", subtitle: "Source and Target Endpoint Telemetry and State Mutation Simulator" };
      case "events":
        return { title: "Canonical Event Layer", subtitle: "Normalized Invariant Business Schemas and Priority Rule Evaluation" };
      case "adapters":
        return { title: "Supplier Adapter Transformations", subtitle: "Schema Isolation and Side-by-Side Supplier Message Formatting" };
      case "failures":
        return { title: "Failure Center & FMEA", subtitle: "Detection, Classification, and Automated Recovery of 5 Enterprise Failure Modes" };
      case "experiments":
        return { title: "Decoupling Benchmark Experiment", subtitle: "Empirical Blast-Radius Comparison: Baseline (6) vs Decoupled (1) Systems" };
      case "changes":
        return { title: "Change Management & Promotion", subtitle: "Formal Review, Approval, and Deployment Workflow for Business Rules" };
      case "rollback":
        return { title: "Rollback Management", subtitle: "Audited Rule Engine Version Restoration Without Downtime" };
      case "audit":
        return { title: "Immutable Audit Trail", subtitle: "Chronological State Deltas, Actors, Outcomes, and Correlation Traces" };
      case "validation":
        return { title: "Stakeholder Validation", subtitle: "Simulated Architectural Scorecard and Feedback Review" };
      default:
        return { title: "Integration Control Tower", subtitle: "Enterprise Integration Decoupling" };
    }
  };

  const meta = getPageMeta();

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-badge">
            <div className="brand-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <div>
              <div className="brand-title">Control Tower</div>
              <div className="brand-subtitle">Integration Pilot</div>
            </div>
          </div>
        </div>

        <nav className="nav-section">
          <div className="nav-label">Core Operations</div>
          {navItems.slice(0, 4).map((item) => (
            <div
              key={item.id}
              className={`nav-item ${currentPage === item.id ? "active" : ""}`}
              onClick={() => setCurrentPage(item.id)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}

          <div className="nav-label" style={{ marginTop: "14px" }}>Canonical & Adapters</div>
          {navItems.slice(4, 7).map((item) => (
            <div
              key={item.id}
              className={`nav-item ${currentPage === item.id ? "active" : ""}`}
              onClick={() => setCurrentPage(item.id)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
              {item.badge && <span className="nav-badge danger">{item.badge}</span>}
            </div>
          ))}

          <div className="nav-label" style={{ marginTop: "14px" }}>Governance & Verification</div>
          {navItems.slice(7).map((item) => (
            <div
              key={item.id}
              className={`nav-item ${currentPage === item.id ? "active" : ""}`}
              onClick={() => setCurrentPage(item.id)}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span>Backend Gateway:</span>
            <span style={{
              color: backendStatus === "ONLINE" ? "#34d399" : "#f87171",
              fontWeight: 700,
              fontSize: "11px"
            }}>
              &bull; {backendStatus}
            </span>
          </div>
          <div style={{ fontSize: "11px", marginTop: "4px" }}>v1.0.0 &bull; Local SQLite</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-wrapper">
        <header className="top-navbar">
          <div className="page-title-box">
            <h1>{meta.title}</h1>
            <p>{meta.subtitle}</p>
          </div>

          <div className="top-actions">
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => window.open("http://127.0.0.1:8000/docs", "_blank")}
            >
              📖 Swagger API Docs
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => setCurrentPage("experiments")}
            >
              83.3% Decoupling KPI
            </button>
          </div>
        </header>

        <main className="content-area">
          {currentPage === "dashboard" && <Dashboard onNavigate={(page) => setCurrentPage(page)} />}
          {currentPage === "orders" && <Orders />}
          {currentPage === "forecasts" && <Forecasts />}
          {currentPage === "integrations" && <Integrations />}
          {currentPage === "events" && <Events />}
          {currentPage === "adapters" && <Adapters />}
          {currentPage === "failures" && <Failures onNavigateToAudit={() => setCurrentPage("audit")} />}
          {currentPage === "experiments" && <Experiments />}
          {currentPage === "changes" && <Changes />}
          {currentPage === "rollback" && <Rollback />}
          {currentPage === "audit" && <AuditTrail />}
          {currentPage === "validation" && <Validation />}
        </main>
      </div>
    </div>
  );
};
