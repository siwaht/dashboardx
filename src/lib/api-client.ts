/**
 * API Client for Backend Communication
 * 
 * Handles all HTTP requests to the FastAPI backend with automatic
 * JWT token management and error handling.
 */

import { supabase } from './supabase';
import type { ChatRequest, ChatResponse } from '../types/agent.types';

class APIClient {
  private baseURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
  }

  /**
   * Get authentication headers with JWT token
   */
  private async getAuthHeaders(): Promise<HeadersInit> {
    const { data: { session } } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error('No active session. Please log in.');
    }

    return {
      'Authorization': `Bearer ${session.access_token}`,
      'Content-Type': 'application/json',
    };
  }

  /**
   * Handle API errors
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.detail || errorData.message || response.statusText;
      
      if (response.status === 401) {
        throw new Error('Authentication failed. Please log in again.');
      } else if (response.status === 403) {
        throw new Error('Access denied. You do not have permission to access this resource.');
      } else if (response.status === 404) {
        throw new Error('Resource not found.');
      } else if (response.status >= 500) {
        throw new Error('Server error. Please try again later.');
      }
      
      throw new Error(errorMessage);
    }

    return response.json();
  }

  /**
   * POST request
   */
  async post<T>(endpoint: string, body: any): Promise<T> {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    return this.handleResponse<T>(response);
  }

  /**
   * GET request
   */
  async get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
    const headers = await this.getAuthHeaders();
    
    let url = `${this.baseURL}${endpoint}`;
    if (params) {
      const searchParams = new URLSearchParams(params);
      url += `?${searchParams.toString()}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * PUT request
   */
  async put<T>(endpoint: string, body: any): Promise<T> {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(body),
    });

    return this.handleResponse<T>(response);
  }

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string): Promise<T> {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'DELETE',
      headers,
    });

    return this.handleResponse<T>(response);
  }

  /**
   * Upload file
   */
  async uploadFile(endpoint: string, file: File, additionalData?: Record<string, any>): Promise<any> {
    const { data: { session } } = await supabase.auth.getSession();

    if (!session?.access_token) {
      throw new Error('No active session. Please log in.');
    }

    const formData = new FormData();
    formData.append('file', file);

    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, typeof value === 'string' ? value : JSON.stringify(value));
      });
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session.access_token}`,
      },
      body: formData,
    });

    return this.handleResponse(response);
  }

  // ==================== Chat Endpoints ====================

  /**
   * Send a chat message (non-streaming)
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.post<ChatResponse>('/chat', request);
  }

  /**
   * Get chat history for a session
   */
  async getChatHistory(sessionId: string): Promise<any> {
    return this.get(`/chat/history/${sessionId}`);
  }

  /**
   * Create a new chat session
   */
  async createChatSession(title?: string): Promise<any> {
    return this.post('/chat/sessions', { title: title || 'New Chat' });
  }

  /**
   * Get all chat sessions for the user
   */
  async getChatSessions(): Promise<any> {
    return this.get('/chat/sessions');
  }

  /**
   * Delete a chat session
   */
  async deleteChatSession(sessionId: string): Promise<any> {
    return this.delete(`/chat/sessions/${sessionId}`);
  }

  // ==================== Document Endpoints ====================

  /**
   * Upload a document
   */
  async uploadDocument(file: File, metadata?: Record<string, any>): Promise<any> {
    return this.uploadFile('/documents/upload', file, metadata);
  }

  /**
   * Get document status
   */
  async getDocumentStatus(documentId: string): Promise<any> {
    return this.get(`/documents/${documentId}/status`);
  }

  /**
   * Get all documents
   */
  async getDocuments(): Promise<any> {
    return this.get('/documents');
  }

  /**
   * Delete a document
   */
  async deleteDocument(documentId: string): Promise<any> {
    return this.delete(`/documents/${documentId}`);
  }

  /**
   * Reprocess a document
   */
  async reprocessDocument(documentId: string): Promise<any> {
    return this.post(`/documents/${documentId}/reprocess`, {});
  }

  // ==================== Data Source Endpoints ====================

  /**
   * Create a data source connector
   */
  async createDataSource(config: any): Promise<any> {
    return this.post('/data-sources', config);
  }

  /**
   * Get all data sources
   */
  async getDataSources(): Promise<any> {
    return this.get('/data-sources');
  }

  /**
   * Update data source configuration
   */
  async updateDataSource(sourceId: string, config: any): Promise<any> {
    return this.put(`/data-sources/${sourceId}`, config);
  }

  /**
   * Delete a data source
   */
  async deleteDataSource(sourceId: string): Promise<any> {
    return this.delete(`/data-sources/${sourceId}`);
  }

  /**
   * Trigger data source sync
   */
  async syncDataSource(sourceId: string): Promise<any> {
    return this.post(`/data-sources/${sourceId}/sync`, {});
  }

  /**
   * Get sync status
   */
  async getSyncStatus(sourceId: string): Promise<any> {
    return this.get(`/data-sources/${sourceId}/sync-status`);
  }

  // ==================== Search Endpoints ====================

  /**
   * Search documents
   */
  async searchDocuments(query: string, options?: {
    top_k?: number;
    similarity_threshold?: number;
  }): Promise<any> {
    return this.post('/search', {
      query,
      ...options,
    });
  }

  // ==================== User Management Endpoints ====================

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<any> {
    return this.get('/api/users/me');
  }

  /**
   * List all users in the tenant
   */
  async listUsers(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    role?: string;
    is_active?: boolean;
  }): Promise<any[]> {
    const queryParams: Record<string, string> = {};
    if (params?.skip !== undefined) queryParams.skip = params.skip.toString();
    if (params?.limit !== undefined) queryParams.limit = params.limit.toString();
    if (params?.search) queryParams.search = params.search;
    if (params?.role) queryParams.role = params.role;
    if (params?.is_active !== undefined) queryParams.is_active = params.is_active.toString();

    return this.get('/api/users', queryParams);
  }

  /**
   * Get a specific user by ID
   */
  async getUser(userId: string): Promise<any> {
    return this.get(`/api/users/${userId}`);
  }

  /**
   * Create a new user
   */
  async createUser(userData: {
    email: string;
    password: string;
    full_name?: string;
    role?: 'admin' | 'user' | 'viewer';
  }): Promise<any> {
    return this.post('/api/users', userData);
  }

  /**
   * Update a user
   */
  async updateUser(userId: string, userData: {
    full_name?: string;
    role?: 'admin' | 'user' | 'viewer';
    is_active?: boolean;
  }): Promise<any> {
    return this.put(`/api/users/${userId}`, userData);
  }

  /**
   * Update user status (enable/disable)
   */
  async updateUserStatus(userId: string, isActive: boolean): Promise<any> {
    const headers = await this.getAuthHeaders();

    const response = await fetch(`${this.baseURL}/api/users/${userId}/status`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify({ is_active: isActive }),
    });

    return this.handleResponse(response);
  }

  /**
   * Delete a user
   */
  async deleteUser(userId: string): Promise<void> {
    return this.delete(`/api/users/${userId}`);
  }

  // ==================== Health Check ====================

  /**
   * Check backend health
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      return response.json();
    } catch (error) {
      throw new Error('Backend is not reachable');
    }
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Export class for testing
export { APIClient };
