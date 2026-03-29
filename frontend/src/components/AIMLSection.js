import React, { useState, useMemo } from 'react';
import IssueCard from './IssueCard';

export default function AIMLSection({ data }) {
  const [activeFilter, setActiveFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  const categories = ['all', 'ml_performance', 'ml_architecture', 'ml_resilience', 'ml_quality'];
  const categoryLabels = {
    all: 'Todos',
    ml_performance: 'Performance',
    ml_architecture: 'Arquitectura',
    ml_resilience: 'Resiliencia',
    ml_quality: 'Calidad',
  };

  const filtered = useMemo(() => {
    if (!data) return [];
    return (data.issues || []).filter(issue => {
      const matchesCat = activeFilter === 'all' || issue.category === activeFilter;
      const matchesSearch = !searchTerm ||
        issue.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (issue.description || '').toLowerCase().includes(searchTerm.toLowerCase());
      return matchesCat && matchesSearch;
    });
  }, [data, activeFilter, searchTerm]);

  const counts = useMemo(() => {
    if (!data) return { all: 0 };
    const c = { all: (data.issues || []).length };
    (data.issues || []).forEach(i => { c[i.category] = (c[i.category] || 0) + 1; });
    return c;
  }, [data]);

  if (!data) return <div className="empty-state"><div className="empty-state-icon">🧠</div><h3>No hay datos</h3></div>;

  return (
    <div data-testid="aiml-section">
      <div className="section-header">
        <h2 className="section-title">🧠 {data.title}</h2>
      </div>

      <div className="section-summary">{data.summary}</div>

      {/* Key metrics highlight */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12, marginBottom: 24 }}>
        {[
          { label: 'Overhead por tarea ARQ', value: '30–60s', desc: 'Carga de modelos ML', color: '#ef4444' },
          { label: 'RAM extra por instancia', value: '~500MB', desc: 'SentenceTransformer', color: '#f97316' },
          { label: 'RAG operacional en prod', value: '0%', desc: 'Índice FAISS no persiste', color: '#ef4444' },
          { label: 'Mejora estimada con fix', value: '~60%', desc: 'Reducir latencia y RAM', color: '#2dd4bf' },
        ].map(metric => (
          <div key={metric.label} style={{
            background: '#1e2235',
            border: '1px solid rgba(255,255,255,0.07)',
            borderRadius: 10,
            padding: '16px',
            borderLeft: `3px solid ${metric.color}`,
          }}>
            <div style={{ fontSize: 24, fontWeight: 800, color: metric.color, fontFamily: 'var(--font-mono)' }}>{metric.value}</div>
            <div style={{ fontSize: 12, fontWeight: 700, color: '#e2e8f0', marginTop: 4 }}>{metric.label}</div>
            <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>{metric.desc}</div>
          </div>
        ))}
      </div>

      <div className="filters-bar">
        <input
          className="search-input"
          placeholder="Buscar optimización..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          data-testid="aiml-search"
        />
        {categories.map(cat => (
          <button
            key={cat}
            className={`filter-btn ${activeFilter === cat ? 'active' : ''}`}
            onClick={() => setActiveFilter(cat)}
            data-testid={`aiml-filter-${cat}`}
          >
            {categoryLabels[cat]} ({cat === 'all' ? counts.all : (counts[cat] || 0)})
          </button>
        ))}
      </div>

      <div className="issues-list">
        {filtered.map(issue => (
          <IssueCard key={issue.id} issue={issue} />
        ))}
      </div>
    </div>
  );
}
