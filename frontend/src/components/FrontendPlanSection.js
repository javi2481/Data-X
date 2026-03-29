import React from 'react';
import IssueCard from './IssueCard';

export default function FrontendPlanSection({ data }) {
  if (!data) return <div data-testid="frontend-plan-loading">Cargando plan de frontend...</div>;

  return (
    <div className="section-container" data-testid="frontend-plan-section">
      <div className="section-header">
        <h1 className="section-title">
          <span className="section-icon">💻</span>
          {data.title}
        </h1>
        <p className="section-summary">{data.summary}</p>
      </div>

      <div className="issues-grid">
        {data.issues?.map(issue => (
          <IssueCard key={issue.id} issue={issue} />
        ))}
      </div>

      {(!data.issues || data.issues.length === 0) && (
        <div className="empty-state">
          <p>No hay issues de frontend definidos</p>
        </div>
      )}
    </div>
  );
}
