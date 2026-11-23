

// import React from "react";
// import "./admin.css";

// const AdminDashboard = ({ stats = null, ragStats = null, loading = false, error = "" }) => {
//   const escalation = stats?.escalations || {};
//   const feedback = stats?.feedback || {};

//   const cards = [
//     {
//       label: "Total Tickets",
//       value: stats?.total_tickets ?? "—",
//       detail: `${stats?.tickets_today ?? "—"} created today`,
//       icon: "🎫",
//       color: "violet",
//     },
//     {
//       label: "Open Escalations",
//       value: escalation.open ?? "—",
//       detail: `${escalation.unassigned ?? "—"} unassigned`,
//       icon: "⚡",
//       color: "orange",
//     },
//     {
//       label: "SLA Breaches",
//       value: escalation.sla_breached ?? "—",
//       detail: "Require attention",
//       icon: "⏱️",
//       color: "rose",
//     },
//     {
//       label: "Customer Satisfaction",
//       value:
//         feedback.satisfaction_pct != null
//           ? `${feedback.satisfaction_pct}%`
//           : "—",
//       detail:
//         feedback.avg_rating != null
//           ? `${feedback.avg_rating} / 5 average rating`
//           : "Awaiting feedback",
//       icon: "⭐",
//       color: "teal",
//     },
//   ];

//   return (
//     <main className="admin-dashboard">
//       <header className="admin-header">
//         <div>
//           <p className="admin-eyebrow">ADMINISTRATION</p>
//           <h1>Admin Dashboard</h1>
//           <p className="admin-subtitle">
//             Monitor support operations and manage customer issues.
//           </p>
//         </div>
//         <span className="admin-live-label">
//           <span className="admin-status-dot" />
//           Operations overview
//         </span>
//       </header>

//       {error && (
//         <div className="admin-error" role="alert">
//           {error}
//         </div>
//       )}

//       {loading && (
//         <p className="admin-loading">Loading dashboard statistics...</p>
//       )}

//       <section className="admin-stats-grid">
//         {cards.map((card) => (
//           <article className="admin-stat-card" key={card.label}>
//             <div className="admin-stat-top">
//               <span>{card.label}</span>
//               <span className={`admin-stat-icon ${card.color}`}>
//                 {card.icon}
//               </span>
//             </div>
//             <h2>{card.value}</h2>
//             <p>{card.detail}</p>
//           </article>
//         ))}
//       </section>

//       <section className="admin-section">
//         <div className="admin-section-heading">
//           <div>
//             <h2>Support Operations</h2>
//             <p>Current ticket and escalation activity</p>
//           </div>
//         </div>

//         <div className="admin-overview-grid">
//           <article className="admin-overview-panel">
//             <div className="admin-panel-heading">
//               <span className="admin-panel-icon violet">📊</span>
//               <h3>Ticket Overview</h3>
//             </div>
//             <div className="admin-metric-row">
//               <span>Total tickets</span>
//               <strong>{stats?.total_tickets ?? "—"}</strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>Created today</span>
//               <strong>{stats?.tickets_today ?? "—"}</strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>Average processing time</span>
//               <strong>
//                 {stats?.avg_processing_ms != null
//                   ? `${stats.avg_processing_ms} ms`
//                   : "—"}
//               </strong>
//             </div>
//           </article>

//           <article className="admin-overview-panel">
//             <div className="admin-panel-heading">
//               <span className="admin-panel-icon orange">🚨</span>
//               <h3>Escalation Monitor</h3>
//             </div>
//             <div className="admin-metric-row">
//               <span>Total escalations</span>
//               <strong>{escalation.total ?? "—"}</strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>Open escalations</span>
//               <strong>{escalation.open ?? "—"}</strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>Unassigned</span>
//               <strong>{escalation.unassigned ?? "—"}</strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>SLA breached</span>
//               <strong className="admin-danger">
//                 {escalation.sla_breached ?? "—"}
//               </strong>
//             </div>
//           </article>

//           <article className="admin-overview-panel">
//             <div className="admin-panel-heading">
//               <span className="admin-panel-icon teal">✨</span>
//               <h3>AI & RAG Performance</h3>
//             </div>
//             <div className="admin-metric-row">
//               <span>Knowledge articles</span>
//               <strong>{ragStats?.kb_articles ?? "—"}</strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>Responses generated</span>
//               <strong>{ragStats?.responses_generated ?? "—"}</strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>Average confidence</span>
//               <strong>
//                 {ragStats?.avg_confidence != null
//                   ? `${(ragStats.avg_confidence * 100).toFixed(1)}%`
//                   : "—"}
//               </strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>Needs human review</span>
//               <strong>
//                 {ragStats?.needs_human_review_pct != null
//                   ? `${ragStats.needs_human_review_pct}%`
//                   : "—"}
//               </strong>
//             </div>
//           </article>

//           <article className="admin-overview-panel">
//             <div className="admin-panel-heading">
//               <span className="admin-panel-icon teal">💬</span>
//               <h3>Customer Feedback</h3>
//             </div>
//             <div className="admin-metric-row">
//               <span>Feedback responses</span>
//               <strong>{feedback.responses ?? "—"}</strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>Issues fixed</span>
//               <strong>
//                 {feedback.fixed_issue_pct != null
//                   ? `${feedback.fixed_issue_pct}%`
//                   : "—"}
//               </strong>
//             </div>
//             <div className="admin-metric-row">
//               <span>Average rating</span>
//               <strong>
//                 {feedback.avg_rating != null
//                   ? `${feedback.avg_rating} / 5`
//                   : "—"}
//               </strong>
//             </div>
//           </article>
//         </div>
//       </section>

//       <footer className="admin-footer">
//         SupportPilot · Administration workspace
//       </footer>
//     </main>
//   );
// };

// export default AdminDashboard;


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
  loading = false,
  error = "",
}) => {
  const escalation = stats?.escalations || {};
  const feedback = stats?.feedback || {};

  const cards = [
    {
      label: "Total Tickets",
      value: stats?.total_tickets ?? "—",
      detail: `${stats?.tickets_today ?? "—"} created today`,
      icon: Ticket,
      color: "violet",
    },
    {
      label: "Open Escalations",
      value: escalation.open ?? "—",
      detail: `${escalation.unassigned ?? "—"} unassigned`,
      icon: Zap,
      color: "orange",
    },
    {
      label: "SLA Breaches",
      value: escalation.sla_breached ?? "—",
      detail: "Require attention",
      icon: Clock,
      color: "rose",
    },
    {
      label: "Customer Satisfaction",
      value:
        feedback.satisfaction_pct != null
          ? `${feedback.satisfaction_pct}%`
          : "—",
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
              <strong>{stats?.total_tickets ?? "—"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Created today</span>
              <strong>{stats?.tickets_today ?? "—"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Average processing time</span>
              <strong>
                {stats?.avg_processing_ms != null
                  ? `${stats.avg_processing_ms} ms`
                  : "—"}
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
              <strong>{escalation.total ?? "—"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Open escalations</span>
              <strong>{escalation.open ?? "—"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Unassigned</span>
              <strong>{escalation.unassigned ?? "—"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>SLA breached</span>
              <strong className="admin-danger">
                {escalation.sla_breached ?? "—"}
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
              <strong>{ragStats?.kb_articles ?? "—"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Responses generated</span>
              <strong>{ragStats?.responses_generated ?? "—"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Average confidence</span>
              <strong>
                {ragStats?.avg_confidence != null
                  ? `${(ragStats.avg_confidence * 100).toFixed(1)}%`
                  : "—"}
              </strong>
            </div>

            <div className="admin-metric-row">
              <span>Needs human review</span>
              <strong>
                {ragStats?.needs_human_review_pct != null
                  ? `${ragStats.needs_human_review_pct}%`
                  : "—"}
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
              <strong>{feedback.responses ?? "—"}</strong>
            </div>

            <div className="admin-metric-row">
              <span>Issues fixed</span>
              <strong>
                {feedback.fixed_issue_pct != null
                  ? `${feedback.fixed_issue_pct}%`
                  : "—"}
              </strong>
            </div>

            <div className="admin-metric-row">
              <span>Average rating</span>
              <strong>
                {feedback.avg_rating != null
                  ? `${feedback.avg_rating} / 5`
                  : "—"}
              </strong>
            </div>
          </article>
        </div>
      </section>

      <footer className="admin-footer">
        SupportPilot · Administration workspace
      </footer>
    </main>
  );
};

export default AdminDashboard;
