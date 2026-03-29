import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Dashboard from './components/Dashboard';
import BugsSection from './components/BugsSection';
import RefactoringSection from './components/RefactoringSection';
import AIMLSection from './components/AIMLSection';
import ActionPlanSection from './components/ActionPlanSection';
import ArchitectureSection from './components/ArchitectureSection';
import NextStepsSection from './components/NextStepsSection';
import FrontendPlanSection from './components/FrontendPlanSection';
import Sidebar from './components/Sidebar';
import LoadingScreen from './components/LoadingScreen';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function App() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeSection, setActiveSection] = useState('dashboard');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const fetchReport = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${BACKEND_URL}/api/report`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  const getSectionData = (key) => {
    if (!report) return null;
    return report.sections.find(s => s.key === key);
  };

  const handleExport = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/report/export.md`);
      const text = await res.text();
      const blob = new Blob([text], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'data-x-audit-report.md';
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed', err);
    }
  };

  if (loading) return <LoadingScreen />;

  if (error) return (
    <div className="error-screen" data-testid="error-screen">
      <div className="error-content">
        <div className="error-icon">⚠️</div>
        <h2>Error al cargar el reporte</h2>
        <p>{error}</p>
        <button onClick={fetchReport} className="retry-btn" data-testid="retry-btn">
          Reintentar
        </button>
      </div>
    </div>
  );

  const renderSection = () => {
    switch (activeSection) {
      case 'dashboard': return <Dashboard report={report} onSectionChange={setActiveSection} />;
      case 'architecture': return <ArchitectureSection data={getSectionData('architecture')} />;
      case 'bugs': return <BugsSection data={getSectionData('bugs')} />;
      case 'refactoring': return <RefactoringSection data={getSectionData('refactoring')} />;
      case 'ai_ml': return <AIMLSection data={getSectionData('ai_ml')} />;
      case 'action_plan': return <ActionPlanSection data={getSectionData('action_plan')} />;
      case 'next_steps': return <NextStepsSection data={getSectionData('next_steps')} />;
      case 'frontend': return <FrontendPlanSection data={getSectionData('frontend')} />;
      default: return <Dashboard report={report} onSectionChange={setActiveSection} />;
    }
  };

  return (
    <div className="app-root" data-testid="app-root">
      <Sidebar
        activeSection={activeSection}
        onSectionChange={setActiveSection}
        meta={report?.meta}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(c => !c)}
        onExport={handleExport}
      />
      <main className={`main-content ${sidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
            className="section-wrapper"
          >
            {renderSection()}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
