import React, { useEffect, useMemo, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  Activity, ShieldAlert, Bot, Star, Repeat2, RefreshCw,
  TrendingUp, Clock3, CheckCircle2, AlertCircle, BarChart3
} from 'lucide-react';
import { analyticsApi } from '../../api';

const C = {
  ink: '#211747', muted: '#77718f', purple: '#7048e8',
  blue: '#3985ed', teal: '#13a995', orange: '#f39b42',
  red: '#e45d76', border: '#eeeaf7', bg: '#f7f5fc',
  white: '#ffffff'
};

const reports = [
  { path: '/admin/analytics/escalations', label: 'Escalations', icon: ShieldAlert },
  { path: '/admin/analytics/agents', label: 'Agent performance', icon: Bot },
  { path: '/admin/analytics/satisfaction', label: 'Satisfaction', icon: Star },
  { path: '/admin/analytics/recurring-issues', label: 'Recurring issues', icon: Repeat2 }
];

const titles = {
  escalations: ['Escalation analytics', 'Monitor escalation volume, ownership and resolution times.'],
  agents: ['Agent performance', 'Review execution volume, success rates, confidence and speed.'],
  satisfaction: ['Customer satisfaction', 'Understand feedback, customer ratings and resolution outcomes.'],
  'recurring-issues': ['Recurring issues', 'Identify repeated issue patterns and their current status.']
};

const panel = {
  background: C.white, border: `1px solid ${C.border}`, borderRadius: 16,
  padding: 20, boxShadow: '0 5px 20px rgba(45, 28, 90, .035)'
};

function Metric({ label, value, note, icon: Icon, color = C.purple }) {
  return <div style={{ ...panel, minWidth: 0 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <span style={{ color: C.muted, fontSize: 13, fontWeight: 600 }}>{label}</span>
      <span style={{ width: 36, height: 36, borderRadius: 11, background: `${color}16`, color, display: 'grid', placeItems: 'center' }}>
        <Icon size={18} />
      </span>
    </div>
    <div style={{ color: C.ink, fontSize: 27, fontWeight: 800, marginTop: 13 }}>{value ?? '?'}</div>
    {note && <div style={{ color: C.muted, fontSize: 12, marginTop: 5 }}>{note}</div>}
  </div>;
}

function Panel({ title, children, empty, count }) {
  return <section style={panel}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 17, gap: 12 }}>
      <h3 style={{ margin: 0, color: C.ink, fontSize: 16 }}>{title}</h3>
      {count !== undefined && <span style={{ color: C.muted, fontSize: 12 }}>{count}</span>}
    </div>
    {empty ? <div style={{ padding: '28px 10px', textAlign: 'center', color: C.muted, fontSize: 13 }}>No records available yet.</div> : children}
  </section>;
}

function Bars({ items, nameKey, valueKey, color = C.purple }) {
  const max = Math.max(1, ...items.map(x => Number(x[valueKey] || 0)));
  if (!items.length) return <div style={{ color: C.muted, padding: 20, textAlign: 'center' }}>No data available yet.</div>;
  return <div style={{ display: 'grid', gap: 14 }}>
    {items.map((item, i) => <div key={`${item[nameKey]}-${i}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, fontSize: 13, marginBottom: 6 }}>
        <span style={{ color: C.ink, fontWeight: 600, overflowWrap: 'anywhere' }}>{item[nameKey]}</span>
        <strong style={{ color: C.ink }}>{item[valueKey]}</strong>
      </div>
      <div style={{ height: 9, background: '#f0edf8', borderRadius: 20, overflow: 'hidden' }}>
        <div style={{ width: `${Math.max(2, Number(item[valueKey] || 0) / max * 100)}%`, height: '100%', background: color, borderRadius: 20 }} />
      </div>
    </div>)}
  </div>;
}

function DataTable({ columns, rows, emptyText = 'No records available yet.' }) {
  if (!rows?.length) return <div style={{ color: C.muted, textAlign: 'center', padding: 25, fontSize: 13 }}>{emptyText}</div>;
  return <div style={{ overflowX: 'auto' }}>
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, minWidth: 560 }}>
      <thead><tr>{columns.map(c => <th key={c.key} style={{ textAlign: 'left', color: C.muted, fontWeight: 700, padding: '10px 12px', borderBottom: `1px solid ${C.border}`, whiteSpace: 'nowrap' }}>{c.label}</th>)}</tr></thead>
      <tbody>{rows.map((row, i) => <tr key={row.id ?? row.signature ?? row.agent_name ?? i}>
        {columns.map(c => <td key={c.key} style={{ padding: '12px', color: C.ink, borderBottom: `1px solid ${C.border}`, verticalAlign: 'top' }}>{c.render ? c.render(row[c.key], row) : (row[c.key] ?? '?')}</td>)}
      </tr>)}</tbody>
    </table>
  </div>;
}

function dateLabel(value) {
  if (!value) return '?';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString();
}

export default function AnalyticsReport() {
  const location = useLocation();
  const slug = location.pathname.split('/').filter(Boolean).pop();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const config = useMemo(() => ({
    escalations: { title: titles.escalations, load: analyticsApi.escalations },
    agents: { title: titles.agents, load: analyticsApi.agents },
    satisfaction: { title: titles.satisfaction, load: analyticsApi.satisfaction },
    'recurring-issues': { title: titles['recurring-issues'], load: analyticsApi.recurringIssues }
  }[slug]), [slug]);

  async function load() {
    if (!config) return;
    setLoading(true);
    setError('');
    try { setData(await config.load()); }
    catch (e) { setError(e.message || 'Unable to load analytics.'); }
    finally { setLoading(false); }
  }

  useEffect(() => { load(); }, [slug]);

  if (!config) return <div style={{ padding: 28 }}>Report not found.</div>;

  const heading = config.title;
  const grid = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(175px, 1fr))', gap: 14, marginBottom: 18 };
  const two = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 330px), 1fr))', gap: 16, marginBottom: 18 };

  return <div style={{ background: C.bg, minHeight: '100%', padding: '26px clamp(14px, 3vw, 30px)', color: C.ink }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap', marginBottom: 22 }}>
      <div>
        <div style={{ color: C.purple, fontSize: 11, fontWeight: 800, letterSpacing: 1.2, textTransform: 'uppercase', marginBottom: 7 }}>SupportPilot / Analytics</div>
        <h1 style={{ margin: 0, fontSize: 25, fontWeight: 800 }}>{heading[0]}</h1>
        <p style={{ margin: '7px 0 0', color: C.muted, fontSize: 13 }}>{heading[1]}</p>
      </div>
      <button onClick={load} disabled={loading} style={{ border: `1px solid ${C.border}`, background: C.white, borderRadius: 10, padding: '10px 14px', color: C.purple, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
        <RefreshCw size={15} /> Refresh
      </button>
    </div>

    <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 13, marginBottom: 18 }}>
      {reports.map(item => {
        const Icon = item.icon;
        return <NavLink key={item.path} to={item.path} style={({ isActive }) => ({
          display: 'inline-flex', alignItems: 'center', gap: 7, whiteSpace: 'nowrap',
          padding: '10px 13px', borderRadius: 10, textDecoration: 'none', fontSize: 12,
          fontWeight: 700, color: isActive ? '#fff' : C.muted,
          background: isActive ? `linear-gradient(120deg, ${C.purple}, #9270f4)` : C.white,
          border: `1px solid ${isActive ? C.purple : C.border}`
        })}><Icon size={15} />{item.label}</NavLink>;
      })}
    </div>

    {loading ? <div style={{ ...panel, textAlign: 'center', padding: 45, color: C.muted }}><RefreshCw size={20} /> <div style={{ marginTop: 10 }}>Loading report data...</div></div>
    : error ? <div style={{ ...panel, borderColor: '#f3c8d0', color: C.red, display: 'flex', alignItems: 'center', gap: 10 }}><AlertCircle size={18} />{error}</div>
    : <>
      {slug === 'escalations' && <>
        <div style={grid}>
          <Metric label="Total escalations" value={data.total ?? 0} icon={ShieldAlert} />
          <Metric label="Resolved" value={data.resolved ?? 0} icon={CheckCircle2} color={C.teal} />
          <Metric label="Open / other statuses" value={Math.max(0, (data.total || 0) - (data.resolved || 0))} icon={Activity} color={C.orange} />
          <Metric label="Avg. resolution time" value={data.average_resolution_hours == null ? '?' : `${data.average_resolution_hours} hrs`} icon={Clock3} color={C.blue} />
        </div>
        <div style={two}>
          <Panel title="Escalations by status" empty={!Object.keys(data.by_status || {}).length}><Bars items={Object.entries(data.by_status || {}).map(([name, count]) => ({ name, count }))} nameKey="name" valueKey="count" /></Panel>
          <Panel title="Escalations by assigned team" empty={!Object.keys(data.by_team || {}).length}><Bars items={Object.entries(data.by_team || {}).map(([name, count]) => ({ name, count }))} nameKey="name" valueKey="count" color={C.blue} /></Panel>
        </div>
        <Panel title="Daily escalation trend" empty={!data.daily_trend?.length}><Bars items={data.daily_trend || []} nameKey="date" valueKey="count" color={C.teal} /></Panel>
      </>}

      {slug === 'agents' && <>
        <div style={grid}>
          <Metric label="Total agent runs" value={data.total_runs ?? 0} icon={Bot} />
          <Metric label="Successful runs" value={Object.entries(data.by_status || {}).filter(([s]) => ['ok','success','completed'].includes(s.toLowerCase())).reduce((n,[,v]) => n + v, 0)} icon={CheckCircle2} color={C.teal} />
          <Metric label="Agent types" value={data.agents?.length ?? 0} icon={BarChart3} color={C.blue} />
          <Metric label="Validation tracking" value={data.validation?.available ? 'Available' : 'Not stored'} icon={AlertCircle} color={C.orange} />
        </div>
        <Panel title="Agent performance" empty={!data.agents?.length}>
          <DataTable rows={data.agents || []} columns={[
            { key: 'agent_name', label: 'Agent' },
            { key: 'total_runs', label: 'Total runs' },
            { key: 'successful_runs', label: 'Successful' },
            { key: 'success_rate', label: 'Success rate', render: v => v == null ? '?' : `${v}%` },
            { key: 'average_duration_ms', label: 'Avg. duration', render: v => v == null ? '?' : `${v} ms` },
            { key: 'average_confidence', label: 'Avg. confidence', render: v => v == null ? '?' : `${(v * 100).toFixed(1)}%` }
          ]} />
        </Panel>
        <div style={{ ...panel, marginTop: 16, color: C.muted, fontSize: 13 }}>
          <strong style={{ color: C.ink }}>Validation outcomes:</strong> {data.validation?.message || 'Validation outcome data is not currently available.'}
        </div>
        {data.validation?.available && <div style={{ ...grid, marginTop: 14 }}>
          <Metric label="Validation runs" value={data.validation.total_runs ?? 0} icon={BarChart3} color={C.blue} />
          <Metric label="Passed" value={data.validation.passed ?? 0} icon={CheckCircle2} color={C.teal} />
          <Metric label="Failed" value={data.validation.failed ?? 0} icon={AlertCircle} color={C.orange} />
          <Metric label="Pass rate" value={data.validation.pass_rate == null ? '?' : `${data.validation.pass_rate}%`} icon={TrendingUp} color={C.teal} />
          <Metric label="Avg. validation confidence" value={data.validation.average_confidence == null ? '?' : `${(data.validation.average_confidence * 100).toFixed(1)}%`} icon={Activity} color={C.blue} />
        </div>}
      </>}

      {slug === 'satisfaction' && <>
        <div style={grid}>
          <Metric label="Total feedback" value={data.total_feedback ?? 0} icon={Activity} />
          <Metric label="Rated responses" value={data.rated_feedback ?? 0} icon={Star} color={C.orange} />
          <Metric label="Average rating" value={data.average_rating == null ? '?' : `${data.average_rating} / 5`} icon={Star} color={C.blue} />
          <Metric label="Satisfaction" value={data.satisfaction_pct == null ? '?' : `${data.satisfaction_pct}%`} icon={TrendingUp} color={C.teal} />
        </div>
        <div style={two}>
          <Panel title="Rating distribution" empty={!data.rated_feedback}><Bars items={(data.rating_distribution || []).map(x => ({ name: `${x.rating} star${x.rating === 1 ? '' : 's'}`, count: x.count }))} nameKey="name" valueKey="count" color={C.orange} /></Panel>
          <Panel title="Resolution feedback" empty={!data.total_feedback}><Bars items={[{ name: 'Resolved', count: data.resolved_feedback || 0 }, { name: 'Not resolved', count: data.unresolved_feedback || 0 }]} nameKey="name" valueKey="count" color={C.teal} /></Panel>
        </div>
        <Panel title="Daily customer feedback trend" empty={!data.daily_trend?.length}>
          <DataTable rows={data.daily_trend || []} columns={[
            { key: 'date', label: 'Date', render: dateLabel },
            { key: 'count', label: 'Feedback received' },
            { key: 'average_rating', label: 'Average rating', render: v => v == null ? '?' : `${v} / 5` }
          ]} />
        </Panel>
      </>}

      {slug === 'recurring-issues' && <>
        <div style={grid}>
          <Metric label="Recurring issue patterns" value={data.total ?? 0} icon={Repeat2} />
          <Metric label="Total occurrences" value={data.total_occurrences ?? 0} icon={Activity} color={C.blue} />
          <Metric label="Categories affected" value={Object.keys(data.by_category || {}).length} icon={BarChart3} color={C.teal} />
          <Metric label="Open issues" value={data.by_status?.Open ?? data.by_status?.open ?? 0} icon={AlertCircle} color={C.orange} />
        </div>
        <div style={two}>
          <Panel title="Issues by category" empty={!Object.keys(data.by_category || {}).length}><Bars items={Object.entries(data.by_category || {}).map(([name, count]) => ({ name, count }))} nameKey="name" valueKey="count" /></Panel>
          <Panel title="Issues by status" empty={!Object.keys(data.by_status || {}).length}><Bars items={Object.entries(data.by_status || {}).map(([name, count]) => ({ name, count }))} nameKey="name" valueKey="count" color={C.orange} /></Panel>
        </div>
        <Panel title="Recurring issue register" empty={!data.issues?.length}>
          <DataTable rows={data.issues || []} columns={[
            { key: 'signature', label: 'Issue signature' },
            { key: 'category', label: 'Category' },
            { key: 'assigned_team', label: 'Assigned team' },
            { key: 'occurrence_count', label: 'Occurrences' },
            { key: 'status', label: 'Status' },
            { key: 'first_seen', label: 'First seen', render: dateLabel },
            { key: 'last_seen', label: 'Last seen', render: dateLabel }
          ]} />
        </Panel>
      </>}
    </>}
  </div>;
}


