import { 
  SessionResponse, 
  AnalysisReport, 
  AnalyzeResponse, 
  ErrorResponse,
  SessionListItem,
  PaginatedSessions,
  UserCreate,
  UserLogin,
  TokenResponse,
  UserResponse
} from "@/types/contracts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

const TOKEN_KEY = 'datax_token';

function getAuthHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
      // Opcionalmente redirigir a login si estamos en el cliente
    }
  }

  if (!res.ok) {
    let error: ErrorResponse;
    try {
      error = await res.json();
    } catch {
      error = { 
        error_code: 'CONNECTION_ERROR', 
        message: 'Error de conexión con el servidor' 
      };
    }
    throw error;
  }
  return res.json();
}

export const api = {
  async register(data: UserCreate): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const result = await handleResponse<TokenResponse>(res);
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEY, result.access_token);
    }
    return result;
  },

  async login(data: UserLogin): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const result = await handleResponse<TokenResponse>(res);
    if (typeof window !== 'undefined') {
      localStorage.setItem(TOKEN_KEY, result.access_token);
    }
    return result;
  },

  async getMe(): Promise<UserResponse> {
    const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: { ...getAuthHeaders() },
    });
    return handleResponse<UserResponse>(res);
  },

  logout() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
    }
  },

  isAuthenticated(): boolean {
    if (typeof window === 'undefined') return false;
    return !!localStorage.getItem(TOKEN_KEY);
  },

  async health() {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    return res.json();
  },

  async createSession(file: File): Promise<SessionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/api/sessions`, {
      method: 'POST',
      headers: { ...getAuthHeaders() },
      body: formData,
    });
    return handleResponse<SessionResponse>(res);
  },

  async getSession(sessionId: string): Promise<SessionResponse> {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
      headers: { ...getAuthHeaders() },
    });
    return handleResponse<SessionResponse>(res);
  },

  async getReport(sessionId: string): Promise<AnalysisReport> {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/report`, {
      headers: { ...getAuthHeaders() },
    });
    return handleResponse<AnalysisReport>(res);
  },

  async analyze(sessionId: string, query: string): Promise<AnalyzeResponse> {
    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify({ session_id: sessionId, query }),
    });
    return handleResponse<AnalyzeResponse>(res);
  },

  async listSessions(limit: number = 20, offset: number = 0): Promise<PaginatedSessions> {
    const res = await fetch(`${API_BASE_URL}/api/sessions?limit=${limit}&offset=${offset}`, {
      headers: { ...getAuthHeaders() },
    });
    
    const data = await handleResponse<{items: SessionResponse[], total: number, limit: number, offset: number}>(res);
    
    return {
      items: data.items.map(s => ({
        session_id: s.session_id,
        status: s.status,
        filename: (s.source_metadata.filename as string) || 'Archivo desconocido',
        created_at: s.created_at,
        finding_count: s.finding_count || 0,
        quality_decision: s.quality_decision || 'unknown'
      })),
      total: data.total,
      limit: data.limit,
      offset: data.offset
    };
  },

  async getSuggestedQuestions(sessionId: string, maxQuestions: number = 8): Promise<{
    session_id: string;
    questions: Array<{
      text: string;
      category: string;
      priority: number;
      context: string;
    }>;
    total: number;
    context: {
      findings_count: number;
      chunks_count: number;
      tables_count: number;
    };
  }> {
    const res = await fetch(
      `${API_BASE_URL}/api/analyze/${sessionId}/suggested-questions?max_questions=${maxQuestions}`,
      {
        headers: { ...getAuthHeaders() },
      }
    );
    return handleResponse(res);
  },
};
