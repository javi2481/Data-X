"use client";

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { FileUploader } from '@/components/FileUploader';
import { FindingsList } from '@/components/FindingsList';
import { ChartGallery } from '@/components/ChartGallery';
import { DataPreviewTable } from '@/components/DataPreviewTable';
import { DataHealthDashboard } from '@/components/DataHealthDashboard';
import { ColumnProfilesTable } from '@/components/ColumnProfilesTable';
import { ProvenancePanel } from '@/components/ProvenancePanel';
import { QueryPanel } from '@/components/QueryPanel';
import { DocumentContextPanel } from '@/components/DocumentContextPanel';
import { SessionHistory } from '@/components/SessionHistory';
import { StateFeedback, SkeletonLoader } from '@/components/StateFeedback';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Database, 
  LayoutDashboard, 
  Search, 
  AlertCircle, 
  RefreshCcw, 
  FileText,
  BarChart3,
  Table as TableIcon,
  ShieldCheck,
  History as HistoryIcon,
  BookOpen
} from 'lucide-react';
import { ExportMenu } from '@/components/ExportMenu';
import { SessionResponse, AnalysisReport } from '@/types/contracts';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';
import { AuthGuard } from '@/components/AuthGuard';
import { UserMenu } from '@/components/UserMenu';

type WorkspaceState = 'empty' | 'uploading' | 'loading_report' | 'ready' | 'error';

function WorkspaceContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const sessionIdParam = searchParams.get('session_id');

  const [state, setState] = useState<WorkspaceState>('empty');
  const [session, setSession] = useState<SessionResponse | null>(null);
  const [report, setReport] = useState<AnalysisReport | null>(null);
  const [error, setError] = useState<{title: string, desc: string} | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');

  const loadReport = useCallback(async (sid: string) => {
    setState('loading_report');
    try {
      const data = await api.getReport(sid);
      setReport(data);
      setState('ready');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'No se pudo completar el análisis automático.';
      setError({ 
        title: 'Error al generar reporte', 
        desc: message 
      });
      setState('error');
    }
  }, []);

  const loadSession = useCallback(async (sid: string) => {
    setState('uploading');
    try {
      const data = await api.getSession(sid);
      setSession(data);
      if (data.status === 'ready') {
        loadReport(sid);
      } else if (data.status === 'error') {
        setError({ title: 'Error en la sesión', desc: 'El procesamiento del archivo falló.' });
        setState('error');
      } else {
        // FE-002: Polling con límite y exponential backoff
        const MAX_ATTEMPTS = 30; // Máximo 30 intentos
        const BASE_DELAY = 2000; // 2 segundos inicial
        const MAX_DELAY = 10000; // Máximo 10 segundos entre intentos
        let attempts = 0;
        
        const poll = async () => {
          attempts++;
          
          if (attempts > MAX_ATTEMPTS) {
            setError({ 
              title: 'Tiempo de espera agotado', 
              desc: 'El procesamiento está tomando más tiempo del esperado. Intenta refrescar la página.' 
            });
            setState('error');
            return;
          }
          
          try {
            const d = await api.getSession(sid);
            setSession(d);
            
            if (d.status === 'ready') {
              loadReport(sid);
            } else if (d.status === 'error') {
              setError({ title: 'Error', desc: 'Fallo al procesar' });
              setState('error');
            } else {
              // Exponential backoff: 2s, 4s, 8s, hasta MAX_DELAY
              const delay = Math.min(BASE_DELAY * Math.pow(1.5, attempts - 1), MAX_DELAY);
              setTimeout(poll, delay);
            }
          } catch (e) {
            console.error("Polling error", e);
            // Si falla el request, reintentar con backoff
            const delay = Math.min(BASE_DELAY * Math.pow(1.5, attempts - 1), MAX_DELAY);
            setTimeout(poll, delay);
          }
        };
        
        setTimeout(poll, BASE_DELAY);
      }
    } catch {
      setError({ 
        title: 'Sesión no encontrada', 
        desc: 'La sesión solicitada no existe o ha expirado.' 
      });
      setState('error');
    }
  }, [loadReport]);

  useEffect(() => {
    if (sessionIdParam && state === 'empty') {
      const initSession = async () => {
        await loadSession(sessionIdParam);
      };
      initSession();
    }
  }, [sessionIdParam, state, loadSession]);

  const handleUploadComplete = (sessionRes: SessionResponse) => {
    setSession(sessionRes);
    router.push(`/workspace?session_id=${sessionRes.session_id}`);
    loadReport(sessionRes.session_id);
  };

  const handleUploadError = (err: unknown) => {
    const message = err instanceof Error ? err.message : 'El motor no pudo procesar el archivo correctamente.';
    setError({ 
      title: 'Error de procesamiento', 
      desc: message 
    });
    setState('error');
  };

  const handleSelectSession = (sid: string) => {
    router.push(`/workspace?session_id=${sid}`);
    loadSession(sid);
  };

  const resetWorkspace = () => {
    setSession(null);
    setReport(null);
    setError(null);
    setState('empty');
    router.push('/workspace');
  };

  const isLoading = state === 'uploading' || state === 'loading_report';

  return (
    <div className="container py-8 px-4 md:px-6 mx-auto max-w-7xl min-h-[calc(100vh-8rem)]">
      <div className="flex flex-col space-y-8">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
              <LayoutDashboard className="w-8 h-8 text-primary" />
              Workspace
            </h1>
            <p className="text-muted-foreground">
              {session 
                ? `Analizando: ${session.source_metadata.filename}` 
                : isLoading 
                  ? 'Iniciando procesamiento...'
                  : 'Sube un dataset para comenzar el análisis determinístico Medallion.'}
            </p>
          </div>
          
          <div className="flex items-center gap-4">
            {session && (
              <div className="flex items-center gap-3">
                {state === 'ready' && report && (
                  <ExportMenu 
                    report={report} 
                    filename={(session.source_metadata.filename as string) || 'dataset.csv'} 
                  />
                )}
                <div className="hidden sm:flex items-center gap-2 bg-muted px-3 py-1.5 rounded-full text-xs font-medium border border-border">
                  <Database className="w-3.5 h-3.5 text-primary" />
                  {session.session_id.substring(0, 8)}...
                </div>
                <Button variant="outline" size="sm" onClick={resetWorkspace} className="gap-2">
                  <RefreshCcw className="w-4 h-4" />
                  Nuevo Análisis
                </Button>
              </div>
            )}
            <UserMenu />
          </div>
        </div>

        {error && (
          <StateFeedback 
            type="error" 
            title={error.title} 
            description={error.desc} 
            onRetry={resetWorkspace}
          />
        )}

        {isLoading && !error && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 p-4 bg-muted/50 rounded-lg border border-dashed animate-pulse">
              <RefreshCcw className="w-5 h-5 text-primary animate-spin" />
              <span className="text-sm font-medium">
                {state === 'uploading' ? 'Ingestando y validando esquema...' : 'Generando hallazgos enriquecidos con IA...'}
              </span>
            </div>
            <SkeletonLoader />
          </div>
        )}

        {state === 'empty' && !error && !isLoading && (
          <div className="max-w-5xl mx-auto w-full py-12 grid grid-cols-1 md:grid-cols-3 gap-8 items-start animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="md:col-span-2">
              <Card className="border-2 shadow-2xl overflow-hidden">
                <div className="h-1.5 bg-gradient-to-r from-primary to-blue-600" />
                <CardHeader className="text-center pt-10">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Search className="w-8 h-8 text-primary" />
                  </div>
                  <CardTitle className="text-2xl font-bold">Inicia tu Análisis</CardTitle>
                  <CardDescription className="max-w-sm mx-auto text-base">
                    Carga un archivo CSV. Nuestro pipeline procesará la estructura y detectará hallazgos automáticamente.
                  </CardDescription>
                </CardHeader>
                <CardContent className="pb-12 px-10">
                  <FileUploader 
                    onUploadComplete={handleUploadComplete} 
                    onUploadError={handleUploadError} 
                  />
                </CardContent>
              </Card>
            </div>
            <div className="md:col-span-1 space-y-6">
              <SessionHistory onSelectSession={handleSelectSession} />
            </div>
          </div>
        )}

        {state === 'ready' && report && (
          <div className="grid gap-8 lg:grid-cols-12 items-start">
            {/* Sidebar Navigation */}
            <div className="lg:col-span-3 sticky top-24 space-y-2">
              <nav className="flex flex-col space-y-1">
                <NavItem 
                  label="Resumen General" 
                  icon={LayoutDashboard} 
                  active={activeTab === 'overview'} 
                  onClick={() => setActiveTab('overview')} 
                />
                <NavItem 
                  label="Hallazgos (Findings)" 
                  icon={ShieldCheck} 
                  count={report.findings.length}
                  active={activeTab === 'findings'} 
                  onClick={() => setActiveTab('findings')} 
                />
                <NavItem 
                  label="Visualizaciones" 
                  icon={BarChart3} 
                  count={report.chart_specs.length}
                  active={activeTab === 'charts'} 
                  onClick={() => setActiveTab('charts')} 
                />
                <NavItem 
                  label="Perfiles de Columna" 
                  icon={TableIcon} 
                  active={activeTab === 'columns'} 
                  onClick={() => setActiveTab('columns')} 
                />
                <NavItem 
                  label="Vista Previa" 
                  icon={FileText} 
                  active={activeTab === 'preview'} 
                  onClick={() => setActiveTab('preview')} 
                />
                <NavItem 
                  label="Documento" 
                  icon={BookOpen} 
                  count={report.document_tables?.length || 0}
                  active={activeTab === 'document'} 
                  onClick={() => setActiveTab('document')} 
                />
                <NavItem 
                  label="Trazabilidad" 
                  icon={HistoryIcon} 
                  active={activeTab === 'provenance'} 
                  onClick={() => setActiveTab('provenance')} 
                />
              </nav>

              <div className="pt-4 border-t">
                <SessionHistory 
                  onSelectSession={handleSelectSession} 
                  currentSessionId={session?.session_id} 
                />
              </div>

              <Card className="mt-6 bg-primary/5 border-primary/10">
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertCircle className="w-4 h-4 text-primary" />
                    <span className="text-xs font-bold uppercase">Estado de Calidad</span>
                  </div>
                  <p className="text-sm font-semibold capitalize">{report.provenance.quality_decision}</p>
                  <p className="text-[10px] text-muted-foreground mt-1 leading-tight">
                    Basado en un análisis de {report.dataset_overview.total_null_percent.toFixed(1)}% de nulos y {report.dataset_overview.duplicate_percent.toFixed(1)}% de duplicados.
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Main Content Area */}
            <div className="lg:col-span-9 space-y-10 pb-20">
              {activeTab === 'overview' && (
                <section className="space-y-6 animate-in fade-in duration-300">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <LayoutDashboard className="w-5 h-5 text-primary" />
                    Resumen del Dataset
                  </h2>

                  <DataHealthDashboard report={report} />
                </section>
              )}

              {activeTab === 'findings' && (
                <section className="space-y-6 animate-in fade-in duration-300">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <ShieldCheck className="w-5 h-5 text-primary" />
                    Hallazgos de Análisis (Findings)
                  </h2>
                  <FindingsList findings={report.findings} enrichedExplanations={report.enriched_explanations} />
                </section>
              )}

              {activeTab === 'charts' && (
                <section className="space-y-6 animate-in fade-in duration-300">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-primary" />
                    Galería de Visualizaciones
                  </h2>
                  <ChartGallery charts={report.chart_specs} />
                </section>
              )}

              {activeTab === 'columns' && (
                <section className="space-y-6 animate-in fade-in duration-300">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <TableIcon className="w-5 h-5 text-primary" />
                    Perfiles Detallados por Columna
                  </h2>
                  <ColumnProfilesTable profiles={report.column_profiles} />
                </section>
              )}

              {activeTab === 'preview' && (
                <section className="space-y-6 animate-in fade-in duration-300">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <FileText className="w-5 h-5 text-primary" />
                    Vista Previa de Datos (Silver)
                  </h2>
                  <DataPreviewTable data={report.data_preview} columnProfiles={report.column_profiles} />
                </section>
              )}

              {activeTab === 'provenance' && (
                <section className="space-y-6 animate-in fade-in duration-300">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <HistoryIcon className="w-5 h-5 text-primary" />
                    Trazabilidad del Proceso
                  </h2>
                  <ProvenancePanel provenance={report.provenance} />
                </section>
              )}

              {activeTab === 'document' && (
                <section className="space-y-6 animate-in fade-in duration-300">
                  <h2 className="text-xl font-bold flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-primary" />
                    Vista Documental
                  </h2>
                  <DocumentContextPanel report={report} />
                </section>
              )}

              <QueryPanel sessionId={report.session_id} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function WorkspacePage() {
  return (
    <AuthGuard>
      <Suspense fallback={<SkeletonLoader />}>
        <WorkspaceContent />
      </Suspense>
    </AuthGuard>
  );
}

function NavItem({ 
  label, 
  icon: Icon, 
  active, 
  onClick, 
  count 
}: { 
  label: string; 
  icon: React.ElementType; 
  active: boolean; 
  onClick: () => void;
  count?: number;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-colors",
        active 
          ? "bg-primary text-primary-foreground shadow-sm" 
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      <div className="flex items-center gap-2">
        <Icon className="w-4 h-4" />
        {label}
      </div>
      {count !== undefined && (
        <span className={cn(
          "text-[10px] px-1.5 py-0.5 rounded-full font-bold",
          active ? "bg-primary-foreground text-primary" : "bg-muted-foreground/20"
        )}>
          {count}
        </span>
      )}
    </button>
  );
}
