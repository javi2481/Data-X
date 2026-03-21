"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  FileText, 
  ZoomIn, 
  ZoomOut, 
  ChevronLeft, 
  ChevronRight,
  Maximize2,
  Minimize2,
  Eye,
  EyeOff,
  MapPin
} from 'lucide-react';
import { BoundingBox, SourceLocation } from '@/types/contracts';
import { cn } from '@/lib/utils';

interface PDFPageViewerProps {
  /** URL or base64 of the PDF page image */
  pageImageUrl?: string;
  /** Current page number (1-indexed) */
  currentPage: number;
  /** Total number of pages */
  totalPages: number;
  /** Bounding boxes to highlight */
  highlights?: Array<{
    bbox: BoundingBox;
    label?: string;
    color?: string;
    sourceId?: string;
  }>;
  /** Called when page changes */
  onPageChange?: (page: number) => void;
  /** Called when a highlight is clicked */
  onHighlightClick?: (sourceId: string) => void;
  /** Page dimensions (for bbox coordinate conversion) */
  pageDimensions?: { width: number; height: number };
  className?: string;
}

/**
 * PDFPageViewer: Displays PDF pages with bounding box overlays for provenance visualization.
 * Sprint 3: Supports zoom, pan, and highlight interactions.
 */
export function PDFPageViewer({
  pageImageUrl,
  currentPage,
  totalPages,
  highlights = [],
  onPageChange,
  onHighlightClick,
  pageDimensions = { width: 612, height: 792 }, // Default Letter size in points
  className
}: PDFPageViewerProps) {
  const [zoom, setZoom] = useState(1);
  const [showHighlights, setShowHighlights] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeHighlight, setActiveHighlight] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<HTMLDivElement>(null);

  // Handle zoom
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5));
  const handleResetZoom = () => setZoom(1);

  // Handle page navigation
  const goToPrevPage = () => {
    if (currentPage > 1 && onPageChange) {
      onPageChange(currentPage - 1);
    }
  };

  const goToNextPage = () => {
    if (currentPage < totalPages && onPageChange) {
      onPageChange(currentPage + 1);
    }
  };

  // Toggle fullscreen
  const toggleFullscreen = () => {
    if (!document.fullscreenElement && containerRef.current) {
      containerRef.current.requestFullscreen();
      setIsFullscreen(true);
    } else if (document.exitFullscreen) {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Convert bbox coordinates to percentage for overlay positioning
  const bboxToStyle = (bbox: BoundingBox): React.CSSProperties => {
    const { l, t, r, b, coord_origin } = bbox;
    
    // Handle different coordinate origins
    let top = t;
    let bottom = b;
    
    if (coord_origin === 'BOTTOMLEFT') {
      // Convert from bottom-left origin to top-left
      top = pageDimensions.height - b;
      bottom = pageDimensions.height - t;
    }
    
    return {
      left: `${(l / pageDimensions.width) * 100}%`,
      top: `${(top / pageDimensions.height) * 100}%`,
      width: `${((r - l) / pageDimensions.width) * 100}%`,
      height: `${((bottom - top) / pageDimensions.height) * 100}%`,
    };
  };

  const getHighlightColor = (color?: string, isActive?: boolean) => {
    if (isActive) return 'rgba(59, 130, 246, 0.4)'; // Blue when active
    if (color) return color;
    return 'rgba(251, 191, 36, 0.3)'; // Default amber
  };

  // Placeholder when no image
  if (!pageImageUrl) {
    return (
      <Card className={cn("", className)}>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Vista de Documento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center h-64 bg-muted/30 rounded-lg border-2 border-dashed">
            <FileText className="w-12 h-12 text-muted-foreground/50 mb-2" />
            <p className="text-sm text-muted-foreground">
              Vista previa no disponible
            </p>
            <p className="text-xs text-muted-foreground/70 mt-1">
              La visualización de páginas requiere procesamiento adicional
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      ref={containerRef}
      className={cn(
        "overflow-hidden",
        isFullscreen && "fixed inset-0 z-50 rounded-none",
        className
      )}
    >
      <CardHeader className="pb-2 border-b">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2">
            <FileText className="w-4 h-4" />
            Página {currentPage} de {totalPages}
            {highlights.length > 0 && (
              <Badge variant="secondary" className="ml-2 text-[10px]">
                <MapPin className="w-3 h-3 mr-1" />
                {highlights.length} ubicación{highlights.length !== 1 ? 'es' : ''}
              </Badge>
            )}
          </CardTitle>
          
          {/* Controls */}
          <div className="flex items-center gap-1">
            {/* Highlight toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowHighlights(!showHighlights)}
              className="h-8 w-8 p-0"
              title={showHighlights ? 'Ocultar marcas' : 'Mostrar marcas'}
            >
              {showHighlights ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
            </Button>

            {/* Zoom controls */}
            <div className="flex items-center border rounded-md">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleZoomOut}
                disabled={zoom <= 0.5}
                className="h-8 w-8 p-0 rounded-r-none"
              >
                <ZoomOut className="h-4 w-4" />
              </Button>
              <span 
                className="px-2 text-xs font-medium cursor-pointer hover:bg-muted"
                onClick={handleResetZoom}
                title="Resetear zoom"
              >
                {Math.round(zoom * 100)}%
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleZoomIn}
                disabled={zoom >= 3}
                className="h-8 w-8 p-0 rounded-l-none"
              >
                <ZoomIn className="h-4 w-4" />
              </Button>
            </div>

            {/* Fullscreen */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleFullscreen}
              className="h-8 w-8 p-0"
            >
              {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0 relative">
        {/* Page navigation */}
        {totalPages > 1 && (
          <>
            <Button
              variant="ghost"
              size="sm"
              onClick={goToPrevPage}
              disabled={currentPage <= 1}
              className="absolute left-2 top-1/2 -translate-y-1/2 z-10 h-10 w-10 p-0 bg-background/80 hover:bg-background shadow-md"
            >
              <ChevronLeft className="h-6 w-6" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={goToNextPage}
              disabled={currentPage >= totalPages}
              className="absolute right-2 top-1/2 -translate-y-1/2 z-10 h-10 w-10 p-0 bg-background/80 hover:bg-background shadow-md"
            >
              <ChevronRight className="h-6 w-6" />
            </Button>
          </>
        )}

        {/* Viewer container */}
        <div 
          ref={viewerRef}
          className="overflow-auto"
          style={{ maxHeight: isFullscreen ? 'calc(100vh - 60px)' : '600px' }}
        >
          <div 
            className="relative mx-auto transition-transform duration-200"
            style={{ 
              transform: `scale(${zoom})`,
              transformOrigin: 'top center',
              width: 'fit-content'
            }}
          >
            {/* Page image */}
            <img
              src={pageImageUrl}
              alt={`Página ${currentPage}`}
              className="max-w-full h-auto"
              draggable={false}
            />

            {/* Bounding box overlays */}
            {showHighlights && highlights.map((highlight, index) => (
              <div
                key={`highlight-${index}-${highlight.sourceId || ''}`}
                className={cn(
                  "absolute border-2 cursor-pointer transition-all duration-200",
                  activeHighlight === highlight.sourceId 
                    ? "border-blue-500 shadow-lg" 
                    : "border-amber-400 hover:border-amber-500"
                )}
                style={{
                  ...bboxToStyle(highlight.bbox),
                  backgroundColor: getHighlightColor(highlight.color, activeHighlight === highlight.sourceId),
                }}
                onClick={() => {
                  setActiveHighlight(highlight.sourceId || null);
                  if (highlight.sourceId && onHighlightClick) {
                    onHighlightClick(highlight.sourceId);
                  }
                }}
                onMouseEnter={() => setActiveHighlight(highlight.sourceId || null)}
                onMouseLeave={() => setActiveHighlight(null)}
                title={highlight.label || `Ubicación ${index + 1}`}
              >
                {/* Label badge */}
                {highlight.label && (
                  <div className="absolute -top-6 left-0 bg-amber-500 text-white text-[10px] px-1.5 py-0.5 rounded whitespace-nowrap">
                    {highlight.label}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Page indicator for mobile */}
        {totalPages > 1 && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-background/90 px-3 py-1 rounded-full shadow-md">
            <span className="text-sm font-medium">
              {currentPage} / {totalPages}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Helper to convert SourceLocation to highlight format
 */
export function sourceLocationToHighlight(
  location: SourceLocation,
  label?: string,
  sourceId?: string
): { bbox: BoundingBox; label?: string; sourceId?: string } | null {
  if (!location.bbox) return null;
  
  return {
    bbox: location.bbox,
    label: label || location.heading || `Pág. ${location.page}`,
    sourceId,
  };
}
