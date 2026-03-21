"use client";

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { History, CheckCircle2, FileText, Database, ShieldCheck } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ProvenanceInfo } from '@/types/contracts';

interface ProvenancePanelProps {
  provenance: ProvenanceInfo;
}

export function ProvenancePanel({ provenance }: ProvenancePanelProps) {
  const getQualityVariant = (decision: string) => {
    switch (decision.toLowerCase()) {
      case 'accept': return 'success';
      case 'warning': return 'warning';
      case 'reject': return 'destructive';
      default: return 'outline';
    }
  };

  return (
    <Card className="h-full bg-muted/10">
      <CardHeader className="py-4 border-b">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-primary" />
          <CardTitle className="text-sm font-semibold uppercase tracking-wider">
            Trazabilidad del Análisis (Medallion v3.0)
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent className="pt-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <FileText className="w-3 h-3" /> Origen
            </div>
            <p className="text-sm font-semibold truncate">{provenance.source}</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <Database className="w-3 h-3" /> Método de Ingesta
            </div>
            <p className="text-sm font-semibold capitalize">{provenance.ingestion_method}</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
              <ShieldCheck className="w-3 h-3" /> Decisión de Calidad
            </div>
            <Badge variant={getQualityVariant(provenance.quality_decision)} className="uppercase text-[10px]">
              {provenance.quality_decision}
            </Badge>
          </div>
        </div>

        <div className="space-y-3">
          <h4 className="text-xs font-bold text-muted-foreground uppercase">Pasos del Pipeline</h4>
          <div className="relative pl-4 space-y-4">
            <div className="absolute left-0 top-1 bottom-1 w-[2px] bg-muted" />
            
            {provenance.processing_steps.map((step, index) => (
              <div key={index} className="relative">
                <div className="absolute -left-[19px] top-1 w-2.5 h-2.5 rounded-full bg-primary border-2 border-background" />
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium">{step}</span>
                  <CheckCircle2 className="w-3 h-3 text-green-500" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {provenance.affected_columns.length > 0 && (
          <div className="space-y-2 pt-2 border-t">
            <h4 className="text-xs font-bold text-muted-foreground uppercase">Columnas con Transformaciones</h4>
            <div className="flex flex-wrap gap-1">
              {provenance.affected_columns.map(col => (
                <span key={col} className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                  {col}
                </span>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
