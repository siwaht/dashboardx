import { supabase } from './supabase';

class APIClient {
  private baseURL: string;

  constructor() {
    // Use relative path to leverage Vite proxy
    this.baseURL = '/api';
  }

  private async getHeaders(): Promise<HeadersInit> {
    const { data: { session } } = await supabase.auth.getSession();
    return {
      'Content-Type': 'application/json',
      'Authorization': session?.access_token ? `Bearer ${session.access_token}` : '',
    };
  }

  async post<T>(endpoint: string, body: any): Promise<T> {
    const res = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: await this.getHeaders(),
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async get<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${this.baseURL}${endpoint}`, {
      headers: await this.getHeaders(),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  // --- Agent Endpoints ---
  async agentChat(query: string, sessionId?: string) {
    return this.post('/agents/chat', { query, session_id: sessionId });
  }

  // --- Document Endpoints ---
  async uploadDocument(file: File) {
    const formData = new FormData();
    formData.append('file', file);

    const { data: { session } } = await supabase.auth.getSession();
    const res = await fetch(`${this.baseURL}/rag/ingest`, {
      method: 'POST',
      headers: {
        'Authorization': session?.access_token ? `Bearer ${session.access_token}` : '',
      },
      body: formData,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  }

  async listDocuments() {
    return this.get('/rag/documents');
  }

  // --- User Endpoints ---
  async getCurrentUser() {
    return this.get('/users/me');
  }
}

export const apiClient = new APIClient();
