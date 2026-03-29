import React from 'react';

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', icon: '🏗️' },
  { key: 'architecture', label: 'Arquitectura', icon: '📐' },
  { key: 'bugs', label: 'Bugs & Vulnerabilidades', icon: '🐛', badgeType: 'critical' },
  { key: 'refactoring', label: 'Refactorización', icon: '⚙️' },
  { key: 'ai_ml', label: 'Optimización IA/ML', icon: '🧠' },
  { key: 'action_plan', label: 'Plan de Acción', icon: '🞹' },
  { key: 'next_steps', label: 'Siguientes Pasos', icon: '🚀' },
  { key: 'frontend', label: 'Plan Frontend', icon: '💻' },
];

const SEVERITY_COUNTS = { 
  bugs: '13 issues', 
  refactoring: '5 issues', 
  ai_ml: '6 issues', 
  action_plan: '14 acciones',
  next_steps: '4 pasos',
  frontend: '10 issues'
};

export default function Sidebar({ activeSection, onSectionChange, meta, collapsed, onToggleCollapse, onExport }) {
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`} data-testid="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">🔍</div>
        {!collapsed && (
          <div>
            <div className="sidebar-title">Data-X Audit</div>
            <div className="sidebar-subtitle">{meta?.repo || 'javi2481/data-x'}</div>
          </div>
        )}
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(item => (
          <div
            key={item.key}
            className={`nav-item ${activeSection === item.key ? 'active' : ''}`}
            onClick={() => onSectionChange(item.key)}
            data-testid={`nav-${item.key}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {!collapsed && (
              <>
                <span className="nav-label">{item.label}</span>
                {SEVERITY_COUNTS[item.key] && (
                  <span className={`nav-badge badge-${item.badgeType || 'low'}`}>
                    {SEVERITY_COUNTS[item.key]}
                  </span>
                )}
              </>
            )}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        {!collapsed && (
          <button className="export-btn" onClick={onExport} data-testid="export-btn">
            <span>📥</span>
            <span>Exportar Markdown</span>
          </button>
        )}
        <button className="sidebar-collapse-btn" onClick={onToggleCollapse} data-testid="collapse-btn">
          <span style={{fontSize: '14px'}}>{collapsed ? '▶' : '◀'}</span>
          {!collapsed && <span>Colapsar</span>}
        </button>
      </div>
    </aside>
  );
}
