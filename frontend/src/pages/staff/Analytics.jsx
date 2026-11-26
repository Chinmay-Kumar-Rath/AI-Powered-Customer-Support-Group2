import React, { useEffect, useMemo, useState } from "react";
import { api } from "../../api";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import {
  BarChart3, Ticket, CheckCircle2, Clock3, Users,
  RefreshCw, Download, TrendingUp, AlertTriangle
} from "lucide-react";

const colors = {
  ink: "#211747", muted: "#77718f", purple: "#7048e8",
  blue: "#3985ed", teal: "#13a995", orange: "#f39b42",
  red: "#e45d76", border: "#eeeaf7", panel: "#ffffff",
  background: "#f7f5fc"
};

const card = {
  background: colors.panel, border: `1px solid ${colors.border}`,
  borderRadius: 18, padding: 20, boxShadow: "0 5px 22px rgba(48,30,90,.045)"
};

const number = value => Number(value || 0).toLocaleString();
const dateKey = value => {
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? "" :
    `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
};

function BarList({ data, color = colors.purple }) {
  const entries = Object.entries(data || {}).sort((a,b) => Number(b[1])-Number(a[1]));
  if (!entries.length) return <p style={{color:colors.muted}}>No data available yet.</p>;
  const max = Math.max(...entries.map(([,v]) => Number(v)||0), 1);
  return <div style={{display:"grid",gap:15}}>
    {entries.map(([name,value]) => <div key={name}>
      <div style={{display:"flex",justifyContent:"space-between",fontSize:13,marginBottom:7}}>
        <span style={{color:colors.ink,fontWeight:600}}>{name || "Unclassified"}</span>
        <b style={{color:colors.ink}}>{number(value)}</b>
      </div>
      <div style={{height:9,background:"#f0edf8",borderRadius:20,overflow:"hidden"}}>
        <div style={{height:"100%",width:`${Math.max(0,(Number(value)||0)/max*100)}%`,background:color,borderRadius:20}}/>
      </div>
    </div>)}
  </div>;
}

function Metric({label,value,detail,Icon,color}) {
  return <div style={{...card,minWidth:0}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:10}}>
      <span style={{fontSize:13,color:colors.muted,fontWeight:600}}>{label}</span>
      <span style={{width:39,height:39,borderRadius:12,background:`${color}18`,color,display:"grid",placeItems:"center"}}>
        <Icon size={19}/>
      </span>
    </div>
    <div style={{fontSize:29,fontWeight:800,color:colors.ink,marginTop:13}}>{value}</div>
    <div style={{fontSize:12,color:colors.muted,marginTop:5}}>{detail}</div>
  </div>;
}

export default function Analytics() {
  const { user } = useAuth();
  const [stats,setStats] = useState(null);
  const [tickets,setTickets] = useState([]);
  const [users,setUsers] = useState([]);
  const [rag,setRag] = useState(null);
  const [loading,setLoading] = useState(true);
  const [error,setError] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    const results = await Promise.allSettled([
      api.stats(), api.tickets({limit:500}), user?.role === "admin" ? api.users({limit:500}) : Promise.resolve([]), api.ragStats()
    ]);
    if (results[0].status === "fulfilled") setStats(results[0].value);
    else setError(results[0].reason?.message || "Could not load statistics.");
    if (results[1].status === "fulfilled") setTickets(Array.isArray(results[1].value)?results[1].value:[]);
    if (results[2].status === "fulfilled") setUsers(Array.isArray(results[2].value)?results[2].value:[]);
    if (results[3].status === "fulfilled") setRag(results[3].value);
    setLoading(false);
  };

  useEffect(() => { load(); }, [user?.role]);

  const analytics = useMemo(() => {
    const normalized = tickets.map(t => ({
      ...t,
      state: String(t.status || "").toLowerCase()
    }));
    const isResolved = t => ["resolved","closed"].includes(t.state) || !!t.resolved_at || !!t.closed_at;
    const resolved = normalized.filter(isResolved).length;
    const open = normalized.filter(t => !isResolved(t)).length;
    const category = stats?.by_category || normalized.reduce((a,t) => {
      const key = t.category || "Unclassified";
      a[key] = (a[key] || 0)+1;
      return a;
    }, {});
    const status = stats?.by_status || normalized.reduce((a,t) => {
      const key = t.status || "Unknown";
      a[key] = (a[key] || 0)+1;
      return a;
    }, {});
    const today = new Date();
    const trend = Array.from({length:7},(_,i) => {
      const d = new Date(today);
      d.setDate(today.getDate()-(6-i));
      const key = dateKey(d);
      return {label:d.toLocaleDateString(undefined,{weekday:"short"}),count:normalized.filter(t=>dateKey(t.created_at)===key).length};
    });
    const maxTrend = Math.max(...trend.map(x=>x.count),1);
    const engineers = users.filter(u=>u.role==="engineer" && u.is_active!==false).map(u=>{
      const assigned = normalized.filter(t=>String(t.assigned_to)===String(u.user_id));
      const active = assigned.filter(t=>!isResolved(t));
      return {name:u.name || u.email || `Engineer ${u.user_id}`,team:u.team || u.department || "—",total:assigned.length,active:active.length};
    }).sort((a,b)=>b.active-a.active);
    return {resolved,open,rate:normalized.length?Math.round(resolved/normalized.length*100):0,category,status,trend,maxTrend,engineers};
  },[tickets,users,stats]);

  const exportCsv = () => {
    const rows = [["Ticket ID","Ticket Code","Subject","Category","Severity","Priority","Status","Assigned To","Created At"]];
    tickets.forEach(t=>rows.push([t.ticket_id,t.ticket_code,t.subject,t.category,t.severity,t.priority,t.status,t.assignee_name,t.created_at]));
    const csv = rows.map(row=>row.map(v=>`"${String(v ?? "").replace(/"/g,'""')}"`).join(",")).join("\r\n");
    const blob = new Blob([csv],{type:"text/csv;charset=utf-8;"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href=url; a.download="supportpilot-analytics-tickets.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  const total = stats?.total_tickets ?? tickets.length;
  const avg = stats?.avg_processing_ms;
  const confidence = rag?.avg_confidence;

  return <div style={{padding:"28px 30px",background:colors.background,minHeight:"100%",color:colors.ink}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:15,flexWrap:"wrap",marginBottom:24}}>
      <div>
        <div style={{fontSize:12,fontWeight:800,color:colors.purple,letterSpacing:1.5}}>INSIGHTS & REPORTING</div>
        <h1 style={{fontSize:28,margin:"7px 0 5px",fontWeight:800}}>Analytics Overview</h1>
        <p style={{margin:0,color:colors.muted,fontSize:14}}>Understand ticket trends, resolutions and team workload.</p>
      </div>
      <div style={{display:"flex",gap:9}}>
        <button onClick={load} disabled={loading} style={{border:`1px solid ${colors.border}`,background:"#fff",padding:"11px 14px",borderRadius:11,color:colors.ink,cursor:"pointer",display:"flex",alignItems:"center",gap:7}}>
          <RefreshCw size={16}/> Refresh
        </button>
        <button onClick={exportCsv} style={{border:0,background:colors.purple,padding:"11px 15px",borderRadius:11,color:"#fff",fontWeight:700,cursor:"pointer",display:"flex",alignItems:"center",gap:7}}>
          <Download size={16}/> Export CSV
        </button>
      </div>
    </div>

    <section style={{marginBottom:20}}>
      <h2 style={{fontSize:18,color:colors.ink,margin:"0 0 13px"}}>Detailed Analytics Reports</h2>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(210px,1fr))",gap:13}}>
        {[
          {title:"Escalation Analytics",description:"Explore escalation trends, teams and outcomes.",path:"/admin/analytics/escalations",Icon:AlertTriangle,color:colors.purple},
          {title:"Agent Performance",description:"Review agent runs, execution time and confidence.",path:"/admin/analytics/agents",Icon:Users,color:colors.blue},
          {title:"Customer Satisfaction",description:"Track feedback, ratings and satisfaction trends.",path:"/admin/analytics/satisfaction",Icon:CheckCircle2,color:colors.teal},
          {title:"Recurring Issues",description:"Identify repeated issues and emerging patterns.",path:"/admin/analytics/recurring-issues",Icon:TrendingUp,color:colors.orange}
        ].map(item => (
          <Link key={item.path} to={item.path} style={{...card,textDecoration:"none",display:"flex",alignItems:"flex-start",gap:13,transition:"transform .2s",color:colors.ink}}>
            <span style={{width:42,height:42,flexShrink:0,borderRadius:12,background:`${item.color}18`,color:item.color,display:"grid",placeItems:"center"}}>
              <item.Icon size={21}/>
            </span>
            <span>
              <strong style={{display:"block",fontSize:14,marginBottom:5}}>{item.title}</strong>
              <span style={{fontSize:12,color:colors.muted,lineHeight:1.5}}>{item.description}</span>
            </span>
          </Link>
        ))}
      </div>
    </section>

    {error && <div style={{...card,marginBottom:18,color:colors.red}}>Statistics error: {error}</div>}
    {loading && <div style={{...card,marginBottom:18,color:colors.muted}}>Loading analytics data…</div>}

    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(190px,1fr))",gap:15,marginBottom:20}}>
      <Metric label="Total Tickets" value={number(total)} detail="All tickets recorded" Icon={Ticket} color={colors.purple}/>
      <Metric label="Resolved Tickets" value={number(analytics.resolved)} detail={`${analytics.rate}% of loaded tickets resolved`} Icon={CheckCircle2} color={colors.teal}/>
      <Metric label="Active Tickets" value={number(analytics.open)} detail="Not yet resolved or closed" Icon={Clock3} color={colors.orange}/>
      <Metric label="Avg. Processing Time" value={avg==null?"—":`${(Number(avg)/1000).toFixed(2)}s`} detail="Ticket classification processing" Icon={TrendingUp} color={colors.blue}/>
    </div>

    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(min(100%,390px),1fr))",gap:18,marginBottom:18}}>
      <section style={card}>
        <h3 style={{margin:"0 0 5px",fontSize:17}}>Ticket Volume — Last 7 Days</h3>
        <p style={{margin:"0 0 22px",fontSize:12,color:colors.muted}}>Based on the latest tickets returned by the API</p>
        <div style={{height:175,display:"flex",alignItems:"end",gap:12}}>
          {analytics.trend.map(day=><div key={day.label+day.count} style={{flex:1,height:"100%",display:"flex",flexDirection:"column",justifyContent:"end",alignItems:"center",gap:8}}>
            <b style={{fontSize:12,color:colors.ink}}>{day.count}</b>
            <div style={{width:"100%",height:`${Math.max(5,day.count/analytics.maxTrend*125)}px`,background:`linear-gradient(180deg,${colors.blue},${colors.purple})`,borderRadius:"8px 8px 3px 3px"}}/>
            <span style={{fontSize:11,color:colors.muted}}>{day.label}</span>
          </div>)}
        </div>
      </section>
      <section style={card}>
        <h3 style={{margin:"0 0 5px",fontSize:17}}>Ticket Categories</h3>
        <p style={{margin:"0 0 20px",fontSize:12,color:colors.muted}}>Distribution across recorded categories</p>
        <BarList data={analytics.category} color={colors.purple}/>
      </section>
    </div>

    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(min(100%,300px),1fr))",gap:18,marginBottom:18}}>
      <section style={card}>
        <h3 style={{margin:"0 0 18px",fontSize:17}}>Ticket Status</h3>
        <BarList data={analytics.status} color={colors.teal}/>
      </section>
      <section style={card}>
        <h3 style={{margin:"0 0 18px",fontSize:17}}>AI & RAG Performance</h3>
        <div style={{display:"grid",gap:16}}>
          <div><span style={{fontSize:13,color:colors.muted}}>Knowledge base articles</span><div style={{fontSize:25,fontWeight:800,marginTop:4}}>{number(rag?.kb_articles)}</div></div>
          <div><span style={{fontSize:13,color:colors.muted}}>Responses generated</span><div style={{fontSize:25,fontWeight:800,marginTop:4}}>{number(rag?.responses_generated)}</div></div>
          <div><span style={{fontSize:13,color:colors.muted}}>Average confidence</span><div style={{fontSize:25,fontWeight:800,marginTop:4}}>{confidence==null?"—":`${(Number(confidence)*100).toFixed(1)}%`}</div></div>
          <div><span style={{fontSize:13,color:colors.muted}}>Needs human review</span><div style={{fontSize:25,fontWeight:800,marginTop:4}}>{rag?.needs_human_review_pct==null?"—":`${rag.needs_human_review_pct}%`}</div></div>
        </div>
      </section>
    </div>

    {user?.role === "admin" && (
    <section style={card}>
      <div style={{display:"flex",alignItems:"center",gap:9,marginBottom:15}}>
        <Users size={19} color={colors.purple}/>
        <h3 style={{margin:0,fontSize:17}}>Engineer Performance</h3>
      </div>
      {analytics.engineers.length===0 ? <p style={{color:colors.muted,fontSize:13}}>No engineer assignment data available.</p> :
        <div style={{overflowX:"auto"}}>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
            <thead><tr style={{textAlign:"left",color:colors.muted,borderBottom:`1px solid ${colors.border}`}}>
              <th style={{padding:"11px 8px"}}>Engineer</th><th style={{padding:"11px 8px"}}>Team</th><th style={{padding:"11px 8px"}}>Assigned</th><th style={{padding:"11px 8px"}}>Active</th>
            </tr></thead>
            <tbody>{analytics.engineers.map((e,i)=><tr key={e.name+i} style={{borderBottom:`1px solid ${colors.border}`}}>
              <td style={{padding:"13px 8px",fontWeight:700}}>{e.name}</td><td style={{padding:"13px 8px",color:colors.muted}}>{e.team}</td><td style={{padding:"13px 8px"}}>{e.total}</td><td style={{padding:"13px 8px",fontWeight:700,color:e.active?colors.orange:colors.teal}}>{e.active}</td>
            </tr>)}</tbody>
          </table>
        </div>}
    </section>
    )}

    <p style={{fontSize:11,color:colors.muted,marginTop:15}}>
      Analytics are calculated from the statistics endpoint and up to 500 tickets visible to the signed-in staff member. Daily trends and engineer figures reflect those returned records, not a complete historical audit.
    </p>
  </div>;
}


