"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { ColumnProfile } from "@/types/contracts";

interface DataPreviewTableProps {
  data: Record<string, string | number | boolean | null>[];
  columnProfiles?: ColumnProfile[];
}

export function DataPreviewTable({ data, columnProfiles }: DataPreviewTableProps) {
  if (data.length === 0) {
    return (
      <div className="p-8 text-center border rounded-lg bg-muted/20">
        <p className="text-muted-foreground italic">No hay previsualización de datos disponible.</p>
      </div>
    );
  }

  const headers = Object.keys(data[0]);

  const getColType = (colName: string) => {
    const profile = columnProfiles?.find(p => p.name === colName);
    return profile?.dtype || 'unknown';
  };

  const getTypeVariant = (type: string) => {
    if (type.includes('int') || type.includes('float')) return 'info';
    if (type.includes('date') || type.includes('time')) return 'success';
    if (type.includes('object') || type.includes('str')) return 'secondary';
    return 'outline';
  };

  return (
    <div className="space-y-2">
      <div className="rounded-md border overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              {headers.map((header) => (
                <TableHead key={header} className="whitespace-nowrap min-w-[120px]">
                  <div className="flex flex-col gap-1 py-1">
                    <span className="font-bold text-foreground">{header}</span>
                    <Badge variant={getTypeVariant(getColType(header))} className="w-fit text-[10px] px-1 py-0 h-4">
                      {getColType(header)}
                    </Badge>
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((row, i) => (
              <TableRow key={i}>
                {headers.map((header) => (
                  <TableCell key={`${i}-${header}`} className="text-sm truncate max-w-[200px]">
                    {row[header] === null ? (
                      <span className="text-muted-foreground italic text-xs">null</span>
                    ) : (
                      String(row[header])
                    )}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <p className="text-[10px] text-muted-foreground text-right italic px-1">
        Mostrando las primeras {data.length} filas del dataset.
      </p>
    </div>
  );
}
