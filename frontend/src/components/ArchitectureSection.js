import React from 'react';

export default function ArchitectureSection({ data }) {
  if (!data) return <div className="empty-state"><div className="empty-state-icon">📐</div><h3>No hay datos</h3></div>;

  return (
    <div data-testid="architecture-section">
      <div className="section-header">
        <h2 className="section-title">📐 {data.title}</h2>
      </div>

      <div className="section-summary">{data.summary}</div>

      {/* Medallion Architecture Diagram */}
      <div className="arch-diagram">
        <div style={{ fontSize: 13, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 16 }}>Pipeline Medallion</div>
        <div className="medallion-flow">
          <div className="medallion-layer bronze">
            <span className="medallion-icon">🪵</span>
            <span className="medallion-name">BRONZE</span>
            <span className="medallion-desc">Raw Data</span>
            <span style={{fontSize: 10, color: '#b45309', marginTop: 4}}>Docling + OCR</span>
          </div>
          <div className="flow-arrow">→</div>
          <div className="medallion-layer silver">
            <span className="medallion-icon">🥈</span>
            <span className="medallion-name">SILVER</span>
            <span className="medallion-desc">Profiling + Findings</span>
            <span style={{fontSize: 10, color: '#94a3b8', marginTop: 4}}>Pandera + EDA + FAISS</span>
          </div>
          <div className="flow-arrow">→</div>
          <div className="medallion-layer gold">
            <span className="medallion-icon">🥇</span>
            <span className="medallion-name">GOLD</span>
            <span className="medallion-desc">AI Enrichment</span>
            <span style={{fontSize: 10, color: '#ca8a04', marginTop: 4}}>LiteLLM + RAG</span>
          </div>
        </div>

        {/* Tech Stack */}
        <div style={{ marginTop: 24, display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: 'center' }}>
          {[
            { label: 'FastAPI', color: '#0ea5e9' },
            { label: 'MongoDB', color: '#22c55e' },
            { label: 'ARQ/Redis', color: '#ef4444' },
            { label: 'FAISS', color: '#a855f7' },
            { label: 'LiteLLM', color: '#f97316' },
            { label: 'Docling', color: '#06b6d4' },
            { label: 'SentenceTransformers', color: '#2dd4bf' },
            { label: 'Pydantic v2', color: '#eab308' },
            { label: 'PydanticAI', color: '#f43f5e' },
          ].map(tech => (
            <span key={tech.label} style={{
              padding: '4px 10px',
              borderRadius: 9999,
              background: `${tech.color}18`,
              border: `1px solid ${tech.color}40`,
              color: tech.color,
              fontSize: 12,
              fontWeight: 600,
            }}>{tech.label}</span>
          ))}
        </div>
      </div>

      {/* Content sections */}
      <div className="arch-content">
        {(data.content || []).map((section, i) => (
          <div key={i} className="arch-section">
            <div className="arch-section-header">
              <span style={{ fontSize: 16 }}>
                {i === 0 ? '🏗️' : i === 1 ? '⚙️' : i === 2 ? '🎯' : i === 3 ? '🗄️' : '⚠️'}
              </span>
              <span className="arch-section-title">{section.heading}</span>
            </div>
            <div className="arch-section-body">{section.text}</div>
          </div>
        ))}
      </div>

      {/* Key observations */}
      <div style={{
        background: 'rgba(239,68,68,0.06)',
        border: '1px solid rgba(239,68,68,0.2)',
        borderRadius: 10,
        padding: '16px 20px',
        marginTop: 16,
      }}>
        <div style={{ fontSize: 12, fontWeight: 700, color: '#ef4444', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8 }}>
          🔴 Observación Crítica
        </div>
        <p style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.7 }}>
          El mayor problema arquitectónico es que el <strong style={{color: '#e2e8f0'}}>EmbeddingService</strong> mantiene el índice FAISS en memoria de instancia.
          El worker construye el índice al procesar un documento, pero el endpoint <code style={{fontFamily: 'var(--font-mono)', color: '#2dd4bf', fontSize: 11}}>/api/analyze</code> instancia
          un <strong style={{color: '#e2e8f0'}}>nuevo EmbeddingService vacío</strong> por request. La funcionalidad RAG está completamente rota en producción.
          Ver <strong style={{color: '#ef4444'}}>BUG-003</strong> para el fix.
        </p>
      </div>
    </div>
  );
}
