import React, { useState, useEffect, useRef } from 'react';
import { Send, Loader2, Brain, Sparkles, Zap } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../lib/supabase';
import type { Database } from '../../lib/database.types';

type Message = Database['public']['Tables']['chat_messages']['Row'];

interface ChatInterfaceProps {
  sessionId: string | null;
  onNewSession: (sessionId: string) => void;
}

export function ChatInterface({ sessionId, onNewSession }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [agentState, setAgentState] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user, profile } = useAuth();

  useEffect(() => {
    if (sessionId) {
      loadMessages(sessionId);
    }
  }, [sessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadMessages = async (sid: string) => {
    const { data, error } = await supabase
      .from('chat_messages')
      .select('*')
      .eq('session_id', sid)
      .order('created_at', { ascending: true });

    if (error) {
      console.error('Error loading messages:', error);
      return;
    }

    setMessages(data || []);
  };

  const createSession = async () => {
    if (!user || !profile) return null;

    const { data, error } = await supabase
      .from('chat_sessions')
      .insert({
        tenant_id: profile.tenant_id,
        user_id: user.id,
        title: 'New Chat',
      })
      .select()
      .single();

    if (error) {
      console.error('Error creating session:', error);
      return null;
    }

    return (data as { id: string }).id;
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !profile) return;

    let currentSessionId = sessionId;
    if (!currentSessionId) {
      const newSessionId = await createSession();
      if (!newSessionId) return;
      currentSessionId = newSessionId;
      onNewSession(newSessionId);
    }

    const userMessage = input.trim();
    setInput('');
    setLoading(true);
    setAgentState('Processing your request...');

    try {
      const { data: userMessageData, error: userMsgError } = await supabase
        .from('chat_messages')
        .insert({
          session_id: currentSessionId,
          tenant_id: profile.tenant_id,
          role: 'user',
          content: userMessage,
        })
        .select();

      if (userMsgError) throw userMsgError;
      if (!userMessageData) throw new Error('No data returned from user message insert');

      setMessages((prev) => [...prev, ...userMessageData]);

      setAgentState('Thinking...');
      await new Promise((resolve) => setTimeout(resolve, 800));

      setAgentState('Searching knowledge base...');
      await new Promise((resolve) => setTimeout(resolve, 1200));

      const assistantResponse = `I've received your message: "${userMessage}". The RAG agent orchestration backend is being implemented next. This will include vector similarity search, LangGraph workflow execution, and streaming responses.`;

      const { data: assistantMessageData, error: assistantMsgError } = await supabase
        .from('chat_messages')
        .insert({
          session_id: currentSessionId,
          tenant_id: profile.tenant_id,
          role: 'assistant',
          content: assistantResponse,
          metadata: { agent_state: 'completed' },
        })
        .select();

      if (assistantMsgError) throw assistantMsgError;
      if (!assistantMessageData) throw new Error('No data returned from assistant message insert');

      setMessages((prev) => [...prev, ...assistantMessageData]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
      setAgentState('');
    }
  };

  return (
    <div className="flex flex-col h-full bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/30">
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center animate-fade-in">
            <div className="relative mb-6">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full blur-2xl opacity-20 animate-pulse-slow"></div>
              <div className="relative w-20 h-20 bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-2xl shadow-blue-500/30 animate-float">
                <Brain size={40} className="text-white" />
              </div>
            </div>
            <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-3">
              Start a conversation
            </h3>
            <p className="text-gray-600 max-w-md mb-6">
              Ask questions about your documents or data and get intelligent responses powered by AI
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-2xl">
              {[
                { icon: Sparkles, text: 'Analyze documents', color: 'from-blue-500 to-cyan-500' },
                { icon: Zap, text: 'Quick insights', color: 'from-purple-500 to-pink-500' },
                { icon: Brain, text: 'Smart answers', color: 'from-indigo-500 to-blue-500' },
              ].map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(item.text)}
                  className="group flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-xl hover:shadow-lg hover:scale-105 transition-all duration-300 hover:border-transparent"
                >
                  <div className={`p-1.5 bg-gradient-to-r ${item.color} rounded-lg`}>
                    <item.icon size={14} className="text-white" />
                  </div>
                  <span className="text-sm text-gray-700 group-hover:text-gray-900 font-medium">
                    {item.text}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={message.id}
            style={{ animationDelay: `${index * 100}ms` }}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}
          >
            <div
              className={`group max-w-[80%] rounded-2xl px-5 py-3 shadow-md transition-all duration-300 hover:shadow-xl ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white ml-12'
                  : 'bg-white text-gray-900 border border-gray-100 mr-12'
              }`}
            >
              <div className="flex items-start gap-3">
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30 group-hover:scale-110 transition-transform">
                    <Brain size={16} className="text-white" />
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
                  <div className="flex items-center gap-2 mt-2 text-xs opacity-60">
                    <span>{new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}

        {agentState && (
          <div className="flex items-start gap-3 animate-fade-in">
            <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30">
              <Loader2 size={16} className="text-white animate-spin" />
            </div>
            <div className="flex-1 bg-white rounded-2xl px-5 py-3 shadow-md border border-gray-100">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <span className="font-medium">{agentState}</span>
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-1.5 h-1.5 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-gray-200 bg-white/80 backdrop-blur-sm p-4 shadow-lg">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto">
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                placeholder="Ask me anything about your documents..."
                className="w-full px-5 py-3.5 pr-12 border-2 border-gray-200 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 bg-white shadow-sm hover:shadow-md focus:shadow-lg text-gray-900 placeholder-gray-400"
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
                <Sparkles size={18} />
              </div>
            </div>
            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="group relative px-6 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40 hover:scale-105 active:scale-95 disabled:hover:scale-100 overflow-hidden"
            >
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
              <Send size={20} className="relative z-10 transition-transform group-hover:translate-x-0.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
