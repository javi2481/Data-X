import React, { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { SessionListItem } from '@/types/contracts';
import { Card, CardContent } from '@/components/ui/card';
import { History, FileIcon, Calendar, ArrowRight, Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface SessionHistoryProps {
  onSelectSession: (sessionId: string) => void;
  currentSessionId?: string;
}

export const SessionHistory: React.FC<SessionHistoryProps> = ({ onSelectSession, currentSessionId }) => {
  const [sessions, setSessions] = useState<SessionListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.listSessions(10);
      setSessions(data);
    } catch (error) {
      console.error('Error loading sessions', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return new Intl.DateTimeFormat('es-AR', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date);
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (sessions.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-gray-500 mb-2">
        <History className="h-4 w-4" />
        <h3 className="text-sm font-medium uppercase tracking-wider">Historial Reciente</h3>
      </div>
      <div className="grid grid-cols-1 gap-2">
        {sessions.map((session) => (
          <button
            key={session.session_id}
            onClick={() => onSelectSession(session.session_id)}
            className={`text-left transition-all duration-200 group w-full ${
              currentSessionId === session.session_id 
                ? 'ring-2 ring-indigo-500 ring-offset-1 rounded-lg' 
                : ''
            }`}
          >
            <Card className={`hover:border-indigo-300 transition-colors ${
              currentSessionId === session.session_id ? 'bg-indigo-50/50 border-indigo-200' : ''
            }`}>
              <CardContent className="p-3">
                <div className="flex justify-between items-start mb-1">
                  <div className="flex items-center gap-2 overflow-hidden">
                    <FileIcon className="h-4 w-4 text-gray-400 shrink-0" />
                    <span className="text-sm font-semibold truncate text-gray-700 group-hover:text-indigo-600 transition-colors">
                      {session.filename}
                    </span>
                  </div>
                  <Badge variant={session.status === 'ready' ? 'default' : 'secondary'} className="text-[10px] px-1.5 py-0">
                    {session.status}
                  </Badge>
                </div>
                
                <div className="flex items-center justify-between text-[11px] text-gray-400">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(session.created_at)}
                  </div>
                  <div className="flex items-center gap-1 text-indigo-400 font-medium">
                    {session.finding_count} hallazgos
                    <ArrowRight className="h-3 w-3 opacity-0 group-hover:translate-x-1 group-hover:opacity-100 transition-all" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
};
