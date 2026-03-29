import React from 'react';
import IssueCard from './IssueCard';

export default function NextStepsSection({ data }) {
  if (!data) return <div data-testid="next-steps-loading">Cargando siguientes pasos...</div>;

  return (
    <div className="section-container" data-testid="next-steps-section">
      <div className="section-header">
        <h1 className="section-title">
          <span className="section-icon">🚀</span>
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
          <p>No hay siguientes pasos definidos</p>
        </div>
      )}
    </div>
  );
}
