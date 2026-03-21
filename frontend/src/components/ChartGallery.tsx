"use client";

import { ChartSpec } from '@/types/contracts';
import { ChartRenderer } from './ChartRenderer';

interface ChartGalleryProps {
  charts: ChartSpec[];
}

export function ChartGallery({ charts }: ChartGalleryProps) {
  if (charts.length === 0) {
    return (
      <div className="p-8 text-center border rounded-lg bg-muted/20">
        <p className="text-muted-foreground italic">No hay visualizaciones disponibles para este conjunto de datos.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {charts.map(chart => (
        <ChartRenderer key={chart.chart_id} spec={chart} />
      ))}
    </div>
  );
}
