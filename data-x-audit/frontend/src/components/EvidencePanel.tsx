"use client";

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  FileText, 
  Table2, 
  Hash, 
  Layers, 
  MapPin,
  ChevronRight,
  ExternalLink,
  BookOpen
} from 'lucide-react';
import { EvidenceSource, SourceLocation, DocumentChunk } from '@/types/contracts';
import { cn } from '@/lib/utils';

interface EvidencePanelProps {
  sources: Array<string | EvidenceSource>;
  chunks?: DocumentChunk[];
  onSourceClick?: (sourceId: string) => void;
  className?: string;
}

/**
 * EvidencePanel: Displays detailed provenance information for query sources.
 * Sprint 1: Shows page numbers, bounding boxes, section paths, and table references.
 */
export function EvidencePanel({ 
  sources, 
  chunks = [],
  onSourceClick,
  className 
}: EvidencePanelProps) {
  if (!sources || sources.length === 0) {
    return null;
  }

  const resolveSource = (source: string | EvidenceSource): EvidenceSource => {
    if (typeof source === 'string') {
      return { 
        source_type: 'finding', 
        source_id: source 
      };
    }
    return source;
  };

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'table':
        return <Table2 className="w-4 h-4" />;
      case 'heading':
        return <Hash className="w-4 h-4" />;
      case 'section':
        return <Layers className="w-4 h-4" />;
      case 'page_reference':
        return <BookOpen className="w-4 h-4" />;
      case 'chunk':
        return <FileText className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getSourceTypeLabel = (sourceType: string) => {
    switch (sourceType) {
      case 'table': return 'Tabla';
      case 'heading': return 'Encabezado';
      case 'section': return 'Sección';
      case 'page_reference': return 'Página';
      case 'chunk': return 'Fragmento';
      case 'finding': return 'Hallazgo';
      default: return sourceType;
    }
  };

  const formatLocation = (location?: SourceLocation) => {
    if (!location) return null;
    
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
    
    return parts.length > 0 ? parts : null;
  };

  const findChunkForSource = (sourceId: string): DocumentChunk | undefined => {
    return chunks.find(c => c.chunk_id === sourceId || c.source_id === sourceId);
  };

  return (
    <Card className={cn("border-l-4 border-l-indigo-400", className)}>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm flex items-center gap-2 text-indigo-900 dark:text-indigo-300">
          <MapPin className="h-4 w-4" />
          Fuentes con Provenance (Docling)
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {sources.map((source, index) => {
          const resolved = resolveSource(source);
          const locationParts = formatLocation(resolved.location);
          const chunk = findChunkForSource(resolved.source_id);
          
          return (
            <div 
              key={`${resolved.source_type}-${resolved.source_id}-${index}`}
              className={cn(
                "group p-3 rounded-lg border bg-muted/30 hover:bg-muted/50 transition-colors",
                onSourceClick && "cursor-pointer"
              )}
              onClick={() => onSourceClick?.(resolved.source_id)}
            >
              {/* Header Row */}
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400">
                    {getSourceIcon(resolved.source_type)}
                  </div>
                  <div>
                    <Badge variant="outline" className="text-[10px] font-medium">
                      {getSourceTypeLabel(resolved.source_type)}
                    </Badge>
                    {resolved.score && (
                      <Badge 
                        variant="secondary" 
                        className="ml-1 text-[10px] bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                      >
                        {Math.round(resolved.score * 100)}% match
                      </Badge>
                    )}
                  </div>
                </div>
                {onSourceClick && (
                  <ExternalLink className="w-4 h-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                )}
              </div>

              {/* Location Info */}
              {locationParts && (
                <div className="mt-2 flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
                  <MapPin className="w-3 h-3" />
                  {locationParts.map((part, i) => (
                    <React.Fragment key={i}>
                      {i > 0 && <ChevronRight className="w-3 h-3" />}
                      <span className="font-medium">{part}</span>
                    </React.Fragment>
                  ))}
                </div>
              )}

              {/* Section Path (if different from heading) */}
              {resolved.location?.section_path && resolved.location.section_path.length > 1 && (
                <div className="mt-1 flex items-center gap-1 text-[10px] text-muted-foreground/70">
                  <Layers className="w-3 h-3" />
                  <span className="truncate">
                    {resolved.location.section_path.join(' → ')}
                  </span>
                </div>
              )}

              {/* Snippet */}
              {resolved.snippet && (
                <div className="mt-2 p-2 rounded bg-background/50 border border-dashed">
                  <p className="text-xs text-muted-foreground line-clamp-2 italic">
                    &quot;{resolved.snippet}&quot;
                  </p>
                </div>
              )}

              {/* Chunk Snippet (if available) */}
              {!resolved.snippet && chunk?.snippet && (
                <div className="mt-2 p-2 rounded bg-background/50 border border-dashed">
                  <p className="text-xs text-muted-foreground line-clamp-2 italic">
                    &quot;{chunk.snippet}&quot;
                  </p>
                </div>
              )}

              {/* Bounding Box Info (for advanced users) */}
              {resolved.location?.bbox && (
                <div className="mt-2 text-[10px] text-muted-foreground/60 font-mono">
                  bbox: [{resolved.location.bbox.l.toFixed(0)}, {resolved.location.bbox.t.toFixed(0)}, {resolved.location.bbox.r.toFixed(0)}, {resolved.location.bbox.b.toFixed(0)}]
                </div>
              )}
            </div>
          );
        })}

        {/* Summary */}
        <div className="pt-2 border-t flex items-center justify-between text-xs text-muted-foreground">
          <span>{sources.length} fuente{sources.length !== 1 ? 's' : ''} vinculada{sources.length !== 1 ? 's' : ''}</span>
          {chunks.length > 0 && (
            <span className="text-indigo-600 dark:text-indigo-400">
              {chunks.length} fragmentos indexados
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
