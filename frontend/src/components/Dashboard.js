import React from 'react';
import { PieChart, Pie, Cell, Tooltip, BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Legend } from 'recharts';

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
};

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: '#1c2030', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8, padding: '10px 14px' }}>
        <p style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 600 }}>{payload[0].name}</p>
        <p style={{ color: payload[0].fill, fontSize: 13 }}>{payload[0].value} issues</p>
      </div>
    );
  }
  return null;
};

export default function Dashboard({ report, onSectionChange }) {
  if (!report) return null;
  const { meta, sections } = report;
  const stats = meta.stats;

  const pieData = [
    { name: 'Crítico', value: stats.critical, color: SEVERITY_COLORS.critical },
    { name: 'Alto', value: stats.high, color: SEVERITY_COLORS.high },
    { name: 'Medio', value: stats.medium, color: SEVERITY_COLORS.medium },
    { name: 'Bajo', value: stats.low, color: SEVERITY_COLORS.low },
  ];

  const barData = [
    { name: 'Bugs', critical: 4, high: 4, medium: 3, low: 2 },
    { name: 'Refactor', critical: 0, high: 1, medium: 3, low: 1 },
    { name: 'IA/ML', critical: 2, high: 1, medium: 2, low: 1 },
  ];

  // Collect top critical + high issues
  const topIssues = [];
  for (const sec of sections) {
    for (const issue of (sec.issues || [])) {
      if (issue.severity === 'critical' || issue.severity === 'high') {
        topIssues.push({ ...issue, sectionKey: sec.key });
      }
    }
  }
  topIssues.sort((a, b) => (a.severity === 'critical' ? -1 : 1));

  const sectionNav = [
    { key: 'architecture', icon: '📐', title: 'Arquitectura', count: 'Análisis completo' },
    { key: 'bugs', icon: '🐛', title: 'Bugs & Vulnerabilidades', count: `${(sections.find(s=>s.key==='bugs')?.issues||[]).length} issues` },
    { key: 'refactoring', icon: '⚙️', title: 'Refactorización', count: `${(sections.find(s=>s.key==='refactoring')?.issues||[]).length} mejoras` },
    { key: 'ai_ml', icon: '🧠', title: 'Optimización IA/ML', count: `${(sections.find(s=>s.key==='ai_ml')?.issues||[]).length} optimizaciones` },
    { key: 'action_plan', icon: '🎯', title: 'Plan de Acción', count: 'Priorizado' },
  ];

  return (
    <div className="dashboard" data-testid="dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div>
          <h1 className="dashboard-title">Auditoría de Código — Data-X</h1>
          <p className="dashboard-subtitle">{meta.summary.substring(0, 140)}...</p>
        </div>
        <div className="repo-badge">
          <span>🔗</span>
          <a href={meta.repo_url} target="_blank" rel="noreferrer">{meta.repo}</a>
        </div>
      </div>

      {/* Commit info */}
      <div className="commit-info">
        <span>Rama: <strong style={{color: '#e2e8f0'}}>{meta.branch}</strong></span>
        <span>Commit: <code>{meta.commit.substring(0, 8)}</code></span>
        <span>Fecha: <strong style={{color: '#e2e8f0'}}>{meta.analysis_date}</strong></span>
        <span>Análisis por: <strong style={{color: '#e2e8f0'}}>{meta.analyst}</strong></span>
        <span>Archivos analizados: <strong style={{color: '#e2e8f0'}}>{meta.stats.files_analyzed}</strong></span>
        <span>Líneas: <strong style={{color: '#e2e8f0'}}>{meta.stats.lines_analyzed.toLocaleString()}</strong></span>
      </div>

      {/* Stats */}
      <div className="stats-grid" data-testid="stats-grid">
        <div className="stat-card" onClick={() => onSectionChange('bugs')}>
          <div className="stat-value total" style={{fontSize: 36}}>{stats.total_issues}</div>
          <div className="stat-label">Total Issues</div>
        </div>
        <div className="stat-card critical" onClick={() => onSectionChange('bugs')}>
          <div className="stat-value critical">{stats.critical}</div>
          <div className="stat-label">🔴 Crítico</div>
        </div>
        <div className="stat-card high" onClick={() => onSectionChange('bugs')}>
          <div className="stat-value high">{stats.high}</div>
          <div className="stat-label">🟠 Alto</div>
        </div>
        <div className="stat-card medium" onClick={() => onSectionChange('refactoring')}>
          <div className="stat-value medium">{stats.medium}</div>
          <div className="stat-label">🟡 Medio</div>
        </div>
        <div className="stat-card low" onClick={() => onSectionChange('ai_ml')}>
          <div className="stat-value low">{stats.low}</div>
          <div className="stat-label">🔵 Bajo</div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-row">
        <div className="chart-card">
          <div className="chart-title">Distribución por Severidad</div>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={3} dataKey="value">
                {pieData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                iconType="circle"
                iconSize={8}
                formatter={(value) => <span style={{color: '#94a3b8', fontSize: 12}}>{value}</span>}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <div className="chart-title">Issues por Sección</div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={barData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#1c2030', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 8 }}
                labelStyle={{ color: '#e2e8f0', fontSize: 12 }}
                itemStyle={{ fontSize: 12 }}
              />
              <Bar dataKey="critical" stackId="a" fill={SEVERITY_COLORS.critical} radius={[0,0,0,0]} />
              <Bar dataKey="high" stackId="a" fill={SEVERITY_COLORS.high} />
              <Bar dataKey="medium" stackId="a" fill={SEVERITY_COLORS.medium} />
              <Bar dataKey="low" stackId="a" fill={SEVERITY_COLORS.low} radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Nav */}
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 12 }}>Explorar Secciones</div>
        <div className="quick-nav">
          {sectionNav.map(item => (
            <div key={item.key} className="quick-nav-card" onClick={() => onSectionChange(item.key)} data-testid={`quick-nav-${item.key}`}>
              <div className="quick-nav-icon">{item.icon}</div>
              <div className="quick-nav-text">
                <div className="quick-nav-title">{item.title}</div>
                <div className="quick-nav-count">{item.count}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Critical Issues */}
      <div className="top-issues">
        <div className="top-issues-header">
          <div className="top-issues-title">🔴 Issues Críticos y Altos</div>
          <span className="view-all-link" onClick={() => onSectionChange('bugs')}>Ver todos →</span>
        </div>
        {topIssues.slice(0, 8).map((issue) => (
          <div key={issue.id} className="top-issue-row" data-testid={`top-issue-${issue.id}`}>
            <span className="top-issue-id">{issue.id}</span>
            <span className="top-issue-title">{issue.title}</span>
            <span className="top-issue-file">{issue.file?.split('/').slice(-1)[0]}</span>
            <span className={`severity-badge ${issue.severity}`}>{issue.severity}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
