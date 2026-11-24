import React, { useEffect, useState } from "react";
import { Search, BookOpen, Plus, X, Save, RefreshCw } from "lucide-react";
import { api } from "../api";
import { CATEGORIES } from "../config";
import { useAuth } from "../context/AuthContext";
import { Loading, ErrorState, Empty } from "../components/UI";

const initialForm = { title: "", category: "Network", keywords: "", content: "" };

export default function KnowledgeBase() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [articles, setArticles] = useState([]);
  const [selected, setSelected] = useState(null);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(initialForm);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      setArticles(await api.kbArticles({ q, category, limit: 200 }));
    } catch (e) {
      setError(e.message || "Unable to load articles.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const t = setTimeout(load, 250);
    return () => clearTimeout(t);
  }, [q, category]);

  const open = async (article) => {
    try {
      setSelected(await api.kbArticle(article.article_id));
      setMessage("");
    } catch (e) {
      setError(e.message);
    }
  };

  const createArticle = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      const created = await api.kbCreate({
        title: form.title.trim(),
        category: form.category,
        keywords: form.keywords.trim() || null,
        content: form.content.trim()
      });
      setShowForm(false);
      setForm(initialForm);
      setMessage(created.indexed
        ? "Article created and indexed successfully."
        : "Article created. Search indexing may need attention.");
      await load();
      if (created.article_id) setSelected(created);
    } catch (e) {
      setError(e.message || "Unable to create article.");
    } finally {
      setSaving(false);
    }
  };

  const inputStyle = {
    width: "100%", padding: "11px 13px", border: "1px solid #e2d9f2",
    borderRadius: 9, fontSize: 14, boxSizing: "border-box",
    color: "#28164f", background: "#fff", outlineColor: "#8055d9"
  };

  return (
    <div className="page-content">
      <div className="page-heading">
        <div>
          <div className="eyebrow"><span className="eyebrow-line" />KNOWLEDGE BASE</div>
          <h1>Support knowledge</h1>
          <p>Browse and manage the articles used by the resolution pipeline.</p>
        </div>
        {isAdmin && (
          <button onClick={() => { setShowForm(true); setMessage(""); setError(""); }}
            style={{ display: "flex", alignItems: "center", gap: 8, padding: "11px 17px",
              border: 0, borderRadius: 10, color: "#fff", fontWeight: 700,
              cursor: "pointer", background: "linear-gradient(120deg,#7040c8,#9b55df)",
              boxShadow: "0 5px 16px #8055d933" }}>
            <Plus size={17} /> Add Article
          </button>
        )}
      </div>

      {message && <div style={{ padding: 13, marginBottom: 14, borderRadius: 9,
        color: "#176b4a", background: "#e8f8ef", border: "1px solid #b8e8ce" }}>{message}</div>}

      {showForm && (
        <section style={{ background: "#fff", border: "1px solid #e9def8",
          borderRadius: 16, padding: 24, marginBottom: 20,
          boxShadow: "0 10px 30px #39205b12" }}>
          <div style={{ display: "flex", justifyContent: "space-between",
            alignItems: "center", marginBottom: 20 }}>
            <div>
              <h2 style={{ margin: 0, color: "#28164f" }}>Create knowledge article</h2>
              <p style={{ margin: "6px 0 0", color: "#817693", fontSize: 13 }}>
                Add an article to support AI-powered resolutions.
              </p>
            </div>
            <button onClick={() => setShowForm(false)} aria-label="Close form"
              style={{ border: 0, background: "#f3effa", borderRadius: 8,
                padding: 8, cursor: "pointer", color: "#65449a" }}>
              <X size={19} />
            </button>
          </div>

          <form onSubmit={createArticle}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <label style={{ color: "#514267", fontSize: 13, fontWeight: 600 }}>
                Article title *
                <input required minLength={5} maxLength={200} value={form.title}
                  onChange={e => setForm({ ...form, title: e.target.value })}
                  placeholder="Enter a descriptive title" style={{ ...inputStyle, marginTop: 7 }} />
              </label>
              <label style={{ color: "#514267", fontSize: 13, fontWeight: 600 }}>
                Category *
                <select required value={form.category}
                  onChange={e => setForm({ ...form, category: e.target.value })}
                  style={{ ...inputStyle, marginTop: 7 }}>
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </label>
            </div>

            <label style={{ display: "block", marginTop: 16, color: "#514267",
              fontSize: 13, fontWeight: 600 }}>
              Keywords
              <input value={form.keywords}
                onChange={e => setForm({ ...form, keywords: e.target.value })}
                placeholder="e.g. connection, troubleshooting, login"
                style={{ ...inputStyle, marginTop: 7 }} />
            </label>

            <label style={{ display: "block", marginTop: 16, color: "#514267",
              fontSize: 13, fontWeight: 600 }}>
              Article content *
              <textarea required minLength={20} rows={9} value={form.content}
                onChange={e => setForm({ ...form, content: e.target.value })}
                placeholder="Write the solution steps and helpful instructions..."
                style={{ ...inputStyle, marginTop: 7, resize: "vertical", lineHeight: 1.6 }} />
              <span style={{ display: "block", textAlign: "right", marginTop: 4,
                color: "#9186a2", fontSize: 11 }}>{form.content.length} characters (minimum 20)</span>
            </label>

            <div style={{ display: "flex", justifyContent: "flex-end",
              gap: 10, marginTop: 20 }}>
              <button type="button" onClick={() => setShowForm(false)}
                style={{ padding: "10px 17px", border: "1px solid #e2d9f2",
                  borderRadius: 9, background: "#fff", color: "#55456e",
                  cursor: "pointer" }}>Cancel</button>
              <button type="submit" disabled={saving}
                style={{ display: "flex", alignItems: "center", gap: 8,
                  padding: "10px 19px", border: 0, borderRadius: 9,
                  background: saving ? "#a99abf" : "linear-gradient(120deg,#7040c8,#9654dc)",
                  color: "#fff", fontWeight: 700, cursor: saving ? "wait" : "pointer" }}>
                <Save size={16} /> {saving ? "Saving..." : "Save Article"}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="panel kb-panel">
        <div className="kb-toolbar">
          <div className="search-box">
            <Search size={15} />
            <input value={q} onChange={e => setQ(e.target.value)}
              placeholder="Search article title..." />
          </div>
          <select className="filter-select" value={category}
            onChange={e => setCategory(e.target.value)}>
            <option value="">All categories</option>
            {CATEGORIES.map(x => <option key={x}>{x}</option>)}
          </select>
          <button onClick={load} title="Refresh articles"
            style={{ border: "1px solid #e6def1", borderRadius: 8,
              background: "#fff", padding: "8px 11px", color: "#7040c8", cursor: "pointer" }}>
            <RefreshCw size={16} />
          </button>
        </div>

        {loading ? <Loading text="Loading articles..." /> :
          error ? <ErrorState message={error} onRetry={load} /> :
          <div className="kb-layout">
            <div className="kb-list">
              {articles.length ? articles.map(a => (
                <button className={`kb-item ${selected?.article_id === a.article_id ? "active" : ""}`}
                  key={a.article_id} onClick={() => open(a)}>
                  <b>{a.title}</b>
                  <span>{a.category || "Uncategorised"}</span>
                </button>
              )) : <Empty title="No matching article"
                detail="Try another search or category." />}
            </div>
            <div className="kb-viewer">
              {selected ? <>
                <div className="eyebrow">{selected.category}</div>
                <h2>{selected.title}</h2>
                <p className="article-meta">{selected.keywords || "Knowledge base article"}</p>
                <div className="kb-content">{selected.content}</div>
              </> : <div className="kb-empty">
                <BookOpen size={28} />
                <b>Select an article</b>
                <span>Choose a result to read the full knowledge-base content.</span>
              </div>}
            </div>
          </div>}
      </section>
    </div>
  );
}
