export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      tenants: {
        Row: {
          id: string
          name: string
          created_at: string
          updated_at: string
          settings: Json
        }
        Insert: {
          id?: string
          name: string
          created_at?: string
          updated_at?: string
          settings?: Json
        }
        Update: {
          id?: string
          name?: string
          created_at?: string
          updated_at?: string
          settings?: Json
        }
      }
      user_profiles: {
        Row: {
          id: string
          tenant_id: string
          full_name: string | null
          role: 'admin' | 'user' | 'viewer'
          is_active: boolean
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          tenant_id: string
          full_name?: string | null
          role?: 'admin' | 'user' | 'viewer'
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          tenant_id?: string
          full_name?: string | null
          role?: 'admin' | 'user' | 'viewer'
          is_active?: boolean
          created_at?: string
          updated_at?: string
        }
      }
      documents: {
        Row: {
          id: string
          tenant_id: string
          title: string
          source_url: string | null
          file_type: string | null
          file_size: number | null
          status: 'pending' | 'processing' | 'completed' | 'failed'
          metadata: Json
          uploaded_by: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          tenant_id: string
          title: string
          source_url?: string | null
          file_type?: string | null
          file_size?: number | null
          status?: 'pending' | 'processing' | 'completed' | 'failed'
          metadata?: Json
          uploaded_by?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          tenant_id?: string
          title?: string
          source_url?: string | null
          file_type?: string | null
          file_size?: number | null
          status?: 'pending' | 'processing' | 'completed' | 'failed'
          metadata?: Json
          uploaded_by?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      document_chunks: {
        Row: {
          id: string
          document_id: string
          tenant_id: string
          content: string
          embedding: number[] | null
          chunk_index: number
          metadata: Json
          created_at: string
        }
        Insert: {
          id?: string
          document_id: string
          tenant_id: string
          content: string
          embedding?: number[] | null
          chunk_index: number
          metadata?: Json
          created_at?: string
        }
        Update: {
          id?: string
          document_id?: string
          tenant_id?: string
          content?: string
          embedding?: number[] | null
          chunk_index?: number
          metadata?: Json
          created_at?: string
        }
      }
      chat_sessions: {
        Row: {
          id: string
          tenant_id: string
          user_id: string
          title: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          tenant_id: string
          user_id: string
          title?: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          tenant_id?: string
          user_id?: string
          title?: string
          created_at?: string
          updated_at?: string
        }
      }
      chat_messages: {
        Row: {
          id: string
          session_id: string
          tenant_id: string
          role: 'user' | 'assistant' | 'system'
          content: string
          metadata: Json
          created_at: string
        }
        Insert: {
          id?: string
          session_id: string
          tenant_id: string
          role: 'user' | 'assistant' | 'system'
          content: string
          metadata?: Json
          created_at?: string
        }
        Update: {
          id?: string
          session_id?: string
          tenant_id?: string
          role?: 'user' | 'assistant' | 'system'
          content?: string
          metadata?: Json
          created_at?: string
        }
      }
      data_sources: {
        Row: {
          id: string
          tenant_id: string
          name: string
          type: 's3' | 'sharepoint' | 'confluence' | 'google_drive' | 'database' | 'api'
          config: Json
          status: 'active' | 'inactive' | 'error'
          last_sync: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          tenant_id: string
          name: string
          type: 's3' | 'sharepoint' | 'confluence' | 'google_drive' | 'database' | 'api'
          config?: Json
          status?: 'active' | 'inactive' | 'error'
          last_sync?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          tenant_id?: string
          name?: string
          type?: 's3' | 'sharepoint' | 'confluence' | 'google_drive' | 'database' | 'api'
          config?: Json
          status?: 'active' | 'inactive' | 'error'
          last_sync?: string | null
          created_at?: string
          updated_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      [_ in never]: never
    }
    Enums: {
      [_ in never]: never
    }
  }
}
