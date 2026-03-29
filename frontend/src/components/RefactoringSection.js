import React, { useState, useMemo } from 'react';
import IssueCard from './IssueCard';

export default function RefactoringSection({ data }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');

  const severities = ['all', 'high', 'medium', 'low'];

  const filtered = useMemo(() => {
    if (!data) return [];
    return (data.issues || []).filter(issue => {
      const matchesSeverity = activeFilter === 'all' || issue.severity === activeFilter;
      const matchesSearch = !searchTerm ||
        issue.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (issue.description || '').toLowerCase().includes(searchTerm.toLowerCase());
      return matchesSeverity && matchesSearch;
    });
  }, [data, activeFilter, searchTerm]);

  const counts = useMemo(() => {
    if (!data) return { all: 0 };
    const c = { all: (data.issues || []).length };
    (data.issues || []).forEach(i => { c[i.severity] = (c[i.severity] || 0) + 1; });
    return c;
  }, [data]);

  if (!data) return <div className="empty-state"><div className="empty-state-icon">⚙️</div><h3>No hay datos</h3></div>;

  return (
    <div data-testid="refactoring-section">
      <div className="section-header">
        <h2 className="section-title">⚙️ {data.title}</h2>
      </div>

      <div className="section-summary">{data.summary}</div>

      <div className="filters-bar">
        <input
          className="search-input"
          placeholder="Buscar mejora..."
          value={searchTerm}
          onChange={e => setSearchTerm(e.target.value)}
          data-testid="refactoring-search"
        />
        {severities.map(sev => (
          <button
            key={sev}
            className={`filter-btn filter-${sev} ${activeFilter === sev ? 'active' : ''}`}
            onClick={() => setActiveFilter(sev)}
            data-testid={`refactor-filter-${sev}`}
          >
            {sev === 'all' ? `Todos (${counts.all})` : `${sev.charAt(0).toUpperCase() + sev.slice(1)} (${counts[sev] || 0})`}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🔍</div>
          <h3>Sin resultados</h3>
        </div>
      ) : (
        <div className="issues-list">
          {filtered.map(issue => (
            <IssueCard key={issue.id} issue={issue} />
          ))}
        </div>
      )}
    </div>
  );
}
