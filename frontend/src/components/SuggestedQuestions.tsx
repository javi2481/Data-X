"use client";

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Lightbulb, 
  MessageCircleQuestion,
  RefreshCw,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { api } from '@/lib/api';
import { cn } from '@/lib/utils';

interface SuggestedQuestion {
  text: string;
  category: string;
  priority: number;
  context: string;
}

interface SuggestedQuestionsProps {
  sessionId: string;
  onSelectQuestion: (question: string) => void;
  className?: string;
}

/**
 * SuggestedQuestions: Displays contextual questions based on document analysis.
 * Sprint 2: Shows questions generated from findings, chunks, and tables.
 */
export function SuggestedQuestions({ 
  sessionId, 
  onSelectQuestion,
  className 
}: SuggestedQuestionsProps) {
  const [questions, setQuestions] = useState<SuggestedQuestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);

  const fetchQuestions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getSuggestedQuestions(sessionId);
      setQuestions(response.questions || []);
    } catch (err) {
      setError('No se pudieron cargar las preguntas sugeridas');
      console.error('Error fetching suggested questions:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sessionId) {
      fetchQuestions();
    }
  }, [sessionId]);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'data_gap':
      case 'reliability_risk':
      case 'quality_issue':
        return '🔍';
      case 'pattern':
      case 'opportunity':
        return '📊';
      case 'document_overview':
      case 'sections':
        return '📄';
      case 'tables':
        return '📋';
      default:
        return '💡';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'data_gap':
      case 'reliability_risk':
        return 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/20 dark:text-red-400';
      case 'pattern':
      case 'opportunity':
        return 'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/20 dark:text-green-400';
      case 'document_overview':
      case 'sections':
        return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400';
      case 'tables':
        return 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/20 dark:text-purple-400';
      default:
        return 'bg-gray-50 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-400';
    }
  };

  if (error) {
    return null; // Silently fail - questions are optional
  }

  if (questions.length === 0 && !loading) {
    return null;
  }

  return (
    <Card className={cn("border-amber-200 bg-amber-50/30 dark:bg-amber-900/10", className)}>
      <CardHeader className="py-3 cursor-pointer" onClick={() => setCollapsed(!collapsed)}>
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm flex items-center gap-2 text-amber-800 dark:text-amber-300">
            <Lightbulb className="h-4 w-4" />
            Preguntas Sugeridas
            {questions.length > 0 && (
              <Badge variant="secondary" className="ml-1 text-[10px] bg-amber-100 dark:bg-amber-900/30">
                {questions.length}
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                fetchQuestions();
              }}
              disabled={loading}
              className="h-7 w-7 p-0"
            >
              <RefreshCw className={cn("h-3 w-3", loading && "animate-spin")} />
            </Button>
            <ChevronRight className={cn(
              "h-4 w-4 text-muted-foreground transition-transform",
              !collapsed && "rotate-90"
            )} />
          </div>
        </div>
      </CardHeader>
      
      {!collapsed && (
        <CardContent className="pt-0 pb-4">
          {loading ? (
            <div className="flex items-center justify-center py-4">
              <Sparkles className="h-5 w-5 animate-pulse text-amber-500" />
              <span className="ml-2 text-sm text-muted-foreground">Generando preguntas...</span>
            </div>
          ) : (
            <div className="space-y-2">
              {questions.map((q, index) => (
                <button
                  key={index}
                  onClick={() => onSelectQuestion(q.text)}
                  className={cn(
                    "w-full text-left p-3 rounded-lg border transition-all",
                    "hover:shadow-sm hover:border-amber-300 dark:hover:border-amber-700",
                    "group flex items-start gap-3",
                    getCategoryColor(q.category)
                  )}
                >
                  <span className="text-lg">{getCategoryIcon(q.category)}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium leading-tight group-hover:text-amber-900 dark:group-hover:text-amber-200">
                      {q.text}
                    </p>
                    <p className="text-[10px] text-muted-foreground mt-1 truncate">
                      {q.context}
                    </p>
                  </div>
                  <MessageCircleQuestion className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity text-amber-600" />
                </button>
              ))}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
