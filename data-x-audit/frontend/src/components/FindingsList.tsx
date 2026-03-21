"use client";

import { Finding } from '@/types/contracts';
import { FindingCard } from './FindingCard';
import { Badge } from '@/components/ui/badge';
import { Database, AlertTriangle, TrendingUp, Sparkles, FileSearch } from 'lucide-react';

interface FindingsListProps {
  findings: Finding[];
  enrichedExplanations?: Record<string, string>;
}

export function FindingsList({ findings, enrichedExplanations = {} }: FindingsListProps) {
  if (findings.length === 0) {
    return (
      <div className="p-8 text-center border rounded-lg bg-muted/20">
        <p className="text-muted-foreground italic">No se detectaron problemas ni hallazgos significativos.</p>
      </div>
    );
  }

  const categories = [
    { id: 'data_gap', label: 'Datos faltantes', icon: Database },
    { id: 'reliability_risk', label: 'Riesgos de confiabilidad', icon: AlertTriangle },
    { id: 'pattern', label: 'Patrones detectados', icon: TrendingUp },
    { id: 'opportunity', label: 'Oportunidades', icon: Sparkles },
    { id: 'quality_issue', label: 'Calidad del dataset', icon: FileSearch },
  ] as const;

  const severityOrder: Record<string, number> = { critical: 0, important: 1, suggestion: 2, insight: 3 };

  const groupedFindings = categories.map(cat => {
    const items = findings
      .filter(f => f.category === cat.id)
      .map(f => ({
        ...f,
        enriched_explanation: f.enriched_explanation || enrichedExplanations[f.finding_id]
      }))
      .sort((a, b) => (severityOrder[a.severity] ?? 99) - (severityOrder[b.severity] ?? 99));
    
    return { ...cat, items };
  }).filter(group => group.items.length > 0);

  return (
    <div className="space-y-8">
      {groupedFindings.map(group => (
        <div key={group.id} className="space-y-4">
          <div className="flex items-center justify-between border-b pb-2">
            <div className="flex items-center gap-2">
              <group.icon className="w-5 h-5 text-primary" />
              <h3 className="text-lg font-bold tracking-tight">{group.label}</h3>
            </div>
            <Badge variant="secondary" className="rounded-full">
              {group.items.length}
            </Badge>
          </div>
          <div className="grid grid-cols-1 gap-4">
            {group.items.map(finding => (
              <FindingCard key={finding.finding_id} finding={finding} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
