"use client";

import { useState } from 'react';
import { Finding, SourceLocation } from '@/types/contracts';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronUp, CheckCircle2, Zap, Lightbulb, MapPin, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FindingCardProps {
  finding: Finding;
}

export function FindingCard({ finding }: FindingCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-400';
      case 'important': return 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/30 dark:text-orange-400';
      case 'suggestion': return 'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400';
      case 'insight': return 'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'data_gap': return 'Datos faltantes';
      case 'reliability_risk': return 'Riesgo de confiabilidad';
      case 'pattern': return 'Patrón detectado';
      case 'opportunity': return 'Oportunidad';
      case 'quality_issue': return 'Calidad del dataset';
      default: return category;
    }
  };

  return (
    <Card id={finding.finding_id} className={cn("overflow-hidden transition-all", isExpanded ? "ring-1 ring-primary/20 shadow-md" : "shadow-sm")}>
      <CardHeader 
        className="p-4 cursor-pointer hover:bg-muted/30 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge className={cn("capitalize border font-medium", getSeverityColor(finding.severity))}>
                {finding.severity}
              </Badge>
              <Badge variant="outline" className="bg-muted/50 text-muted-foreground border-muted-foreground/20">
                {getCategoryLabel(finding.category)}
              </Badge>
              {finding.confidence === 'verified' && (
                <CheckCircle2 className="w-4 h-4 text-green-500" />
              )}
            </div>
            <CardTitle className="text-lg font-bold leading-tight">{finding.title}</CardTitle>
          </div>
          {isExpanded ? <ChevronUp className="w-5 h-5 text-muted-foreground" /> : <ChevronDown className="w-5 h-5 text-muted-foreground" />}
        </div>
        
        <div className="mt-3 space-y-2">
          <p className="text-sm font-medium leading-snug">
            {finding.what}
          </p>
          <p className="text-xs text-muted-foreground leading-relaxed">
            {finding.so_what}
          </p>
        </div>
      </CardHeader>
      
      <CardContent className="p-4 pt-0 space-y-4">
        <div className={cn("p-3 rounded-lg border flex items-start gap-3", 
          finding.severity === 'critical' || finding.severity === 'important' ? "bg-primary/5 border-primary/20" : "bg-muted/30 border-muted"
        )}>
          <Zap className="w-4 h-4 mt-0.5 text-primary" />
          <div className="space-y-1">
            <p className="text-xs font-bold uppercase tracking-wider text-primary">¿Qué hacer?</p>
            <p className="text-sm font-medium leading-relaxed">{finding.now_what}</p>
          </div>
        </div>

        {isExpanded && (
          <>
            {finding.enriched_explanation && (
              <div className="space-y-2 pt-2 border-t">
                <div className="flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-amber-500" />
                  <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Análisis IA</h4>
                </div>
                <p className="text-sm italic leading-relaxed text-muted-foreground bg-amber-50/50 dark:bg-amber-900/10 p-3 rounded-md">
                  {finding.enriched_explanation}
                </p>
              </div>
            )}

            {finding.evidence.length > 0 && (
              <div className="space-y-2 pt-2 border-t">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Evidencia numérica</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {finding.evidence.map((ev, i) => (
                    <div key={i} className="flex flex-col p-2 rounded border bg-background">
                      <span className="text-[10px] text-muted-foreground uppercase font-semibold">{ev.metric}</span>
                      <div className="flex items-baseline gap-2">
                        <span className="text-base font-bold">{ev.value}</span>
                        {ev.context && <span className="text-[10px] text-muted-foreground">{ev.context}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {finding.affected_columns.length > 0 && (
              <div className="space-y-2 pt-2 border-t">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Columnas involucradas</h4>
                <div className="flex flex-wrap gap-1">
                  {finding.affected_columns.map(col => (
                    <Badge key={col} variant="secondary" className="text-[10px] font-mono">
                      {col}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Sprint 1: Document Provenance */}
            {finding.source_locations && finding.source_locations.length > 0 && (
              <div className="space-y-2 pt-2 border-t">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                  <MapPin className="w-3 h-3" />
                  Ubicación en documento
                </h4>
                <div className="space-y-1">
                  {finding.source_locations.map((loc, i) => (
                    <SourceLocationBadge key={i} location={loc} />
                  ))}
                </div>
              </div>
            )}

            {finding.source_chunk_ids && finding.source_chunk_ids.length > 0 && (
              <div className="space-y-2 pt-2 border-t">
                <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                  <FileText className="w-3 h-3" />
                  Fragmentos relacionados
                </h4>
                <div className="flex flex-wrap gap-1">
                  {finding.source_chunk_ids.map(chunkId => (
                    <Badge key={chunkId} variant="outline" className="text-[10px] font-mono bg-indigo-50 dark:bg-indigo-900/20">
                      {chunkId}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Helper component to display a SourceLocation as a compact badge
 */
function SourceLocationBadge({ location }: { location: SourceLocation }) {
  const parts: string[] = [];
  
  if (location.page) {
    parts.push(`Pág. ${location.page}`);
  }
  
  if (location.heading) {
    parts.push(location.heading);
  } else if (location.section_path && location.section_path.length > 0) {
    parts.push(location.section_path[location.section_path.length - 1]);
  }
  
  if (location.table_id) {
    parts.push(`Tabla: ${location.table_id}`);
  }
  
  if (parts.length === 0) {
    return null;
  }
  
  return (
    <div className="flex items-center gap-1 text-xs text-muted-foreground bg-muted/50 px-2 py-1 rounded">
      <MapPin className="w-3 h-3 text-indigo-500" />
      <span>{parts.join(' • ')}</span>
      {location.bbox && (
        <span className="text-[10px] font-mono text-muted-foreground/60 ml-1">
          [bbox]
        </span>
      )}
    </div>
  );
}
