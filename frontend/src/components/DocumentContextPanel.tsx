"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AnalysisReport, DocumentTableRef } from "@/types/contracts";
import { FileText, Table2, Check, RefreshCw, ChevronDown, ChevronUp, Info } from "lucide-react";
import { cn } from "@/lib/utils";

interface DocumentContextPanelProps {
  report: AnalysisReport;
  onTableSelect?: (tableIndex: number) => void;
}

/**
 * DocumentContextPanel: Shows detected tables and document context.
 * Sprint 2: Added functional table selector with re-analysis capability.
 */
export function DocumentContextPanel({ report, onTableSelect }: DocumentContextPanelProps) {
  const tables = report.document_tables ?? [];
  const selectedIndex = report.selected_table_index ?? 0;
  const context = report.document_context ?? "";
  const [expandedContext, setExpandedContext] = useState(false);
  const [selectingTable, setSelectingTable] = useState<number | null>(null);

  const handleTableSelect = async (tableIndex: number) => {
    if (tableIndex === selectedIndex) return;
    
    setSelectingTable(tableIndex);
    try {
      if (onTableSelect) {
        await onTableSelect(tableIndex);
      }
    } finally {
      setSelectingTable(null);
    }
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return "bg-gray-100 text-gray-600";
    if (confidence >= 0.9) return "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400";
    if (confidence >= 0.7) return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400";
    return "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400";
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <Table2 className="w-4 h-4 text-primary" />
              Tablas detectadas
              {tables.length > 1 && (
                <Badge variant="outline" className="ml-2 text-[10px]">
                  {tables.length} tablas
                </Badge>
              )}
            </CardTitle>
            {tables.length > 1 && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Info className="w-3 h-3" />
                <span>Hacé clic para cambiar de tabla</span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {tables.length === 0 ? (
            <p className="text-sm text-muted-foreground">No hay tablas detectadas para esta sesión.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {tables.map((table) => (
                <TableCard
                  key={table.table_id}
                  table={table}
                  isSelected={table.index === selectedIndex}
                  isLoading={selectingTable === table.index}
                  canSelect={tables.length > 1 && !!onTableSelect}
                  onSelect={() => handleTableSelect(table.index)}
                  confidenceColor={getConfidenceColor(table.confidence)}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3 cursor-pointer" onClick={() => setExpandedContext(!expandedContext)}>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base flex items-center gap-2">
              <FileText className="w-4 h-4 text-primary" />
              Contexto narrativo del documento
            </CardTitle>
            {context && (
              <Button variant="ghost" size="sm" className="h-6 px-2">
                {expandedContext ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {context ? (
            <pre className={cn(
              "whitespace-pre-wrap text-xs text-muted-foreground overflow-auto bg-muted/40 p-3 rounded-md transition-all",
              expandedContext ? "max-h-[600px]" : "max-h-[200px]"
            )}>
              {context}
            </pre>
          ) : (
            <p className="text-sm text-muted-foreground">
              No hay contexto narrativo disponible para esta sesión.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * TableCard: Individual table display with selection capability.
 */
interface TableCardProps {
  table: DocumentTableRef;
  isSelected: boolean;
  isLoading: boolean;
  canSelect: boolean;
  onSelect: () => void;
  confidenceColor: string;
}

function TableCard({ 
  table, 
  isSelected, 
  isLoading, 
  canSelect, 
  onSelect,
  confidenceColor 
}: TableCardProps) {
  return (
    <div
      onClick={canSelect && !isLoading ? onSelect : undefined}
      className={cn(
        "border rounded-md p-3 bg-background transition-all",
        isSelected && "ring-2 ring-primary/50 border-primary",
        canSelect && !isSelected && "cursor-pointer hover:border-primary/50 hover:shadow-sm",
        isLoading && "opacity-50"
      )}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold">Tabla {table.index + 1}</p>
          {isSelected && (
            <Badge variant="default" className="text-[10px] bg-primary">
              <Check className="w-3 h-3 mr-1" />
              Activa
            </Badge>
          )}
          {isLoading && (
            <RefreshCw className="w-4 h-4 animate-spin text-primary" />
          )}
        </div>
        {table.confidence !== undefined && (
          <Badge variant="outline" className={cn("text-[10px]", confidenceColor)}>
            {Math.round(table.confidence * 100)}% conf.
          </Badge>
        )}
      </div>
      <p className="text-xs text-muted-foreground mt-1">
        {table.row_count ?? 0} filas · {table.column_count ?? 0} columnas
      </p>
      {table.headers && table.headers.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-2">
          {table.headers.slice(0, 6).map((header) => (
            <span key={header} className="text-[10px] bg-muted px-1.5 py-0.5 rounded">
              {header}
            </span>
          ))}
          {table.headers.length > 6 && (
            <span className="text-[10px] text-muted-foreground">+{table.headers.length - 6} más</span>
          )}
        </div>
      )}
      {canSelect && !isSelected && (
        <p className="text-[10px] text-primary mt-2 opacity-0 group-hover:opacity-100">
          Clic para analizar esta tabla
        </p>
      )}
    </div>
  );
}
