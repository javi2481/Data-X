import React from 'react';
import { Badge } from "@/components/ui/badge";
import { LucideZap, LucideZapOff } from "lucide-react";

interface CostIndicatorProps {
  costUsd?: number;
  modelUsed?: string;
  callsCount?: number;
}

export function CostIndicator({ costUsd = 0, modelUsed = "", callsCount = 0 }: CostIndicatorProps) {
  const isDeterministic = costUsd === 0;

  if (isDeterministic) {
    return (
      <div className="flex items-center gap-2 text-[11px] text-muted-foreground mt-4 italic">
        <LucideZapOff size={12} className="opacity-60" />
        <span>Análisis determinístico (sin IA)</span>
      </div>
    );
  }

  const getStyles = (cost: number) => {
    if (cost < 0.01) {
      return "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-50 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-800/30";
    }
    if (cost <= 0.05) {
      return "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-50 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-800/30";
    }
    return "bg-red-50 text-red-700 border-red-200 hover:bg-red-50 dark:bg-red-950/20 dark:text-red-400 dark:border-red-800/30";
  };

  return (
    <div className="flex items-center gap-2 mt-4 animate-in fade-in slide-in-from-top-1 duration-300">
      <Badge variant="outline" className={`font-medium shadow-sm text-[11px] px-2 py-0.5 ${getStyles(costUsd)}`}>
        <LucideZap size={12} className="mr-1.5 fill-current" />
        IA: ${costUsd.toFixed(3)} ({modelUsed}, {callsCount} {callsCount === 1 ? 'llamada' : 'llamadas'})
      </Badge>
    </div>
  );
}
