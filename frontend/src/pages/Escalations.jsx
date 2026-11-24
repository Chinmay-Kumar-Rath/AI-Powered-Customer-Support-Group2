import React, { useCallback, useEffect, useState } from "react";
import { escalationApi, api } from "../api";

const styles = {
  page: { padding: "28px", color: "var(--text-primary, #172554)" },
  heading: { display: "flex", justifyContent: "space-between", alignItems: "center", gap: "16px", flexWrap: "wrap", marginBottom: "22px" },
  button: { border: 0, borderRadius: "9px", padding: "10px 15px", background: "#4f46e5", color: "white", fontWeight: 600, cursor: "pointer" },
  card: { background: "var(--card-bg, white)", border: "1px solid var(--border, #e2e8f0)", borderRadius: "14px", padding: "18px", marginBottom: "14px", boxShadow: "0 5px 18px rgba(30,41,59,.05)" },
  muted: { color: "var(--text-secondary, #64748b)", fontSize: "13px" },
  select: { padding: "9px 12px", border: "1px solid #cbd5e1", borderRadius: "8px", background: "white", color: "#172554" },
  action: { border: "1px solid #c7d2fe", background: "#eef2ff", color: "#3730a3", borderRadius: "8px", padding: "8px 11px", cursor: "pointer", fontWeight: 600 },
};

function statusColor(status) {
  const s = String(status || "").toLowerCase();
  if (s.includes("resolve") || s === "closed") return { background: "#dcfce7", color: "#166534" };
  if (s.includes("progress") || s.includes("accept")) return { background: "#dbeafe", color: "#1d4ed8" };
  return { background: "#fef3c7", color: "#92400e" };
}

export default function Escalations() {
  const [items, setItems] = useState([]);
  const [engineers, setEngineers] = useState([]);
  const [filter, setFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [escalationData, userData] = await Promise.all([
        escalationApi.list({ limit: 500 }),
        api.users({ limit: 500 }),
      ]);
      setItems(Array.isArray(escalationData) ? escalationData : []);
      const list = Array.isArray(userData) ? userData : [];
      setEngineers(list.filter((u) => u.role === "engineer" && u.is_active !== false));
    } catch (e) {
      setError(e.message || "Could not load the escalation queue.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function perform(id, action, callback) {
    setBusy(id);
    setError("");
    setMessage("");
    try {
      await callback();
      setMessage("Escalation updated successfully.");
      await load();
    } catch (e) {
      setError(e.message || "Action failed.");
    } finally {
      setBusy(null);
    }
  }

  const visible = items.filter((item) => {
    if (filter === "all") return true;
    if (filter === "unassigned") return item.assigned_to == null;
    const normalizedStatus = String(item.status || "")
  .trim()
  .toLowerCase()
  .replace(/\s+/g, "_");

return normalizedStatus === filter;
  });

  return (
    <main style={styles.page}>
      <div style={styles.heading}>
        <div>
          <h1 style={{ margin: 0, fontSize: "27px", fontWeight: 800 }}>Escalation Queue</h1>
          <p style={styles.muted}>Review, assign and resolve escalated support tickets.</p>
        </div>
        <button style={styles.button} onClick={load} disabled={loading}>? Refresh queue</button>
      </div>

      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "20px" }}>
        {[
          ["all", "All escalations"],
          ["open", "Open"],
          ["in_progress", "In progress"],
          ["resolved", "Resolved"],
          ["unassigned", "Unassigned"],
        ].map(([value, label]) => (
          <button key={value} onClick={() => setFilter(value)}
            style={{ ...styles.action, background: filter === value ? "#3730a3" : "#eef2ff", color: filter === value ? "white" : "#3730a3" }}>
            {label}
          </button>
        ))}
        <span style={{ ...styles.muted, alignSelf: "center" }}>{visible.length} result(s)</span>
      </div>

      {message && <p role="status" style={{ color: "#15803d" }}>{message}</p>}
      {error && <p role="alert" style={{ color: "#b91c1c", background: "#fef2f2", padding: "12px", borderRadius: "8px" }}>{error}</p>}
      {loading && <p style={styles.muted}>Loading escalation queue...</p>}
      {!loading && visible.length === 0 && (
        <section style={styles.card}><strong>No escalations found.</strong><p style={styles.muted}>Try another filter or refresh the queue.</p></section>
      )}

      {!loading && visible.map((item) => (
        <section key={item.escalation_id} style={styles.card}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
            <div>
              <div style={{ display: "flex", gap: "9px", alignItems: "center", flexWrap: "wrap" }}>
                <strong style={{ fontSize: "17px" }}>{item.ticket_code || `Ticket #${item.ticket_id}`}</strong>
                <span style={{ ...statusColor(item.status), borderRadius: "20px", padding: "4px 10px", fontSize: "12px", fontWeight: 700 }}>{item.status}</span>
              </div>
              <h3 style={{ margin: "9px 0 6px" }}>{item.ticket_subject || "Untitled ticket"}</h3>
              <p style={styles.muted}>{item.ticket_category || "Uncategorised"} · Severity: {item.ticket_severity || "Unknown"} · Priority: {item.ticket_priority || "Unknown"}</p>
            </div>
            <div style={{ textAlign: "right" }}>
              <div style={styles.muted}>Due date</div>
              <strong>{item.due_at ? new Date(item.due_at).toLocaleString() : "Not set"}</strong>
            </div>
          </div>

          <div style={{ margin: "14px 0", padding: "12px", borderRadius: "9px", background: "#f8fafc" }}>
            <div style={styles.muted}>Escalation reason</div>
            <div>{item.escalation_reason || "No reason provided."}</div>
          </div>

          <div style={{ display: "flex", gap: "18px", flexWrap: "wrap", marginBottom: "15px" }}>
            <span style={styles.muted}>Team: <strong>{item.assigned_team || "Unassigned"}</strong></span>
            <span style={styles.muted}>Engineer: <strong>{item.assignee_name || "Unassigned"}</strong></span>
            <span style={styles.muted}>Created: <strong>{item.created_at ? new Date(item.created_at).toLocaleString() : "Unknown"}</strong></span>
          </div>

          {item.resolution_notes && <p style={styles.muted}>Resolution: {item.resolution_notes}</p>}

          <div style={{ display: "flex", gap: "9px", flexWrap: "wrap", borderTop: "1px solid #e2e8f0", paddingTop: "14px" }}>
            {String(item.status).toLowerCase() !== "resolved" && (
              <>
                <button style={styles.action} disabled={busy === item.escalation_id}
                  onClick={() => perform(item.escalation_id, "accept", () => escalationApi.accept(item.escalation_id))}>
                  Accept
                </button>

                <button style={styles.action} disabled={busy === item.escalation_id}
                  onClick={() => {
                    const choice = window.prompt(
                      "Enter the engineer's user ID:\n" + engineers.map((u) => `${u.user_id}: ${u.name} (${u.email})`).join("\n")
                    );
                    if (choice && Number.isInteger(Number(choice)) && Number(choice) > 0) {
                      perform(item.escalation_id, "assign", () => escalationApi.assign(item.escalation_id, Number(choice)));
                    } else if (choice) {
                      setError("Please enter a valid engineer user ID.");
                    }
                  }}>
                  Assign engineer
                </button>

                <button style={styles.action} disabled={busy === item.escalation_id}
                  onClick={() => {
                    const note = window.prompt("Enter an internal note:");
                    if (note && note.trim()) perform(item.escalation_id, "note", () => escalationApi.addNote(item.escalation_id, note.trim(), false));
                  }}>
                  Add internal note
                </button>

                <button style={{ ...styles.action, background: "#ecfdf5", color: "#047857", borderColor: "#a7f3d0" }}
                  disabled={busy === item.escalation_id}
                  onClick={() => {
                    const notes = window.prompt("Describe how the issue was resolved (at least 3 characters):");
                    if (notes && notes.trim().length >= 3) perform(item.escalation_id, "resolve", () => escalationApi.resolve(item.escalation_id, notes.trim()));
                    else if (notes) setError("Please enter at least 3 characters describing the resolution.");
                  }}>
                  Resolve
                </button>
              </>
            )}
            {busy === item.escalation_id && <span style={styles.muted}>Updating...</span>}
          </div>
        </section>
      ))}
    </main>
  );
}


