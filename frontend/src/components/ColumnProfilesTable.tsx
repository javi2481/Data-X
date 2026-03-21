"use client";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ColumnProfile } from "@/types/contracts";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ColumnProfilesTableProps {
  profiles: ColumnProfile[];
}

export function ColumnProfilesTable({ profiles }: ColumnProfilesTableProps) {
  const getTypeVariant = (type: string) => {
    if (type.includes('int') || type.includes('float')) return 'info';
    if (type.includes('date') || type.includes('time')) return 'success';
    if (type.includes('object') || type.includes('str')) return 'secondary';
    return 'outline';
  };

  return (
    <div className="rounded-md border overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[150px]">Columna</TableHead>
            <TableHead>Tipo</TableHead>
            <TableHead className="text-right">Nulos</TableHead>
            <TableHead className="text-right">Únicos</TableHead>
            <TableHead className="text-right">Cardinalidad</TableHead>
            <TableHead className="text-right">Min</TableHead>
            <TableHead className="text-right">Max</TableHead>
            <TableHead className="text-right">Promedio</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {profiles.map((profile) => (
            <TableRow key={profile.name}>
              <TableCell className="font-medium">{profile.name}</TableCell>
              <TableCell>
                <Badge variant={getTypeVariant(profile.dtype)} className="text-[10px] px-1 h-4">
                  {profile.dtype}
                </Badge>
              </TableCell>
              <TableCell className={cn(
                "text-right",
                profile.null_percent > 30 ? "text-red-500 font-semibold" : ""
              )}>
                {profile.null_percent.toFixed(1)}%
              </TableCell>
              <TableCell className="text-right">{profile.unique_count.toLocaleString()}</TableCell>
              <TableCell className={cn(
                "text-right",
                profile.cardinality > 0.95 ? "text-yellow-600 font-semibold" : ""
              )}>
                {(profile.cardinality * 100).toFixed(1)}%
              </TableCell>
              <TableCell className="text-right text-muted-foreground text-xs">
                {profile.min !== undefined ? profile.min.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '-'}
              </TableCell>
              <TableCell className="text-right text-muted-foreground text-xs">
                {profile.max !== undefined ? profile.max.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '-'}
              </TableCell>
              <TableCell className="text-right text-muted-foreground text-xs">
                {profile.mean !== undefined ? profile.mean.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '-'}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
