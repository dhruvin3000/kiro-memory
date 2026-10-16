import React, { useState, useEffect, useCallback } from 'react';

// ── Inline styles (no external CSS deps) ─────────────────────────────────────
const S = {
  app: { minHeight: '100vh', background: '#0d1117', color: '#e6edf3', fontFamily: 'inherit' },
  header: {
    background: '#161b22', borderBottom: '1px solid #30363d',
    padding: '16px 32px', display: 'flex', alignItems: 'center', gap: '16px',
  },
  logo: { fontSize: '22px', fontWeight: 700, color: '#58a6ff' },
  badge: {
    background: '#21262d', border: '1px solid #30363d', borderRadius: '12px',
    padding: '2px 10px', fontSize: '12px', color: '#8b949e',
  },
  main: { maxWidth: '1100px', margin: '0 auto', padding: '32px 24px' },
  searchBar: {
    display: 'flex', gap: '12px', marginBottom: '32px',
  },
  input: {
    flex: 1, background: '#21262d', border: '1px solid #30363d', borderRadius: '8px',
    color: '#e6edf3', padding: '12px 16px', fontSize: '16px', outline: 'none',
  },
  btn: {
    background: '#238636', border: 'none', borderRadius: '8px', color: '#fff',
    padding: '12px 24px', fontSize: '15px', cursor: 'pointer', fontWeight: 600,
  },
  btnSecondary: {
    background: '#21262d', border: '1px solid #30363d', borderRadius: '8px',
    color: '#e6edf3', padding: '12px 16px', fontSize: '14px', cursor: 'pointer',
  },
  statsRow: {
    display: 'flex', gap: '16px', marginBottom: '32px', flexWrap: 'wrap',
  },
  statCard: {
    background: '#161b22', border: '1px solid #30363d', borderRadius: '10px',
    padding: '16px 24px', flex: '1', minWidth: '140px',
  },
  statNum: { fontSize: '28px', fontWeight: 700, color: '#58a6ff' },
  statLabel: { fontSize: '13px', color: '#8b949e', marginTop: '4px' },
  grid: { display: 'flex', flexDirection: 'column', gap: '16px' },
  card: {
    background: '#161b22', border: '1px solid #30363d', borderRadius: '10px',
    padding: '20px 24px', cursor: 'pointer', transition: 'border-color 0.15s',
  },
  cardHover: { borderColor: '#58a6ff' },
  cardTitle: { fontSize: '17px', fontWeight: 700, color: '#58a6ff', marginBottom: '6px' },
  cardQ: { fontSize: '14px', color: '#8b949e', marginBottom: '10px' },
  cardRationale: { fontSize: '14px', color: '#e6edf3', lineHeight: 1.6, marginBottom: '12px' },
  tagsRow: { display: 'flex', gap: '6px', flexWrap: 'wrap' },
  tag: {
    background: '#1f2d3d', border: '1px solid #1f6feb', borderRadius: '6px',
    padding: '2px 10px', fontSize: '12px', color: '#58a6ff',
  },
  altTag: {
    background: '#2d1f1f', border: '1px solid #6e3a3a', borderRadius: '6px',
    padding: '2px 10px', fontSize: '12px', color: '#f85149',
  },
  meta: { fontSize: '12px', color: '#8b949e', marginTop: '10px' },
  filterRow: { display: 'flex', gap: '8px', marginBottom: '20px', flexWrap: 'wrap' },
  filterChip: {
    background: '#21262d', border: '1px solid #30363d', borderRadius: '20px',
    padding: '4px 14px', fontSize: '13px', cursor: 'pointer', color: '#8b949e',
  },
  filterChipActive: {
    background: '#1f6feb', border: '1px solid #58a6ff', color: '#fff',
  },
  empty: { textAlign: 'center', padding: '64px 0', color: '#8b949e', fontSize: '16px' },
  confBar: { display: 'inline-block', height: '4px', borderRadius: '2px', background: '#238636', marginLeft: '8px', verticalAlign: 'middle' },
  sourceChip: {
    display: 'inline-block', padding: '2px 8px', borderRadius: '4px',
    fontSize: '11px', marginLeft: '8px',
  },
};

const SOURCE_COLORS = {
  spec: { background: '#1a2d1a', color: '#3fb950' },
  git_commit: { background: '#2d1f1a', color: '#f0883e' },
  readme: { background: '#1a1a2d', color: '#79c0ff' },
  steering: { background: '#2d1a2d', color: '#d2a8ff' },
};

// ── API ───────────────────────────────────────────────────────────────────────

const API = '/api';

async function apiFetch(path) {
  const res = await fetch(API + path);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

// ── Components ────────────────────────────────────────────────────────────────

function StatCard({ num, label }) {
  return (
    <div style={S.statCard}>
      <div style={S.statNum}>{num}</div>
      <div style={S.statLabel}>{label}</div>
    </div>
  );
}

function DecisionCard({ decision, onClick }) {
  const [hovered, setHovered] = useState(false);
  const srcStyle = SOURCE_COLORS[decision.source_type] || { background: '#21262d', color: '#8b949e' };
  const confWidth = Math.round(decision.confidence * 60);

  return (
    <div
      style={{ ...S.card, ...(hovered ? S.cardHover : {}) }}
      onClick={() => onClick(decision)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <div style={S.cardTitle}>
        {decision.decision}
        <span style={{ ...S.sourceChip, ...srcStyle }}>{decision.source_type}</span>
        <span style={{ ...S.confBar, width: confWidth }} title={`Confidence: ${Math.round(decision.confidence * 100)}%`} />
      </div>
      <div style={S.cardQ}>Q: {decision.question}</div>
      <div style={S.cardRationale}>{decision.rationale}</div>
      <div style={S.tagsRow}>
        {decision.tags.map(t => <span key={t} style={S.tag}>#{t}</span>)}
        {decision.alternatives_rejected.map(a => <span key={a} style={S.altTag}>✗ {a}</span>)}
      </div>
      <div style={S.meta}>
        {decision.source_path} · {decision.source_date?.slice(0, 10) || 'unknown date'}
      </div>
    </div>
  );
}

function DetailModal({ decision, onClose }) {
  if (!decision) return null;
  const srcStyle = SOURCE_COLORS[decision.source_type] || {};
  return (
    <div
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#161b22', border: '1px solid #30363d', borderRadius: '14px',
          padding: '32px', maxWidth: '680px', width: '90%', maxHeight: '80vh',
          overflowY: 'auto',
        }}
        onClick={e => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h2 style={{ color: '#58a6ff', fontSize: '20px' }}>{decision.decision}</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#8b949e', fontSize: '20px', cursor: 'pointer' }}>✕</button>
        </div>
        <p style={{ color: '#8b949e', marginBottom: '16px', fontSize: '14px' }}>
          <strong style={{ color: '#e6edf3' }}>Question:</strong> {decision.question}
        </p>
        <p style={{ marginBottom: '16px', lineHeight: 1.7 }}>
          <strong>Rationale:</strong> {decision.rationale}
        </p>
        {decision.alternatives_rejected.length > 0 && (
          <p style={{ marginBottom: '16px' }}>
            <strong>Rejected alternatives:</strong>{' '}
            {decision.alternatives_rejected.map(a => (
              <span key={a} style={{ ...S.altTag, marginRight: '6px' }}>✗ {a}</span>
            ))}
          </p>
        )}
        <div style={{ ...S.tagsRow, marginBottom: '20px' }}>
          {decision.tags.map(t => <span key={t} style={S.tag}>#{t}</span>)}
        </div>
        <div style={{ background: '#0d1117', borderRadius: '8px', padding: '16px', fontSize: '13px', color: '#8b949e' }}>
          <div><strong>Source:</strong> <span style={{ ...S.sourceChip, ...srcStyle }}>{decision.source_type}</span></div>
          <div style={{ marginTop: '8px' }}><strong>Path:</strong> {decision.source_path}</div>
          {decision.commit_sha && <div style={{ marginTop: '8px' }}><strong>Commit:</strong> {decision.commit_sha}</div>}
          {decision.author && <div style={{ marginTop: '8px' }}><strong>Author:</strong> {decision.author}</div>}
          <div style={{ marginTop: '8px' }}><strong>Date:</strong> {decision.source_date || 'unknown'}</div>
          <div style={{ marginTop: '8px' }}><strong>Confidence:</strong> {Math.round(decision.confidence * 100)}%</div>
          <div style={{ marginTop: '8px', fontSize: '11px', color: '#6e7681' }}><strong>ID:</strong> {decision.id}</div>
        </div>
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────

export default function App() {
  const [decisions, setDecisions] = useState([]);
  const [stats, setStats] = useState(null);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [activeTag, setActiveTag] = useState(null);
  const [selected, setSelected] = useState(null);
  const [mode, setMode] = useState('all'); // 'all' | 'search'

  // Load stats + all decisions on mount
  useEffect(() => {
    apiFetch('/stats').then(setStats).catch(console.error);
    loadAll();
  }, []);

  function loadAll() {
    setLoading(true);
    apiFetch('/decisions?limit=100')
      .then(data => { setDecisions(data); setMode('all'); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  function handleSearch(e) {
    e && e.preventDefault();
    if (!query.trim()) { loadAll(); return; }
    setLoading(true);
    apiFetch(`/decisions/search?q=${encodeURIComponent(query)}&top=20`)
      .then(data => { setDecisions(data); setMode('search'); setActiveTag(null); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  function filterByTag(tag) {
    if (activeTag === tag) { setActiveTag(null); loadAll(); return; }
    setActiveTag(tag);
    setLoading(true);
    apiFetch(`/decisions?tag=${encodeURIComponent(tag)}&limit=100`)
      .then(data => { setDecisions(data); setMode('tag'); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }

  const topTags = stats ? Object.entries(stats.top_tags).slice(0, 10) : [];

  return (
    <div style={S.app}>
      {/* Header */}
      <div style={S.header}>
        <span style={S.logo}>⚡ kiro-recall</span>
        <span style={S.badge}>Architectural Decision Log</span>
        {stats && <span style={S.badge}>{stats.total} decisions</span>}
        {stats && <span style={{ ...S.badge, marginLeft: 'auto' }}>
          {stats.vector_index_available ? '🔍 Semantic search' : '🔎 Keyword search'}
        </span>}
      </div>

      <div style={S.main}>
        {/* Stats */}
        {stats && (
          <div style={S.statsRow}>
            <StatCard num={stats.total} label="Total Decisions" />
            {Object.entries(stats.by_source).map(([src, count]) => (
              <StatCard key={src} num={count} label={src} />
            ))}
          </div>
        )}

        {/* Search */}
        <form onSubmit={handleSearch} style={S.searchBar}>
          <input
            style={S.input}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder='Ask anything: "why did we choose postgres?" or "auth approach"...'
          />
          <button type="submit" style={S.btn}>Search</button>
          {mode !== 'all' && (
            <button type="button" style={S.btnSecondary} onClick={() => { setQuery(''); loadAll(); setActiveTag(null); }}>
              Clear
            </button>
          )}
        </form>

        {/* Tag filters */}
        {topTags.length > 0 && (
          <div style={S.filterRow}>
            {topTags.map(([tag, count]) => (
              <span
                key={tag}
                style={{ ...S.filterChip, ...(activeTag === tag ? S.filterChipActive : {}) }}
                onClick={() => filterByTag(tag)}
              >
                #{tag} <span style={{ opacity: 0.6 }}>{count}</span>
              </span>
            ))}
          </div>
        )}

        {/* Results */}
        {loading ? (
          <div style={S.empty}>Loading decisions...</div>
        ) : decisions.length === 0 ? (
          <div style={S.empty}>
            {mode === 'search'
              ? `No decisions found for "${query}"`
              : 'No decisions indexed yet. Run: kiro-recall scan'}
          </div>
        ) : (
          <div style={S.grid}>
            {decisions.map(d => (
              <DecisionCard key={d.id} decision={d} onClick={setSelected} />
            ))}
          </div>
        )}
      </div>

      {/* Detail modal */}
      <DetailModal decision={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
