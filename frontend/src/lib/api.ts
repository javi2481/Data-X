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

// FE-001 Fix: No más localStorage para JWT (vulnerabilidad XSS)
// El token ahora se maneja via httpOnly cookies desde el backend

function getAuthHeaders(): Record<string, string> {
  // Las cookies httpOnly se envían automáticamente con credentials: 'include'
  return {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    // FE-001: Con httpOnly cookies, el backend maneja la expiración
    // Solo redirigimos al login si es necesario
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
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
      credentials: 'include', // FE-001: Incluir cookies en requests
      body: JSON.stringify(data),
    });
    const result = await handleResponse<TokenResponse>(res);
    // FE-001: El backend establece la cookie httpOnly automáticamente
    return result;
  },

  async login(data: UserLogin): Promise<TokenResponse> {
    const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // FE-001: Incluir cookies en requests
      body: JSON.stringify(data),
    });
    const result = await handleResponse<TokenResponse>(res);
    // FE-001: El backend establece la cookie httpOnly automáticamente
    return result;
  },

  async getMe(): Promise<UserResponse> {
    const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
      credentials: 'include', // FE-001: Cookies se envían automáticamente
    });
    return handleResponse<UserResponse>(res);
  },

  async logout() {
    // FE-001: Llamar endpoint del backend que borre la cookie
    const res = await fetch(`${API_BASE_URL}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    return handleResponse(res);
  },

  isAuthenticated(): boolean {
    // FE-001: Ya no podemos verificar desde el cliente con httpOnly cookies
    // Esto debe manejarse via llamada al backend o state management
    // Por ahora retornamos true (el backend validará)
    return true;
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
      credentials: 'include', // FE-001: Incluir cookies
      body: formData,
    });
    return handleResponse<SessionResponse>(res);
  },

  async getSession(sessionId: string): Promise<SessionResponse> {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}`, {
      credentials: 'include', // FE-001: Incluir cookies
    });
    return handleResponse<SessionResponse>(res);
  },

  async getReport(sessionId: string): Promise<AnalysisReport> {
    const res = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/report`, {
      credentials: 'include', // FE-001: Incluir cookies
    });
    return handleResponse<AnalysisReport>(res);
  },

  async analyze(sessionId: string, query: string): Promise<AnalyzeResponse> {
    const res = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // FE-001: Incluir cookies
      body: JSON.stringify({ session_id: sessionId, query }),
    });
    return handleResponse<AnalyzeResponse>(res);
  },

  async listSessions(limit: number = 20, offset: number = 0): Promise<PaginatedSessions> {
    const res = await fetch(`${API_BASE_URL}/api/sessions?limit=${limit}&offset=${offset}`, {
      credentials: 'include', // FE-001: Incluir cookies
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
        credentials: 'include', // FE-001: Incluir cookies
      }
    );
    return handleResponse(res);
  },
};
