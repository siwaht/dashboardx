import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Send, Loader2 } from 'lucide-react';
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
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <div className="mb-6">
        <h1 className="text-3xl font-bold" data-testid="text-page-title">Chat</h1>
        <p className="text-gray-400 mt-1">Ask questions about your documents using RAG</p>
      </div>

      {/* Messages */}
      <div className="flex-1 bg-[#161b22] border border-[#30363d] rounded-lg overflow-y-auto p-4 space-y-4 mb-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500" data-testid="text-empty-state">
            <div className="text-center">
              <p className="text-lg font-medium">No messages yet</p>
              <p className="text-sm mt-1">Start a conversation by typing below</p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              data-testid={`message-${message.id}`}
            >
              <div
                className={`max-w-[70%] rounded-lg px-4 py-2 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-[#21262d] text-white'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs mt-1 opacity-70">
                  {new Date(message.createdAt).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your documents..."
          className="flex-1 px-4 py-3 bg-[#161b22] border border-[#30363d] rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={sendMessage.isPending}
          data-testid="input-message"
        />
        <button
          type="submit"
          disabled={!input.trim() || sendMessage.isPending}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          data-testid="button-send"
        >
          {sendMessage.isPending ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </form>
    </div>
  );
}
