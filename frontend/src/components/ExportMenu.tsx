"use client";

import { useState } from 'react';
import { Download, FileJson, FileText, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AnalysisReport } from '@/types/contracts';
import { jsPDF } from 'jspdf';
import { cn } from '@/lib/utils';

interface ExportMenuProps {
  report: AnalysisReport;
  filename: string;
}

export function ExportMenu({ report, filename }: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false);

  const exportJson = () => {
    const dataStr = JSON.stringify(report, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `${filename.replace(/\.[^/.]+$/, "")}_report.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    setIsOpen(false);
  };

  const exportPdf = () => {
    const doc = new jsPDF();
    const cleanFilename = filename.replace(/\.[^/.]+$/, "");
    const date = new Date(report.generated_at).toLocaleString();

    // Configuración de fuentes y márgenes
    const margin = 20;
    let y = 20;
    const pageWidth = doc.internal.pageSize.getWidth();

    // Título
    doc.setFontSize(18);
    doc.setFont("helvetica", "bold");
    doc.text(`Reporte de Análisis — ${cleanFilename}`, margin, y);
    y += 10;

    // Fecha
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.text(`Fecha del análisis: ${date}`, margin, y);
    y += 15;

    // Dataset Overview
    doc.setFontSize(14);
    doc.setFont("helvetica", "bold");
    doc.text("Resumen del Dataset", margin, y);
    y += 8;
    
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    doc.text(`Filas: ${report.dataset_overview.row_count}`, margin, y);
    y += 5;
    doc.text(`Columnas: ${report.dataset_overview.column_count}`, margin, y);
    y += 5;
    doc.text(`Completitud: ${(100 - report.dataset_overview.total_null_percent).toFixed(2)}%`, margin, y);
    y += 15;

    // Executive Summary
    if (report.executive_summary) {
      doc.setFontSize(14);
      doc.setFont("helvetica", "bold");
      doc.text("Resumen Ejecutivo", margin, y);
      y += 8;
      
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      const splitSummary = doc.splitTextToSize(report.executive_summary, pageWidth - (margin * 2));
      doc.text(splitSummary, margin, y);
      y += (splitSummary.length * 5) + 10;
    }

    // Findings
    if (report.findings && report.findings.length > 0) {
      doc.setFontSize(14);
      doc.setFont("helvetica", "bold");
      doc.text("Hallazgos Principales", margin, y);
      y += 8;

      report.findings.forEach((finding, index) => {
        // Verificar si hay espacio en la página
        if (y > 250) {
          doc.addPage();
          y = 20;
        }

        doc.setFontSize(11);
        doc.setFont("helvetica", "bold");
        doc.text(`${index + 1}. ${finding.title}`, margin, y);
        y += 6;

        doc.setFontSize(10);
        doc.setFont("helvetica", "normal");
        
        // What
        doc.setFont("helvetica", "bold");
        doc.text("¿Qué encontramos?", margin, y);
        y += 5;
        doc.setFont("helvetica", "normal");
        const splitWhat = doc.splitTextToSize(finding.what, pageWidth - (margin * 2));
        doc.text(splitWhat, margin, y);
        y += (splitWhat.length * 5) + 3;

        // Now What
        doc.setFont("helvetica", "bold");
        doc.text("¿Qué hacer?", margin, y);
        y += 5;
        doc.setFont("helvetica", "normal");
        const splitNow = doc.splitTextToSize(finding.now_what, pageWidth - (margin * 2));
        doc.text(splitNow, margin, y);
        y += (splitNow.length * 5) + 8;
      });
    }

    doc.save(`${cleanFilename}_report.pdf`);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <Button 
        variant="outline" 
        size="sm" 
        className="flex items-center gap-2"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Download className="h-4 w-4" />
        <span>Exportar</span>
        <ChevronDown className={cn("h-4 w-4 transition-transform", isOpen && "rotate-180")} />
      </Button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)} 
          />
          <div className="absolute right-0 mt-2 w-48 rounded-md border bg-white shadow-lg z-20 overflow-hidden">
            <button
              className="flex w-full items-center gap-2 px-4 py-2 text-sm hover:bg-slate-100 transition-colors"
              onClick={exportPdf}
            >
              <FileText className="h-4 w-4 text-blue-600" />
              <span>Exportar como PDF</span>
            </button>
            <button
              className="flex w-full items-center gap-2 px-4 py-2 text-sm border-t hover:bg-slate-100 transition-colors"
              onClick={exportJson}
            >
              <FileJson className="h-4 w-4 text-orange-600" />
              <span>Exportar como JSON</span>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
