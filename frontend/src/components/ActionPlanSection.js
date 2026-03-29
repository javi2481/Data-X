import React, { useState } from 'react';

function ActionCard({ action, priority }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="action-card" data-testid={`action-card-${action.id}`}>
      <div className="action-card-id">{action.id} • Ref: {action.ref}</div>
      <div className="action-card-title">{action.title}</div>
      <div className="action-card-meta">
        <span className="action-effort">⏱ {action.effort}</span>
      </div>
      <div
        style={{ cursor: 'pointer', fontSize: 11, color: '#2dd4bf', marginTop: 8 }}
        onClick={() => setExpanded(e => !e)}
        data-testid={`action-expand-${action.id}`}
      >
        {expanded ? '▴ Ocultar pasos' : '▾ Ver pasos'}
      </div>
      {expanded && (
        <div className="action-steps">
          <div style={{ fontSize: 11, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.3px', marginBottom: 6 }}>
            Impacto: {action.impact}
          </div>
          {(action.steps || []).map((step, i) => (
            <div key={i} className="action-step">{step}</div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ActionPlanSection({ data }) {
  if (!data || !data.actions) return (
    <div className="empty-state">
      <div className="empty-state-icon">🎯</div>
      <h3>No hay datos del plan de acción</h3>
    </div>
  );

  const { actions } = data;
  const columns = [
    { key: 'critical', label: '🔴 Crítico', emoji: '🔴', items: actions.critical || [] },
    { key: 'medium', label: '🟡 Medio', emoji: '🟡', items: actions.medium || [] },
    { key: 'low', label: '🔵 Bajo', emoji: '🔵', items: actions.low || [] },
  ];

  return (
    <div data-testid="action-plan-section">
      <div className="section-header">
        <h2 className="section-title">🎯 {data.title}</h2>
      </div>

      <div className="section-summary">{data.summary}</div>

      {/* Summary row */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
        {columns.map(col => (
          <div key={col.key} style={{
            background: 'var(--bg-card)',
            border: `1px solid var(--${col.key}-border, var(--border))`,
            borderRadius: 8,
            padding: '12px 20px',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}>
            <span style={{ fontSize: 20 }}>{col.emoji}</span>
            <div>
              <div style={{ fontSize: 22, fontWeight: 800, color: `var(--${col.key})`, fontFamily: 'var(--font-mono)' }}>
                {col.items.length}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                Acciones {col.key === 'critical' ? 'Críticas' : col.key === 'medium' ? 'Medias' : 'Bajas'}
              </div>
            </div>
          </div>
        ))}

        <div style={{
          background: 'rgba(45,212,191,0.06)',
          border: '1px solid rgba(45,212,191,0.2)',
          borderRadius: 8,
          padding: '12px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
        }}>
          <span style={{ fontSize: 20 }}>⏰</span>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#2dd4bf' }}>1–2 días</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.3px' }}>Esfuerzo total crítico</div>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="action-board" data-testid="action-board">
        {columns.map(col => (
          <div key={col.key} className="action-column">
            <div className={`action-col-header ${col.key}`}>
              <span style={{ fontSize: 14 }}>{col.emoji}</span>
              <span className="action-col-title">
                {col.key === 'critical' ? 'Crítico' : col.key === 'medium' ? 'Medio' : 'Bajo'}
              </span>
              <span className="action-col-count">{col.items.length}</span>
            </div>
            <div className="action-cards">
              {col.items.map(action => (
                <ActionCard key={action.id} action={action} priority={col.key} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
