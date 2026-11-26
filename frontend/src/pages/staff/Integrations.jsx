import React, { useCallback, useEffect, useState } from "react";
import { api } from "../../api";
import { RefreshCw, Mail, GitBranch, CheckCircle2, AlertCircle, Clock3 } from "lucide-react";

export default function Integrations() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await api.integrationsStatus();
      setData(result);
    } catch (err) {
      setError(err.message || "Could not load integration status.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const installed = value => value === "integrations-package";
  const date = value => value ? new Date(value).toLocaleString() : "No activity recorded";

  const Status = ({ active }) => (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 6,
      padding: "6px 11px", borderRadius: 20, fontSize: 12, fontWeight: 700,
      color: active ? "#087a55" : "#a34b25",
      background: active ? "#dcfce9" : "#fff0df"
    }}>
      {active ? <CheckCircle2 size={14}/> : <AlertCircle size={14}/>}
      {active ? "Module installed" : "Not installed"}
    </span>
  );

  const card = {
    background: "#fff", border: "1px solid #e8e2f5", borderRadius: 18,
    padding: 22, boxShadow: "0 8px 24px rgba(48,31,91,.06)"
  };

  const metric = (label, value, color) => (
    <div style={{background: "#f7f4ff", borderRadius: 13, padding: 15}}>
      <div style={{fontSize: 12, color: "#746b89", marginBottom: 7}}>{label}</div>
      <div style={{fontSize: 25, fontWeight: 800, color: color || "#34215f"}}>{value ?? 0}</div>
    </div>
  );

  return (
    <div style={{padding: 26, maxWidth: 1200, margin: "0 auto", color: "#281b49"}}>
      <div style={{display: "flex", justifyContent: "space-between", alignItems: "center", gap: 15, flexWrap: "wrap", marginBottom: 24}}>
        <div>
          <h1 style={{fontSize: 27, fontWeight: 800, margin: 0}}>Integrations</h1>
          <p style={{color: "#766b8d", marginTop: 7}}>Monitor Jira synchronization and email activity.</p>
        </div>
        <button onClick={load} disabled={loading} style={{
          display: "flex", alignItems: "center", gap: 8, border: 0,
          borderRadius: 11, padding: "11px 16px", color: "#fff",
          background: "linear-gradient(135deg,#673ab7,#39206f)",
          cursor: "pointer", fontWeight: 700
        }}><RefreshCw size={16}/> Refresh</button>
      </div>

      {loading && <p>Loading integration information...</p>}
      {error && <div style={{...card, color: "#a34b25", marginBottom: 18}}>{error}</div>}

      {data && <>
        <div style={{display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(280px,1fr))", gap: 18}}>
          <section style={card}>
            <div style={{display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap"}}>
              <div style={{display: "flex", alignItems: "center", gap: 10}}>
                <GitBranch size={23} color="#673ab7"/>
                <h2 style={{fontSize: 19, margin: 0}}>Jira</h2>
              </div>
              <Status active={installed(data.modules?.jira)}/>
            </div>
            <p style={{color: "#766b8d", fontSize: 13, marginTop: 17}}>Recorded Jira synchronization activity</p>
            <div style={{fontSize: 30, fontWeight: 800, marginTop: 8}}>{data.jira?.records ?? 0}</div>
            <div style={{fontSize: 12, color: "#766b8d"}}>Jira records</div>
            <div style={{marginTop: 18, fontSize: 13, color: "#51466a"}}>
              <div>Latest issue: <b>{data.jira?.latest_issue || "None recorded"}</b></div>
              <div style={{marginTop: 8, display: "flex", gap: 7, alignItems: "center"}}>
                <Clock3 size={14}/> Last recorded sync: {date(data.jira?.last_sync)}
              </div>
            </div>
          </section>

          <section style={card}>
            <div style={{display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap"}}>
              <div style={{display: "flex", alignItems: "center", gap: 10}}>
                <Mail size={23} color="#087e91"/>
                <h2 style={{fontSize: 19, margin: 0}}>Email notifications</h2>
              </div>
              <Status active={installed(data.modules?.notifications)}/>
            </div>
            <p style={{color: "#766b8d", fontSize: 13, marginTop: 17}}>Recorded email activity</p>
            <div style={{display: "grid", gridTemplateColumns: "repeat(2,minmax(0,1fr))", gap: 10, marginTop: 15}}>
              {metric("Total", data.email?.total)}
              {metric("Sent", data.email?.sent, "#087a55")}
              {metric("Failed", data.email?.failed, "#bd4b4b")}
              {metric("Dry run", data.email?.dry_run, "#9a6812")}
            </div>
            <div style={{marginTop: 17, fontSize: 13, color: "#51466a", display: "flex", gap: 7, alignItems: "center"}}>
              <Clock3 size={14}/> Last activity: {date(data.email?.last_activity)}
            </div>
          </section>
        </div>
        <p style={{fontSize: 12, color: "#766b8d", marginTop: 18}}>
          Status reflects whether integration modules are installed. Activity counts come from stored database records; they do not independently verify external service connectivity or successful delivery.
        </p>
      </>}
    </div>
  );
}


