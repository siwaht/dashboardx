import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Send, Loader2, Sparkles, Bot, User as UserIcon } from 'lucide-react';
import { queryClient, apiRequest } from '@/lib/queryClient';
import { getDemoConfig } from '@/lib/demoConfig';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
}

export function ChatPage() {
  const [input, setInput] = useState('');

  const { data: config } = useQuery({
    queryKey: ['/api/demo/config'],
    queryFn: getDemoConfig,
  });

  const { data: messages = [], isLoading } = useQuery<Message[]>({
    queryKey: ['/api/chat/sessions', config?.sessionId, 'messages'],
    queryFn: async () => {
      if (!config) return [];
      const res = await fetch(`/api/chat/sessions/${config.sessionId}/messages`);
      if (!res.ok) return [];
      return res.json();
    },
    enabled: !!config,
  });

  const sendMessage = useMutation({
    mutationFn: async (content: string) => {
      if (!config) throw new Error('Config not loaded');
      return apiRequest(`/api/chat/messages`, {
        method: 'POST',
        body: JSON.stringify({
          sessionId: config.sessionId,
          tenantId: config.tenantId,
          role: 'user',
          content,
          metadata: {},
        }),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/chat/sessions', config?.sessionId, 'messages'] });
      setInput('');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sendMessage.isPending) return;
    sendMessage.mutate(input);
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 shadow-sm">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent" data-testid="text-page-title">
                AI Assistant
              </h1>
              <p className="text-sm text-gray-600">Ask questions about your documents using RAG</p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="max-w-4xl mx-auto px-6 py-8">
        {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <Loader2 className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
                <p className="text-gray-600 font-medium">Loading conversation...</p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="flex items-center justify-center h-full" data-testid="text-empty-state">
              <div className="text-center max-w-md animate-fade-in-up">
                <div className="w-20 h-20 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-3xl mx-auto mb-6 flex items-center justify-center shadow-lg shadow-indigo-500/50">
                  <Sparkles className="w-10 h-10 text-white" />
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-3">Start a Conversation</h2>
                <p className="text-gray-600 mb-6">
                  Ask me anything about your documents and I'll help you find the answers using advanced AI.
                </p>
                <div className="grid gap-3">
                  <button
                    onClick={() => setInput("What documents do I have?")}
                    className="px-4 py-3 bg-white border-2 border-gray-200 rounded-xl hover:border-indigo-300 hover:bg-indigo-50 transition-all text-left text-sm text-gray-700 hover:text-indigo-700"
                  >
                    📚 What documents do I have?
                  </button>
                  <button
                    onClick={() => setInput("Summarize my latest document")}
                    className="px-4 py-3 bg-white border-2 border-gray-200 rounded-xl hover:border-indigo-300 hover:bg-indigo-50 transition-all text-left text-sm text-gray-700 hover:text-indigo-700"
                  >
                    ✨ Summarize my latest document
                  </button>
                  <button
                    onClick={() => setInput("Find information about...")}
                    className="px-4 py-3 bg-white border-2 border-gray-200 rounded-xl hover:border-indigo-300 hover:bg-indigo-50 transition-all text-left text-sm text-gray-700 hover:text-indigo-700"
                  >
                    🔍 Find information about...
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((message, index) => (
                <div
                  key={message.id}
                  className={`flex gap-4 animate-fade-in-up ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                  style={{ animationDelay: `${index * 0.05}s` }}
                  data-testid={`message-${message.id}`}
                >
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
                        <Bot className="w-5 h-5 text-white" />
                      </div>
                    </div>
                  )}

                  <div
                    className={`max-w-[70%] group ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/30'
                        : 'bg-white text-gray-900 shadow-md border border-gray-100'
                    } rounded-2xl px-5 py-3.5 transition-all hover:shadow-xl`}
                  >
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                    <div className={`flex items-center gap-2 mt-2 text-xs ${
                      message.role === 'user' ? 'text-white/70' : 'text-gray-500'
                    }`}>
                      <span>{new Date(message.createdAt).toLocaleTimeString()}</span>
                    </div>
                  </div>

                  {message.role === 'user' && (
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
                        <UserIcon className="w-5 h-5 text-white" />
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {sendMessage.isPending && (
                <div className="flex gap-4 justify-start animate-fade-in">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  </div>
                  <div className="bg-white border border-gray-100 rounded-2xl px-5 py-4 shadow-md">
                    <div className="flex items-center gap-3">
                      <div className="flex gap-1.5">
                        <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2 h-2 bg-indigo-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <span className="text-sm text-gray-600">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white/80 backdrop-blur-xl border-t border-gray-200/50 shadow-lg">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <div className="flex-1 relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything about your documents..."
                className="w-full px-5 py-4 pr-12 bg-white border-2 border-gray-200 rounded-2xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-100 transition-all outline-none text-gray-900 placeholder-gray-400"
                disabled={sendMessage.isPending}
                data-testid="input-message"
              />
              {input.trim() && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <div className="w-8 h-8 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={!input.trim() || sendMessage.isPending}
              className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-2xl shadow-lg shadow-indigo-500/50 hover:shadow-xl hover:shadow-indigo-500/60 transition-all duration-300 hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center gap-2 font-semibold"
              data-testid="button-send"
            >
              {sendMessage.isPending ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span className="hidden sm:inline">Sending</span>
                </>
              ) : (
                <>
                  <Send className="w-5 h-5" />
                  <span className="hidden sm:inline">Send</span>
                </>
              )}
            </button>
          </form>

          <p className="text-xs text-gray-500 text-center mt-3">
            Powered by Advanced RAG AI · Your data is secure and private
          </p>
        </div>
      </div>
    </div>
  );
}
