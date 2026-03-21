"use client";

import React, { useState } from 'react';
import { 
  Card 
} from "@/components/ui/card";
import { 
  AlertCircle, 
  CheckCircle2, 
  Lightbulb, 
  ChevronDown, 
  ChevronUp,
  LayoutDashboard,
  ShieldAlert
} from "lucide-react";
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer 
} from 'recharts';
import { Badge } from "@/components/ui/badge";
import { AnalysisReport } from "@/types/contracts";
import { CostIndicator } from "./CostIndicator";

interface DataHealthDashboardProps {
  report: AnalysisReport;
}

export function DataHealthDashboard({ report }: DataHealthDashboardProps) {
  const [showTechnical, setShowTechnical] = useState(false);
  const { dataset_overview, findings, executive_summary } = report;

  // 1. Calcular Health Score
  const criticalCount = findings.filter(f => f.severity === 'critical').length;
  const importantCount = findings.filter(f => f.severity === 'important').length;
  
  const scoreDeduction = (dataset_overview.total_null_percent * 0.5) + 
                         (dataset_overview.duplicate_percent * 0.3) + 
                         (criticalCount * 10) + 
                         (importantCount * 5);
  
  const healthScore = Math.max(0, Math.min(100, 100 - scoreDeduction));
  
  let colorClass = "text-green-500";
  let strokeColor = "#22c55e";
  let badgeVariant: "default" | "secondary" | "destructive" | "outline" = "outline";
  let healthStatus = "Datos Confiables";

  if (healthScore < 50) {
    colorClass = "text-red-500";
    strokeColor = "#ef4444";
    badgeVariant = "destructive";
    healthStatus = "Riesgo Crítico";
  } else if (healthScore < 80) {
    colorClass = "text-yellow-500";
    strokeColor = "#eab308";
    badgeVariant = "secondary";
    healthStatus = "Atención Requerida";
  }

  const chartData = [
    { value: healthScore },
    { value: 100 - healthScore }
  ];

  return (
    <Card className={`p-6 border-l-4 ${healthScore >= 80 ? 'border-green-500' : healthScore >= 50 ? 'border-yellow-500' : 'border-red-500'} bg-card shadow-lg transition-all duration-300`}>
      <div className="flex flex-col lg:flex-row gap-8">
        
        {/* LADO IZQUIERDO: INDICADOR DE SALUD */}
        <div className="flex flex-col items-center gap-4 w-48 shrink-0">
          <div className="relative w-32 h-32">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={35}
                  outerRadius={50}
                  startAngle={180}
                  endAngle={-180}
                  paddingAngle={0}
                  dataKey="value"
                >
                  <Cell fill={strokeColor} />
                  <Cell fill="rgba(0,0,0,0.05)" />
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className={`text-3xl font-black ${colorClass}`}>{Math.round(healthScore)}%</span>
              <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Salud</span>
            </div>
          </div>
          <Badge variant={badgeVariant} className="font-semibold uppercase px-3 py-1 text-[10px]">
            {healthStatus}
          </Badge>
        </div>

        {/* CENTRO: NARRATIVA DINÁMICA */}
        <div className="flex-1 space-y-6">
          <div>
            <h3 className="text-xl font-bold flex items-center gap-2">
              <LayoutDashboard className="w-5 h-5 text-primary" />
              Análisis de Calidad y Salud
            </h3>
            <p className="text-muted-foreground leading-relaxed mt-2 text-sm">
              Tu dataset tiene <span className="text-foreground font-semibold font-mono">{dataset_overview.row_count.toLocaleString()} registros</span> con 
              <span className="text-foreground font-semibold font-mono"> {dataset_overview.column_count} variables</span> analizadas.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Bullet Nulos */}
            <div className="flex gap-3 items-start p-3 rounded-lg bg-muted/30 border border-transparent hover:border-primary/10 transition-all">
              {dataset_overview.total_nulls === 0 ? (
                <div className="p-1.5 bg-green-50 dark:bg-green-950/30 rounded-full"><CheckCircle2 className="w-4 h-4 text-green-600" /></div>
              ) : (
                <div className="p-1.5 bg-yellow-50 dark:bg-yellow-950/30 rounded-full"><AlertCircle className="w-4 h-4 text-yellow-600" /></div>
              )}
              <div>
                <p className="text-sm font-bold">
                  {dataset_overview.total_nulls === 0 ? "Sin datos faltantes ✅" : `${dataset_overview.total_nulls.toLocaleString()} datos faltantes`}
                </p>
                <p className="text-[11px] text-muted-foreground leading-tight mt-1">
                  {dataset_overview.total_nulls === 0 
                    ? "Cada campo tiene información completa para procesar." 
                    : `${dataset_overview.total_null_percent.toFixed(1)}% de los datos están vacíos. Podría afectar algunos análisis.`}
                </p>
              </div>
            </div>

            {/* Bullet Duplicados */}
            <div className="flex gap-3 items-start p-3 rounded-lg bg-muted/30 border border-transparent hover:border-primary/10 transition-all">
              {dataset_overview.duplicate_rows === 0 ? (
                <div className="p-1.5 bg-green-50 dark:bg-green-950/30 rounded-full"><CheckCircle2 className="w-4 h-4 text-green-600" /></div>
              ) : (
                <div className="p-1.5 bg-red-50 dark:bg-red-950/30 rounded-full"><AlertCircle className="w-4 h-4 text-red-600" /></div>
              )}
              <div>
                <p className="text-sm font-bold">
                  {dataset_overview.duplicate_rows === 0 ? "Cada registro es único ✅" : `${dataset_overview.duplicate_rows.toLocaleString()} filas duplicadas`}
                </p>
                <p className="text-[11px] text-muted-foreground leading-tight mt-1">
                  {dataset_overview.duplicate_rows === 0 
                    ? "No hay redundancia detectada en la información." 
                    : "Esto puede inflar artificialmente algunas métricas."}
                </p>
              </div>
            </div>

            {/* Bullet Tipos / Capacidad */}
            <div className="flex gap-3 items-start p-3 rounded-lg bg-muted/30 border border-transparent hover:border-primary/10 transition-all">
              <div className="p-1.5 bg-blue-50 dark:bg-blue-950/30 rounded-full"><Lightbulb className="w-4 h-4 text-blue-600" /></div>
              <div>
                <p className="text-sm font-bold">Capacidad de Análisis</p>
                <p className="text-[11px] text-muted-foreground leading-tight mt-1">
                  Tenés {dataset_overview.numeric_columns} métricas para medir y {dataset_overview.categorical_columns} categorías para segmentar resultados.
                </p>
              </div>
            </div>

            {/* Bullet Hallazgos */}
            <div className="flex gap-3 items-start p-3 rounded-lg bg-muted/30 border border-transparent hover:border-primary/10 transition-all">
              <div className="p-1.5 bg-primary/5 rounded-full"><ShieldAlert className="w-4 h-4 text-primary" /></div>
              <div>
                <p className="text-sm font-bold">{findings.length} Hallazgos detectados</p>
                <p className="text-[11px] text-muted-foreground leading-tight mt-1">
                  {criticalCount > 0 
                    ? `Contiene ${criticalCount} problemas críticos. Revisar antes de avanzar.` 
                    : findings.length > 0 ? "Ninguno es crítico — podés avanzar con confianza." : "Excelente salud de datos."}
                </p>
              </div>
            </div>
          </div>

          {/* INTEGRACIÓN CON LLM: Executive Summary */}
          <div className="bg-muted/40 p-5 rounded-2xl border border-dashed border-muted-foreground/20 mt-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
               <Lightbulb className="w-12 h-12" />
            </div>
            <p className="text-sm italic leading-relaxed text-foreground/90 relative z-10">
              <span className="font-bold not-italic block mb-1 text-primary">Resumen Inteligente del Dataset</span> 
              {executive_summary || "Resumen basado en análisis determinístico generado por el motor de Data-X."}
            </p>
          </div>
          
          <CostIndicator 
            costUsd={report.llm_cost_usd} 
            modelUsed={report.llm_model_used} 
            callsCount={report.llm_calls_count} 
          />
        </div>
      </div>

      {/* FOOTER: DETALLES TÉCNICOS COLAPSABLES */}
      <div className="mt-8 border-t pt-4">
        <button 
          onClick={() => setShowTechnical(!showTechnical)}
          className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground hover:text-primary transition-colors uppercase tracking-widest"
        >
          {showTechnical ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          {showTechnical ? "Ocultar detalles técnicos" : "Ver especificaciones técnicas para expertos"}
        </button>
        
        {showTechnical && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-6 animate-in slide-in-from-top-2 duration-300">
            <TechnicalItem label="Total Filas" value={dataset_overview.row_count.toLocaleString()} />
            <TechnicalItem label="Total Columnas" value={dataset_overview.column_count.toString()} />
            <TechnicalItem label="Var. Numéricas" value={dataset_overview.numeric_columns.toString()} />
            <TechnicalItem label="Var. Categorías" value={dataset_overview.categorical_columns.toString()} />
            <TechnicalItem label="Valores Nulos" value={`${dataset_overview.total_nulls} (${dataset_overview.total_null_percent.toFixed(2)}%)`} />
            <TechnicalItem label="Filas Duplicadas" value={`${dataset_overview.duplicate_rows} (${dataset_overview.duplicate_percent.toFixed(2)}%)`} />
            <TechnicalItem label="Hallazgos Totales" value={findings.length.toString()} />
            <TechnicalItem label="Score de Salud" value={`${healthScore.toFixed(1)}%`} />
          </div>
        )}
      </div>
    </Card>
  );
}

function TechnicalItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-tighter">{label}</p>
      <p className="text-sm font-mono font-medium">{value}</p>
    </div>
  );
}
