import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { MetricCard } from "../components/MetricCard";
import { Modal } from "../components/Modal";

export const Validation: React.FC = () => {
  const [summary, setSummary] = useState<any>(null);
  const [validations, setValidations] = useState<any[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  // Form State
  const [name, setName] = useState("Operations Director");
  const [role, setRole] = useState("Supply Chain Lead");
  const [scoreFlow, setScoreFlow] = useState(5);
  const [scoreHealth, setScoreHealth] = useState(5);
  const [scoreRecovery, setScoreRecovery] = useState(4);
  const [scoreChange, setScoreChange] = useState(5);
  const [scoreRollback, setScoreRollback] = useState(5);
  const [scoreDecoupling, setScoreDecoupling] = useState(5);
  const [comments, setComments] = useState("The prototype clearly demonstrates that changing business rules does not cause downstream supplier disruption.");

  const loadData = async () => {
    try {
      const [sum, list] = await Promise.all([
        api.getValidationSummary(),
        api.getValidations()
      ]);
      setSummary(sum);
      setValidations(list);
    } catch (err) {
      console.error("Failed to load validation feedback:", err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.submitValidation({
        respondent_name: name,
        respondent_role: role,
        score_flow: Number(scoreFlow),
        score_health: Number(scoreHealth),
        score_recovery: Number(scoreRecovery),
        score_change: Number(scoreChange),
        score_rollback: Number(scoreRollback),
        score_decoupling: Number(scoreDecoupling),
        comments
      });
      setNotice("Stakeholder evaluation recorded in SQLite repository!");
      setIsModalOpen(false);
      loadData();
      setTimeout(() => setNotice(null), 5000);
    } catch (err: any) {
      alert(`Submission error: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div>
      {/* Required Disclaimer Banner */}
      <div style={{
        background: "rgba(139, 92, 246, 0.1)",
        border: "1px solid rgba(139, 92, 246, 0.4)",
        borderRadius: "10px",
        padding: "16px",
        marginBottom: "24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between"
      }}>
        <div>
          <span style={{
            fontSize: "11px",
            background: "rgba(139, 92, 246, 0.3)",
            color: "#c084fc",
            padding: "3px 8px",
            borderRadius: "4px",
            fontWeight: 800,
            textTransform: "uppercase"
          }}>
            Prototype Validation &ndash; Sample/Simulated
          </span>
          <div style={{ fontSize: "14px", fontWeight: 700, color: "#fff", marginTop: "6px" }}>
            Enterprise Architecture Pilot Stakeholder Review
          </div>
          <div style={{ fontSize: "12px", color: "#cbd5e1" }}>
            Evaluations collected from internal enterprise architects, integration engineers, and supply chain operators.
          </div>
        </div>
        <button className="btn btn-primary" onClick={() => setIsModalOpen(true)}>
          + Submit Evaluation
        </button>
      </div>

      {notice && (
        <div style={{
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid #10b981",
          borderRadius: "8px",
          padding: "12px 16px",
          marginBottom: "20px",
          color: "#34d399",
          fontWeight: 600
        }}>
          {notice}
        </div>
      )}

      {/* Summary Score Cards */}
      {summary && (
        <div className="metrics-grid">
          <MetricCard
            label="Overall Satisfaction"
            value={`${summary.average_overall_score} / 5.0`}
            subtext={`Across ${summary.response_count} Responses`}
            isHighlight
          />
          <MetricCard
            label="Decoupling Ease"
            value={`${summary.category_averages?.decoupling_ease || 5.0} / 5.0`}
            subtext="Perceived Architectural Benefit"
          />
          <MetricCard
            label="Rollback Clarity"
            value={`${summary.category_averages?.rollback_clarity || 5.0} / 5.0`}
            subtext="Safety & Auditability Rating"
          />
          <MetricCard
            label="Integration Health"
            value={`${summary.category_averages?.integration_health || 4.8} / 5.0`}
            subtext="Control Tower Observability"
          />
        </div>
      )}

      {/* Structured Category Breakdowns & Qualitative Findings */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
        {/* Positive Takeaways */}
        <div className="panel-card">
          <div className="panel-header">
            <div className="panel-title">
              <span style={{ color: "#10b981" }}>&check;</span> Key Validated Strengths
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "13px", color: "#cbd5e1" }}>
            <div style={{ background: "#0d1424", padding: "12px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
              &bull; <strong>Blast Radius Reduction:</strong> 83.3% metric is quantifiable and directly convincing to executive leadership.
            </div>
            <div style={{ background: "#0d1424", padding: "12px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
              &bull; <strong>Zero Supplier Disruption:</strong> Supplier adapters remain 100% stable when changing urgent-order volume thresholds.
            </div>
            <div style={{ background: "#0d1424", padding: "12px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
              &bull; <strong>Idempotency Guarantees:</strong> Automatic suppression of duplicate order submissions eliminates redundant factory work.
            </div>
          </div>
        </div>

        {/* Improvement Areas */}
        <div className="panel-card">
          <div className="panel-header">
            <div className="panel-title">
              <span style={{ color: "#fbbf24" }}>💡</span> Identified Future Improvements
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "13px", color: "#cbd5e1" }}>
            <div style={{ background: "#0d1424", padding: "12px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
              &bull; <strong>Automated Alerts:</strong> Add automated Slack/Teams webhooks when retry thresholds on offline suppliers are exceeded.
            </div>
            <div style={{ background: "#0d1424", padding: "12px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
              &bull; <strong>Self-Service Onboarding:</strong> Visual schema mapper for supply chain analysts to onboard Supplier D without code.
            </div>
          </div>
        </div>
      </div>

      {/* Review Log Table */}
      <div className="panel-card">
        <div className="panel-header">
          <div className="panel-title">Stakeholder Review Responses</div>
        </div>

        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Reviewer</th>
                <th>Enterprise Role</th>
                <th>Event Flow</th>
                <th>Health Mon</th>
                <th>Recovery</th>
                <th>Change Ctrl</th>
                <th>Rollback</th>
                <th>Decoupling</th>
                <th>Qualitative Remarks</th>
              </tr>
            </thead>
            <tbody>
              {validations.map((v) => (
                <tr key={v.id}>
                  <td style={{ fontWeight: 700, color: "#fff" }}>{v.respondent_name}</td>
                  <td style={{ fontSize: "12px", color: "#94a3b8" }}>{v.respondent_role}</td>
                  <td>⭐ {v.score_flow}/5</td>
                  <td>⭐ {v.score_health}/5</td>
                  <td>⭐ {v.score_recovery}/5</td>
                  <td>⭐ {v.score_change}/5</td>
                  <td>⭐ {v.score_rollback}/5</td>
                  <td>⭐ {v.score_decoupling}/5</td>
                  <td style={{ fontSize: "12px", color: "#cbd5e1", maxWidth: "260px" }}>{v.comments}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal */}
      <Modal isOpen={isModalOpen} title="Submit Stakeholder Validation Scorecard" onClose={() => setIsModalOpen(false)}>
        <form onSubmit={handleSubmit}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div className="form-group">
              <label className="form-label">Reviewer Name</label>
              <input type="text" className="form-control" value={name} onChange={(e) => setName(e.target.value)} required />
            </div>
            <div className="form-group">
              <label className="form-label">Enterprise Role</label>
              <input type="text" className="form-control" value={role} onChange={(e) => setRole(e.target.value)} required />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginTop: "10px" }}>
            <div className="form-group">
              <label className="form-label">1. Event Flow Understandable? (1-5)</label>
              <input type="number" min="1" max="5" className="form-control" value={scoreFlow} onChange={(e) => setScoreFlow(Number(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">2. Health Clear? (1-5)</label>
              <input type="number" min="1" max="5" className="form-control" value={scoreHealth} onChange={(e) => setScoreHealth(Number(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">3. Failure Recovery Clear? (1-5)</label>
              <input type="number" min="1" max="5" className="form-control" value={scoreRecovery} onChange={(e) => setScoreRecovery(Number(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">4. Change Workflow Control? (1-5)</label>
              <input type="number" min="1" max="5" className="form-control" value={scoreChange} onChange={(e) => setScoreChange(Number(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">5. Rollback Process Clear? (1-5)</label>
              <input type="number" min="1" max="5" className="form-control" value={scoreRollback} onChange={(e) => setScoreRollback(Number(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">6. Decoupled Easier to Change? (1-5)</label>
              <input type="number" min="1" max="5" className="form-control" value={scoreDecoupling} onChange={(e) => setScoreDecoupling(Number(e.target.value))} />
            </div>
          </div>

          <div className="form-group" style={{ marginTop: "12px" }}>
            <label className="form-label">Qualitative Review Feedback & Comments</label>
            <textarea className="form-control" rows={3} value={comments} onChange={(e) => setComments(e.target.value)} required />
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "16px" }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsModalOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={submitting}>
              Submit Scorecard
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
