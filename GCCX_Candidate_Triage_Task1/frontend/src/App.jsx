import { useCallback, useEffect, useMemo, useState } from "react";
import { checkHealth, getCandidates, getCandidateFacets, getFitSummary, updateCandidate } from "./api.js";
import "./styles.css";

function CandidateCard({ candidate, onShortlist, onTags, onSummary, summary, busySummary }) {
  const [tagInput, setTagInput] = useState(candidate.tags.join(", "));
  useEffect(() => setTagInput(candidate.tags.join(", ")), [candidate.tags]);

  return (
    <article className={`candidate-card ${candidate.is_shortlisted ? "is-shortlisted" : ""}`}>
      <div className="candidate-main">
        <div className="avatar">{candidate.name.split(/\s+/).map(part => part[0]).slice(0, 2).join("").toUpperCase()}</div>
        <div className="candidate-title">
          <div className="name-line"><h2>{candidate.name}</h2><span className="candidate-id">{candidate.id}</span></div>
          <p>{candidate.target_role} <span className="dot-sep">·</span> {candidate.years_experience} years experience</p>
          <div className="meta-row"><span>{candidate.source}</span><span>Applied {candidate.applied_date || "date unknown"}</span></div>
        </div>
        <button className={`shortlist-btn ${candidate.is_shortlisted ? "active" : ""}`} onClick={() => onShortlist(candidate)} aria-pressed={candidate.is_shortlisted}>
          {candidate.is_shortlisted ? "★ Shortlisted" : "☆ Shortlist"}
        </button>
      </div>
      <div className="skills-row">{candidate.skills.map(skill => <span className="skill" key={skill}>{skill}</span>)}</div>
      <div className="notes"><span className="section-label">RECRUITER NOTES</span><p>{candidate.notes || "No notes provided."}</p></div>
      <div className="tags-editor">
        <label htmlFor={`tags-${candidate.id}`}>Tags <span>(comma-separated)</span></label>
        <div className="tag-controls">
          <input id={`tags-${candidate.id}`} value={tagInput} maxLength={1200} onChange={e => setTagInput(e.target.value)} placeholder="e.g. strong portfolio, follow-up" />
          <button className="secondary-btn" onClick={() => onTags(candidate, tagInput)}>Save tags</button>
        </div>
        {candidate.tags.length > 0 && <div className="saved-tags">{candidate.tags.map(tag => <span key={tag}>{tag}</span>)}</div>}
      </div>
      <div className="ai-section">
        <div className="ai-heading"><span className="sparkle">✳</span><strong>AI fit summary</strong><span className="ai-caption">Grounded in supplied candidate notes</span></div>
        <button className="ai-btn" onClick={() => onSummary(candidate)} disabled={busySummary}>{busySummary ? "Generating…" : "Generate summary"}</button>
        {summary && <div className={`summary-result ${summary.provider === "error" || summary.provider === "not_configured" ? "summary-warning" : ""}`}>
          {summary.summary && <p>{summary.summary}</p>}
          {summary.message && <p>{summary.message}</p>}
          {summary.provider === "groq" && <span className="provider-label">Generated with Groq</span>}
        </div>}
      </div>
    </article>
  );
}

export default function App() {
  const [candidates, setCandidates] = useState([]);
  const [facets, setFacets] = useState({ roles: [], sources: [], skills: [], total_candidates: 0, shortlisted_count: 0 });
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [source, setSource] = useState("");
  const [skill, setSkill] = useState("");
  const [minExperience, setMinExperience] = useState("");
  const [maxExperience, setMaxExperience] = useState("");
  const [shortlistedOnly, setShortlistedOnly] = useState(false);
  const [apiReady, setApiReady] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [summaries, setSummaries] = useState({});
  const [busySummaries, setBusySummaries] = useState({});
  const [toast, setToast] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [data, facetData] = await Promise.all([
        getCandidates({ search, role, source, skill, min_experience: minExperience, max_experience: maxExperience, shortlisted_only: shortlistedOnly }),
        getCandidateFacets()
      ]);
      setCandidates(data.items); setFacets(facetData); setApiReady(true);
    } catch (e) { setError(e.message); setApiReady(false); }
    finally { setLoading(false); }
  }, [search, role, source, skill, minExperience, maxExperience, shortlistedOnly]);

  useEffect(() => { checkHealth().then(setApiReady).catch(() => setApiReady(false)); }, []);
  useEffect(() => { const timer = setTimeout(load, 180); return () => clearTimeout(timer); }, [load]);

  const shortlistedCount = useMemo(() => candidates.filter(c => c.is_shortlisted).length, [candidates]);

  async function toggleShortlist(candidate) {
    try {
      await updateCandidate(candidate.id, { is_shortlisted: !candidate.is_shortlisted });
      setToast(candidate.is_shortlisted ? "Removed from shortlist" : "Added to shortlist");
      await load();
    } catch (e) { setError(e.message); }
  }
  async function saveTags(candidate, value) {
    const tags = [...new Set(value.split(",").map(t => t.trim()).filter(Boolean))].slice(0, 20);
    try {
      await updateCandidate(candidate.id, { tags });
      setToast("Tags saved"); await load();
    } catch (e) { setError(e.message); }
  }
  async function createSummary(candidate) {
    setBusySummaries(prev => ({ ...prev, [candidate.id]: true }));
    setSummaries(prev => ({ ...prev, [candidate.id]: null }));
    try {
      const result = await getFitSummary(candidate.id, role || candidate.target_role);
      setSummaries(prev => ({ ...prev, [candidate.id]: result }));
    } catch (e) {
      setSummaries(prev => ({ ...prev, [candidate.id]: { provider: "error", message: e.message } }));
    } finally { setBusySummaries(prev => ({ ...prev, [candidate.id]: false })); }
  }
  function resetFilters() {
    setSearch(""); setRole(""); setSource(""); setSkill(""); setMinExperience(""); setMaxExperience(""); setShortlistedOnly(false);
  }

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand"><div className="brand-mark">G</div><div><span className="eyebrow">GCCX · TASK 1</span><h1>Candidate Triage</h1><p className="subtitle">A focused workspace for faster, evidence-based candidate review.</p></div></div>
      <div className="api-status"><span className={`status-dot ${apiReady ? "online" : apiReady === false ? "offline" : ""}`}></span>{apiReady ? "API connected" : apiReady === false ? "API offline" : "Connecting…"}</div>
    </header>

    <section className="stats">
      <div className="stat-card"><span className="stat-label">CANDIDATES MATCHING</span><strong>{loading ? "—" : candidates.length}</strong><span className="stat-foot">Current filter results</span></div>
      <div className="stat-card"><span className="stat-label">SHORTLISTED IN VIEW</span><strong>{facets.shortlisted_count ?? candidates.filter(c => c.is_shortlisted).length}</strong><span className="stat-foot">Persisted in SQLite · all candidates</span></div>
      <div className="stat-card"><span className="stat-label">AVAILABLE SKILLS</span><strong>{facets.skills.length}</strong><span className="stat-foot">Across supplied dataset</span></div>
      <div className="stat-card"><span className="stat-label">DATASET</span><strong>{facets.total_candidates ?? 0}</strong><span className="stat-foot">Mock candidates from starter kit</span></div>
    </section>

    <section className="toolbar">
      <div className="search-wrap"><span className="search-icon">⌕</span><input aria-label="Search candidates" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search name, role, notes, or candidate ID…" /></div>
      <label className="filter"><span>Target role</span><select value={role} onChange={e => setRole(e.target.value)}><option value="">All roles</option>{facets.roles.map(x => <option key={x}>{x}</option>)}</select></label>
      <label className="filter"><span>Source</span><select value={source} onChange={e => setSource(e.target.value)}><option value="">All sources</option>{facets.sources.map(x => <option key={x}>{x}</option>)}</select></label>
      <label className="filter"><span>Skill</span><select value={skill} onChange={e => setSkill(e.target.value)}><option value="">Any skill</option>{facets.skills.map(x => <option key={x}>{x}</option>)}</select></label>
      <div className="experience-filter"><label className="filter"><span>Min years</span><input type="number" min="0" value={minExperience} onChange={e => setMinExperience(e.target.value)} placeholder="0" /></label><label className="filter"><span>Max years</span><input type="number" min="0" value={maxExperience} onChange={e => setMaxExperience(e.target.value)} placeholder="Any" /></label></div>
      <label className="shortlisted-filter"><input type="checkbox" checked={shortlistedOnly} onChange={e => setShortlistedOnly(e.target.checked)} /> Shortlisted only</label>
      <button className="reset-btn" onClick={resetFilters}>Reset filters</button>
    </section>

    <div className="results-header"><div><h2>Candidate pipeline</h2><p>Review the available evidence, save tags, and shortlist candidates for follow-up.</p></div><span className="count-pill">{candidates.length} results</span></div>
    {toast && <div className="toast" role="status">{toast}<button onClick={() => setToast("")} aria-label="Dismiss">×</button></div>}
    {error && <div className="error-banner"><strong>Something went wrong</strong><p>{error}</p><button onClick={load}>Retry</button></div>}
    {loading ? <div className="empty-state">Loading candidate records…</div> : candidates.length === 0 && !error ? <div className="empty-state"><h3>No candidates found</h3><p>Try removing a filter or searching for another skill or role.</p><button className="secondary-btn" onClick={resetFilters}>Clear filters</button></div> :
      <section className="candidate-list">{candidates.map(candidate => <CandidateCard key={candidate.id} candidate={candidate} onShortlist={toggleShortlist} onTags={saveTags} onSummary={createSummary} summary={summaries[candidate.id]} busySummary={Boolean(busySummaries[candidate.id])} />)}</section>}
    <footer><span>GCCX Candidate Triage Tool</span><span>Human review required · AI summaries are decision support, not hiring decisions.</span></footer>
  </main>;
}
