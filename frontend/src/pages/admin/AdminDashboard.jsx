

import React from "react";
import {
  Ticket,
  Zap,
  Clock,
  Star,
  ChartColumn,
  Siren,
  Sparkles,
  MessageCircle,
} from "lucide-react";
import "./admin.css";

const AdminDashboard = ({
  stats = null,
  ragStats = null,
  users = [],
  tickets = [],
  loading = false,
  error = "",
}) => {
  const escalation = stats?.escalations || {};
  const feedback = stats?.feedback || {};

  const cards = [
    {
      label: "Total Tickets",
      value: stats?.total_tickets ?? "â€”",
      detail: `${stats?.tickets_today ?? "â€”"} created today`,
      icon: Ticket,
      color: "violet",
    },
    {
      label: "Open Escalations",
      value: escalation.open ?? "â€”",
      detail: `${escalation.unassigned ?? "â€”"} unassigned`,
      icon: Zap,
      color: "orange",
    },
    {
      label: "SLA Breaches",
      value: escalation.sla_breached ?? "â€”",
      detail: "Require attention",
      icon: Clock,
      color: "rose",
    },
    {
      label: "Customer Satisfaction",
      value:
        feedback.satisfaction_pct != null
          ? `${feedback.satisfaction_pct}%`
          : "â€”",
      detail:
        feedback.avg_rating != null
          ? `${feedback.avg_rating} / 5 average rating`
          : "Awaiting feedback",
      icon: Star,
      color: "teal",
    },
  ];

  return (
    <main className="admin-dashboard">
      <header className="admin-header">
        <div>
          <p className="admin-eyebrow">ADMINISTRATION</p>
          <h1>Admin Dashboard</h1>
          <p className="admin-subtitle">
            Monitor support operations and manage customer issues.
          </p>
        </div>

        <span className="admin-live-label">
          <span className="admin-status-dot" />
          Operations overview
        </span>
      </header>

      {error && (
        <div className="admin-error" role="alert">
          {error}
        </div>
      )}

      {loading && (
        <p className="admin-loading">
          Loading dashboard statistics...
        </p>
      )}

      <section className="admin-stats-grid">
        {cards.map((card) => {
          const Icon = card.icon;

          return (
            <article className="admin-stat-card" key={card.label}>
              <div className="admin-stat-top">
                <span>{card.label}</span>

                <span className={`admin-stat-icon ${card.color}`}>
                  <Icon size={20} strokeWidth={2.2} />
                </span>
              </div>

              <h2>{card.value}</h2>
              <p>{card.detail}</p>
            </article>
          );
        })}
      </section>

      <section className="admin-section">
        <div className="admin-section-heading">
          <div>
            <h2>Support Operations</h2>
            <p>Current ticket and escalation activity</p>
          </div>
        </div>

        <div className="admin-overview-grid">
          <article className="admin-overview-panel">
            <div className="admin-panel-heading">
              <span className="admin-panel-icon violet">
                <ChartColumn size={20} strokeWidth={2.2} />
              </span>
              <h3>Ticket Overview</h3>
            </div>

            <div className="admin-metric-row">
              <span>Total tickets</span>
              <strong>{stats?.total_tickets ?? "â€”"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Created today</span>
              <strong>{stats?.tickets_today ?? "â€”"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Average processing time</span>
              <strong>
                {stats?.avg_processing_ms != null
                  ? `${stats.avg_processing_ms} ms`
                  : "â€”"}
              </strong>
            </div>
          </article>

          <article className="admin-overview-panel">
            <div className="admin-panel-heading">
              <span className="admin-panel-icon orange">
                <Siren size={20} strokeWidth={2.2} />
              </span>
              <h3>Escalation Monitor</h3>
            </div>

            <div className="admin-metric-row">
              <span>Total escalations</span>
              <strong>{escalation.total ?? "â€”"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Open escalations</span>
              <strong>{escalation.open ?? "â€”"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Unassigned</span>
              <strong>{escalation.unassigned ?? "â€”"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>SLA breached</span>
              <strong className="admin-danger">
                {escalation.sla_breached ?? "â€”"}
              </strong>
            </div>
          </article>

          <article className="admin-overview-panel">
            <div className="admin-panel-heading">
              <span className="admin-panel-icon teal">
                <Sparkles size={20} strokeWidth={2.2} />
              </span>
              <h3>AI & RAG Performance</h3>
            </div>

            <div className="admin-metric-row">
              <span>Knowledge articles</span>
              <strong>{ragStats?.kb_articles ?? "â€”"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Responses generated</span>
              <strong>{ragStats?.responses_generated ?? "â€”"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Average confidence</span>
              <strong>
                {ragStats?.avg_confidence != null
                  ? `${(ragStats.avg_confidence * 100).toFixed(1)}%`
                  : "â€”"}
              </strong>
            </div>

            <div className="admin-metric-row">
              <span>Needs human review</span>
              <strong>
                {ragStats?.needs_human_review_pct != null
                  ? `${ragStats.needs_human_review_pct}%`
                  : "â€”"}
              </strong>
            </div>
          </article>

          <article className="admin-overview-panel">
            <div className="admin-panel-heading">
              <span className="admin-panel-icon teal">
                <MessageCircle size={20} strokeWidth={2.2} />
              </span>
              <h3>Customer Feedback</h3>
            </div>

            <div className="admin-metric-row">
              <span>Feedback responses</span>
              <strong>{feedback.responses ?? "â€”"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Issues fixed</span>
              <strong>
                {feedback.fixed_issue_pct != null
                  ? `${feedback.fixed_issue_pct}%`
                  : "â€”"}
              </strong>
            </div>

            <div className="admin-metric-row">
              <span>Average rating</span>
              <strong>
                {feedback.avg_rating != null
                  ? `${feedback.avg_rating} / 5`
                  : "â€”"}
              </strong>
            </div>
          </article>
        </div>
      </section>

      <section className="admin-section">
        <div className="admin-section-heading">
          <div>
            <h2>Engineer Workload</h2>
            <p>Assigned tickets and active workload by engineer</p>
          </div>
        </div>
        <div className="admin-overview-grid">
          {users.filter((u) => u.role === "engineer" && u.is_active !== false).map((engineer) => {
            const assigned = tickets.filter((t) => Number(t.assigned_to) === Number(engineer.user_id));
            const active = assigned.filter((t) => !["resolved", "closed"].includes(String(t.status || "").toLowerCase()));
            return (
              <article className="admin-overview-panel" key={engineer.user_id}>
                <div className="admin-panel-heading">
                  <span className="admin-panel-icon violet"><Ticket size={20} /></span>
                  <h3>{engineer.name || engineer.email}</h3>
                </div>
                <div className="admin-metric-row">
                  <span>Team</span><strong>{engineer.team || "Not assigned"}</strong>
                </div>
                <div className="admin-metric-row">
                  <span>Total assigned</span><strong>{assigned.length}</strong>
                </div>
                <div className="admin-metric-row">
                  <span>Active tickets</span><strong>{active.length}</strong>
                </div>
                <div style={{ height: "7px", background: "#e2e8f0", borderRadius: "10px", overflow: "hidden", marginTop: "14px" }}>
                  <div style={{ height: "100%", width: `${assigned.length ? Math.min(100, active.length / assigned.length * 100) : 0}%`, background: "linear-gradient(90deg,#6366f1,#a855f7)", borderRadius: "10px" }} />
                </div>
              </article>
            );
          })}
          {users.filter((u) => u.role === "engineer" && u.is_active !== false).length === 0 && (
            <article className="admin-overview-panel">
              <p>No engineer records are currently available.</p>
            </article>
          )}
        </div>
      </section>
      <footer className="admin-footer">
        SupportPilot Â· Administration workspace
      </footer>
    </main>
  );
};

export default AdminDashboard;

