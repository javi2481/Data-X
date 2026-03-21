import { Card, CardContent } from '@/components/ui/card';
import { Loader2, AlertCircle, Inbox } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface StateFeedbackProps {
  type: 'loading' | 'error' | 'empty';
  title: string;
  description?: string;
  onRetry?: () => void;
}

export function StateFeedback({ type, title, description, onRetry }: StateFeedbackProps) {
  const icons = {
    loading: <Loader2 className="w-10 h-10 text-primary animate-spin" />,
    error: <AlertCircle className="w-10 h-10 text-destructive" />,
    empty: <Inbox className="w-10 h-10 text-muted-foreground" />,
  };

  return (
    <Card className="border-dashed py-12">
      <CardContent className="flex flex-col items-center text-center space-y-4">
        {icons[type]}
        <div className="space-y-1">
          <h3 className="font-semibold text-lg">{title}</h3>
          {description && (
            <p className="text-sm text-muted-foreground max-w-sm">
              {description}
            </p>
          )}
        </div>
        {onRetry && (
          <Button onClick={onRetry} variant="outline" size="sm">
            Reintentar
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

export function SkeletonLoader() {
  return (
    <div className="space-y-8 w-full animate-pulse">
      <div className="space-y-4">
        <div className="h-10 bg-muted rounded w-1/4" />
        <div className="h-4 bg-muted rounded w-2/3" />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="h-32 bg-muted rounded-xl" />
        <div className="h-32 bg-muted rounded-xl" />
        <div className="h-32 bg-muted rounded-xl" />
      </div>

      <div className="space-y-6">
        <div className="h-48 bg-muted rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-64 bg-muted rounded-xl" />
          <div className="h-64 bg-muted rounded-xl" />
        </div>
      </div>
    </div>
  );
}
