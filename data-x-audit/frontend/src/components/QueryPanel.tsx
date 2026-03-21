import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MessageSquare, Send, Sparkles, AlertCircle, FileSearch } from 'lucide-react';
import { api } from '@/lib/api';
import { AnalyzeResponse, EvidenceSource } from '@/types/contracts';
import { Badge } from '@/components/ui/badge';
import { FindingCard } from './FindingCard';
import { EvidencePanel } from './EvidencePanel';
import { SuggestedQuestions } from './SuggestedQuestions';

interface QueryPanelProps {
  sessionId: string;
}

export const QueryPanel: React.FC<QueryPanelProps> = ({ sessionId }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showDetailedSources, setShowDetailedSources] = useState(false);

  const handleSend = async () => {
    if (!query.trim() || loading) return;

    setLoading(true);
    setError(null);
    try {
      const response = await api.analyze(sessionId, query);
      setResult(response);
      setQuery('');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Error al procesar la consulta';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const resolveSource = (source: string | EvidenceSource) => {
    if (typeof source === 'string') {
      return { sourceId: source, sourceType: 'finding' as const };
    }
    return { sourceId: source.source_id, sourceType: source.source_type };
  };

  return (
    <div className="space-y-6 mt-12 pb-12">
      <Card className="border-indigo-200 shadow-sm overflow-hidden">
        <CardHeader className="bg-indigo-50/50 pb-4">
          <CardTitle className="text-lg flex items-center gap-2 text-indigo-900">
            <MessageSquare className="h-5 w-5" />
            Consulta Inteligente (IA)
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="flex gap-2">
            <Input
              placeholder="Preguntá sobre tu dataset (ej: ¿Cuáles son las columnas más importantes?)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={loading}
              className="flex-1"
            />
            <Button 
              onClick={handleSend} 
              disabled={loading || !query.trim()}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              {loading ? <Sparkles className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              <span className="ml-2 hidden sm:inline">Consultar</span>
            </Button>
          </div>
          {error && (
            <div className="mt-3 text-red-600 text-sm flex items-center gap-1">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Sprint 2: Suggested Questions */}
      {!result && (
        <SuggestedQuestions
          sessionId={sessionId}
          onSelectQuestion={(question) => {
            setQuery(question);
          }}
        />
      )}

      {result && (
        <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
          <Card className="border-l-4 border-l-green-500 shadow-md">
            <CardHeader className="pb-2">
              <div className="flex justify-between items-start">
                <CardTitle className="text-md text-gray-500 font-normal italic">
                  Respuesta a: &quot;{result.query}&quot;
                </CardTitle>
                <Badge variant={result.confidence === 'high' ? 'default' : result.confidence === 'medium' ? 'secondary' : 'outline'} className={
                  result.confidence === 'high' ? 'bg-green-100 text-green-800 hover:bg-green-100' :
                  result.confidence === 'medium' ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100' :
                  'bg-red-100 text-red-800 hover:bg-red-100'
                }>
                  Confianza: {result.confidence}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                {result.answer}
              </p>

              {result.sources && result.sources.length > 0 && (
                <div className="mt-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                      <Sparkles className="h-4 w-4 text-indigo-500" />
                      Fuentes vinculadas ({result.sources.length})
                    </h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowDetailedSources(!showDetailedSources)}
                      className="text-xs text-indigo-600 hover:text-indigo-700"
                    >
                      <FileSearch className="h-3 w-3 mr-1" />
                      {showDetailedSources ? 'Vista simple' : 'Ver provenance'}
                    </Button>
                  </div>
                  
                  {showDetailedSources ? (
                    <EvidencePanel 
                      sources={result.sources}
                      onSourceClick={(sourceId) => {
                        const element = document.getElementById(sourceId);
                        if (element) {
                          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                          element.classList.add('ring-2', 'ring-indigo-500');
                          setTimeout(() => element.classList.remove('ring-2', 'ring-indigo-500'), 3000);
                        }
                      }}
                    />
                  ) : (
                    <div className="flex flex-wrap gap-2">
                      {result.sources.map((source, index) => {
                        const { sourceId, sourceType } = resolveSource(source);
                        const finding = result.relevant_findings.find(f => f.finding_id === sourceId);
                        const badgeKey = typeof source === 'string' ? source : `${source.source_type}-${source.source_id}-${index}`;
                        const hasLocation = typeof source !== 'string' && source.location;
                        return (
                          <Badge 
                            key={badgeKey} 
                            variant="secondary" 
                            className="cursor-pointer hover:bg-indigo-100 hover:text-indigo-900 transition-colors py-1 px-2 text-[10px] flex items-center gap-1"
                            onClick={() => {
                              const element = document.getElementById(sourceId);
                              if (element) {
                                element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                element.classList.add('ring-2', 'ring-indigo-500');
                                setTimeout(() => element.classList.remove('ring-2', 'ring-indigo-500'), 3000);
                              }
                            }}
                          >
                            {finding?.title || `${sourceType}: ${sourceId.split('_')[1] || sourceId}`}
                            {hasLocation && source.location?.page && (
                              <span className="text-indigo-500 ml-1">p.{source.location.page}</span>
                            )}
                          </Badge>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {result.relevant_findings.length > 0 && (
                <div className="mt-6 space-y-3">
                  <h4 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                    Contexto detectado
                  </h4>
                  <div className="grid grid-cols-1 gap-3">
                    {result.relevant_findings.slice(0, 2).map((f) => (
                      <FindingCard key={f.finding_id} finding={f} />
                    ))}
                    {result.relevant_findings.length > 2 && (
                      <p className="text-xs text-center text-muted-foreground">
                        + {result.relevant_findings.length - 2} hallazgos adicionales usados como contexto
                      </p>
                    )}
                  </div>
                </div>
              )}
              
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setResult(null)}
                className="mt-4 text-gray-400 hover:text-gray-600"
              >
                Limpiar respuesta
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};
