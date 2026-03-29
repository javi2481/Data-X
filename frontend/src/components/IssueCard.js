import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

const REPO_BASE = 'https://github.com/javi2481/data-x/blob/main/';

function CodeBlock({ code, label }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="code-block-wrapper">
      <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={handleCopy} data-testid={`copy-btn-${label}`}>
        {copied ? '✓ Copiado' : 'Copiar'}
      </button>
      <SyntaxHighlighter
        language="python"
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          background: '#0d0f14',
          fontSize: '12px',
          borderRadius: 0,
          maxHeight: '320px',
          overflowY: 'auto',
        }}
        showLineNumbers={false}
        wrapLongLines={true}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

export default function IssueCard({ issue, defaultExpanded = false }) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [activeTab, setActiveTab] = useState('before');

  const fix = issue.suggested_fix;
  const ghUrl = issue.file && issue.line_start
    ? `${REPO_BASE}${issue.file}#L${issue.line_start}-L${issue.line_end || issue.line_start}`
    : null;

  const categoryLabels = {
    bug: 'Bug', security: 'Seguridad', performance: 'Performance',
    reliability: 'Confiabilidad', design: 'Diseño', code_quality: 'Calidad',
    ml_performance: 'ML Performance', ml_architecture: 'ML Arquitectura',
    ml_resilience: 'ML Resiliencia', ml_quality: 'ML Calidad', deprecation: 'Deprecación',
  };

  return (
    <div className={`issue-card ${issue.severity}`} data-testid={`issue-card-${issue.id}`}>
      <div className="issue-header" onClick={() => setExpanded(e => !e)} data-testid={`issue-header-${issue.id}`}>
        <span className="issue-id">{issue.id}</span>
        <span className="issue-title">{issue.title}</span>
        <div className="issue-meta">
          {issue.category && (
            <span style={{ fontSize: 11, color: '#64748b', padding: '2px 7px', background: 'rgba(255,255,255,0.04)', borderRadius: 4, border: '1px solid rgba(255,255,255,0.07)' }}>
              {categoryLabels[issue.category] || issue.category}
            </span>
          )}
          <span className={`severity-badge ${issue.severity}`}>{issue.severity}</span>
          <span className={`expand-icon ${expanded ? 'expanded' : ''}`}>▼</span>
        </div>
      </div>

      {expanded && (
        <div className="issue-body" data-testid={`issue-body-${issue.id}`}>
          {/* File reference */}
          {issue.file && (
            <div className="issue-file">
              <span className="file-path">{issue.file}</span>
              {issue.line_start && (
                <span className="file-lines">L{issue.line_start}{issue.line_end ? `–L${issue.line_end}` : ''}</span>
              )}
              {ghUrl && (
                <a href={ghUrl} target="_blank" rel="noreferrer" className="gh-link" data-testid={`gh-link-${issue.id}`}>
                  <span>🔗</span> Ver en GitHub
                </a>
              )}
            </div>
          )}

          {/* Description */}
          <div>
            <div className="issue-section-label">Descripción</div>
            <div className="issue-text">{issue.description}</div>
          </div>

          {/* Impact */}
          {issue.impact && (
            <div>
              <div className="issue-section-label">Impacto</div>
              <div className="issue-impact">⚠️ {issue.impact}</div>
            </div>
          )}

          {/* Evidence */}
          {issue.evidence && (
            <div>
              <div className="issue-section-label">Evidencia</div>
              <div className="issue-evidence">{issue.evidence}</div>
            </div>
          )}

          {/* Fix */}
          {fix && (
            <div className="fix-block">
              <div className="fix-header">
                <span className="fix-label">🔧 Fix Sugerido</span>
              </div>
              <div className="fix-summary">{fix.summary}</div>
              {(fix.before || fix.after) && (
                <>
                  <div className="code-tabs">
                    {fix.before && (
                      <div className={`code-tab ${activeTab === 'before' ? 'active' : ''}`} onClick={() => setActiveTab('before')}>
                        Antes
                      </div>
                    )}
                    {fix.after && (
                      <div className={`code-tab ${activeTab === 'after' ? 'active' : ''}`} onClick={() => setActiveTab('after')}>
                        Después
                      </div>
                    )}
                  </div>
                  {activeTab === 'before' && fix.before && <CodeBlock code={fix.before} label={`${issue.id}-before`} />}
                  {activeTab === 'after' && fix.after && <CodeBlock code={fix.after} label={`${issue.id}-after`} />}
                </>
              )}
              {fix.notes && (
                <div style={{ padding: '10px 14px', borderTop: '1px solid rgba(255,255,255,0.07)', fontSize: 12, color: '#64748b', fontStyle: 'italic' }}>
                  💡 {fix.notes}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
