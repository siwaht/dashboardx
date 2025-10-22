import React, { useEffect, useState } from 'react';
import { MessageSquare, Plus, Settings, LogOut, FileText, Database, Sparkles, Plug, Users, Shield } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { usePermissions } from '../../hooks/usePermissions';
import { supabase } from '../../lib/supabase';
import type { Database as DB } from '../../lib/database.types';

type ChatSession = DB['public']['Tables']['chat_sessions']['Row'];

interface SidebarProps {
  currentSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
  onNavigate: (view: 'chat' | 'documents' | 'sources' | 'settings' | 'mcp' | 'users') => void;
  currentView: string;
}

export function Sidebar({
  currentSessionId,
  onSessionSelect,
  onNewChat,
  onNavigate,
  currentView,
}: SidebarProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const { signOut, profile } = useAuth();
  const { canManageUsers } = usePermissions();

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    const { data, error } = await supabase
      .from('chat_sessions')
      .select('*')
      .order('updated_at', { ascending: false })
      .limit(20);

    if (error) {
      console.error('Error loading sessions:', error);
      return;
    }

    setSessions(data || []);
  };

  const handleNewChat = () => {
    onNewChat();
    loadSessions();
  };

  return (
    <div className="w-64 bg-gradient-to-b from-gray-900 via-gray-900 to-gray-950 text-white flex flex-col h-screen shadow-2xl border-r border-gray-800/50 relative overflow-hidden">
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-600/5 via-purple-600/5 to-indigo-600/5 opacity-50"></div>
      
      <div className="relative z-10 p-4 border-b border-gray-800/50 backdrop-blur-sm">
        <div className="flex items-center gap-3 mb-4 animate-fade-in">
          <div className="relative w-10 h-10 bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30 animate-float group">
            <MessageSquare size={20} className="text-white transition-transform group-hover:scale-110" />
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-blue-400 via-purple-400 to-indigo-500 opacity-0 group-hover:opacity-100 blur-md transition-opacity duration-300"></div>
          </div>
          <div>
            <h1 className="font-bold text-lg bg-gradient-to-r from-blue-400 via-purple-400 to-indigo-400 bg-clip-text text-transparent">
              RAG Platform
            </h1>
            <div className="flex items-center gap-2">
              <p className="text-xs text-gray-400 font-medium truncate max-w-[100px]">{profile?.full_name}</p>
              {profile?.role === 'admin' && (
                <span className="flex items-center gap-1 px-1.5 py-0.5 bg-purple-500/20 text-purple-300 text-[10px] font-semibold rounded border border-purple-500/30">
                  <Shield size={10} />
                  ADMIN
                </span>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={handleNewChat}
          className="group w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 rounded-xl transition-all duration-300 font-medium shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 hover:shadow-xl hover:scale-[1.02] active:scale-95 relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
          <Plus size={18} className="relative z-10 transition-transform group-hover:rotate-90 duration-300" />
          <span className="relative z-10">New Chat</span>
        </button>
      </div>

      <div className="relative z-10 flex-1 overflow-y-auto p-3 custom-scrollbar-dark">
        <div className="mb-4">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 py-2 flex items-center gap-2">
            <Sparkles size={12} className="text-blue-400" />
            Navigation
          </h3>
          <nav className="space-y-1">
            <button
              onClick={() => onNavigate('chat')}
              className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 ${
                currentView === 'chat'
                  ? 'bg-gradient-to-r from-blue-600/20 to-indigo-600/20 text-white shadow-lg shadow-blue-500/10 border border-blue-500/20'
                  : 'text-gray-300 hover:bg-gray-800/50 hover:text-white hover:translate-x-1'
              }`}
            >
              <MessageSquare size={18} className={`transition-transform duration-300 ${currentView === 'chat' ? 'text-blue-400' : 'group-hover:scale-110'}`} />
              <span className="font-medium">Chat</span>
              {currentView === 'chat' && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse"></div>
              )}
            </button>
            <button
              onClick={() => onNavigate('documents')}
              className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 ${
                currentView === 'documents'
                  ? 'bg-gradient-to-r from-purple-600/20 to-pink-600/20 text-white shadow-lg shadow-purple-500/10 border border-purple-500/20'
                  : 'text-gray-300 hover:bg-gray-800/50 hover:text-white hover:translate-x-1'
              }`}
            >
              <FileText size={18} className={`transition-transform duration-300 ${currentView === 'documents' ? 'text-purple-400' : 'group-hover:scale-110'}`} />
              <span className="font-medium">Documents</span>
              {currentView === 'documents' && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-purple-400 animate-pulse"></div>
              )}
            </button>
            <button
              onClick={() => onNavigate('sources')}
              className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 ${
                currentView === 'sources'
                  ? 'bg-gradient-to-r from-indigo-600/20 to-cyan-600/20 text-white shadow-lg shadow-indigo-500/10 border border-indigo-500/20'
                  : 'text-gray-300 hover:bg-gray-800/50 hover:text-white hover:translate-x-1'
              }`}
            >
              <Database size={18} className={`transition-transform duration-300 ${currentView === 'sources' ? 'text-indigo-400' : 'group-hover:scale-110'}`} />
              <span className="font-medium">Data Sources</span>
              {currentView === 'sources' && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-indigo-400 animate-pulse"></div>
              )}
            </button>
            <button
              onClick={() => onNavigate('mcp')}
              className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 ${
                currentView === 'mcp'
                  ? 'bg-gradient-to-r from-violet-600/20 to-purple-600/20 text-white shadow-lg shadow-violet-500/10 border border-violet-500/20'
                  : 'text-gray-300 hover:bg-gray-800/50 hover:text-white hover:translate-x-1'
              }`}
            >
              <Plug size={18} className={`transition-transform duration-300 ${currentView === 'mcp' ? 'text-violet-400' : 'group-hover:scale-110'}`} />
              <span className="font-medium">MCP Servers</span>
              {currentView === 'mcp' && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse"></div>
              )}
            </button>
            {canManageUsers() && (
              <button
                onClick={() => onNavigate('users')}
                className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 ${
                  currentView === 'users'
                    ? 'bg-gradient-to-r from-amber-600/20 to-orange-600/20 text-white shadow-lg shadow-amber-500/10 border border-amber-500/20'
                    : 'text-gray-300 hover:bg-gray-800/50 hover:text-white hover:translate-x-1'
                }`}
              >
                <Users size={18} className={`transition-transform duration-300 ${currentView === 'users' ? 'text-amber-400' : 'group-hover:scale-110'}`} />
                <span className="font-medium">User Management</span>
                {currentView === 'users' && (
                  <div className="ml-auto w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></div>
                )}
              </button>
            )}
          </nav>
        </div>

        {sessions.length > 0 && (
          <div className="animate-fade-in">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 py-2 flex items-center gap-2">
              <MessageSquare size={12} className="text-purple-400" />
              Recent Chats
            </h3>
            <div className="space-y-1">
              {sessions.map((session, index) => (
                <button
                  key={session.id}
                  onClick={() => onSessionSelect(session.id)}
                  style={{ animationDelay: `${index * 50}ms` }}
                  className={`group w-full text-left px-3 py-2.5 rounded-xl transition-all duration-300 truncate animate-slide-in-left ${
                    currentSessionId === session.id
                      ? 'bg-gray-800/80 text-white shadow-md border border-gray-700/50'
                      : 'text-gray-400 hover:bg-gray-800/50 hover:text-white hover:translate-x-1'
                  }`}
                >
                  <span className="text-sm font-medium">{session.title}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="relative z-10 p-3 border-t border-gray-800/50 backdrop-blur-sm space-y-1">
        <button
          onClick={() => onNavigate('settings')}
          className={`group w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-300 ${
            currentView === 'settings'
              ? 'bg-gradient-to-r from-gray-700/50 to-gray-800/50 text-white shadow-md border border-gray-600/30'
              : 'text-gray-300 hover:bg-gray-800/50 hover:text-white hover:translate-x-1'
          }`}
        >
          <Settings size={18} className={`transition-transform duration-300 ${currentView === 'settings' ? '' : 'group-hover:rotate-90'}`} />
          <span className="font-medium">Settings</span>
        </button>
        <button
          onClick={signOut}
          className="group w-full flex items-center gap-3 px-3 py-2.5 text-gray-400 hover:bg-red-500/10 hover:text-red-400 rounded-xl transition-all duration-300 hover:translate-x-1 border border-transparent hover:border-red-500/20"
        >
          <LogOut size={18} className="transition-transform group-hover:translate-x-1" />
          <span className="font-medium">Sign Out</span>
        </button>
      </div>
    </div>
  );
}
