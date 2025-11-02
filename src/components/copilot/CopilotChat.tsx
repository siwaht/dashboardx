/**
 * CopilotKit Chat Component
 * 
 * Interactive chat interface with real-time agent responses,
 * citations, and generative UI elements.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useCopilotAgent } from '../../hooks/useCopilotAgent';
import { AgentStateRenderer } from './AgentStateRenderer';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Array<{
    text: string;
    metadata: Record<string, any>;
  }>;
  timestamp: Date;
}

interface CopilotChatProps {
  className?: string;
  placeholder?: string;
  showAgentState?: boolean;
}

export function CopilotChat({ 
  className = '', 
  placeholder = 'Ask me anything...',
  showAgentState = true 
}: CopilotChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const { 
    isConnected, 
    isProcessing, 
    response, 
    agentState,
    error,
    sendQuery 
  } = useCopilotAgent();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  // Add assistant response when complete
  useEffect(() => {
    if (response && !isProcessing && agentState?.step === 'completed') {
      const assistantMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: response,
        citations: agentState.citations,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    }
  }, [response, isProcessing, agentState]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!input.trim() || !isConnected || isProcessing) {
      return;
    }

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    // Send to agent
    await sendQuery(input);
  };

  return (
    <div className={`copilot-chat ${className}`}>
      <div className="chat-container">
        {/* Messages Area */}
        <div className="messages-area">
          {messages.length === 0 && (
            <div className="empty-state">
              <svg className="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
              <h3>Start a conversation</h3>
              <p>Ask me anything about your documents or data</p>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id} className={`message ${message.role}`}>
              <div className="message-avatar">
                {message.role === 'user' ? (
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                  </svg>
                )}
              </div>
              
              <div className="message-content">
                <div className="message-text">{message.content}</div>
                
                {message.citations && message.citations.length > 0 && (
                  <div className="citations">
                    <h4>Sources:</h4>
                    {message.citations.map((citation, idx) => (
                      <div key={idx} className="citation-item">
                        <span className="citation-number">[{idx + 1}]</span>
                        <span className="citation-text">{citation.text}</span>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="message-timestamp">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="message assistant processing">
              <div className="message-avatar">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                </svg>
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <svg className="error-icon" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Agent State Sidebar */}
        {showAgentState && isProcessing && (
          <div className="agent-state-sidebar">
            <AgentStateRenderer />
          </div>
        )}
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="input-area">
        <div className="input-wrapper">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={placeholder}
            disabled={!isConnected || isProcessing}
            className="chat-input"
          />
          <button
            type="submit"
            disabled={!isConnected || isProcessing || !input.trim()}
            className="send-button"
          >
            {isProcessing ? (
              <svg className="spinner" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
              </svg>
            )}
          </button>
        </div>
        
        {!isConnected && (
          <div className="connection-warning">
            <svg className="warning-icon" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            <span>Connecting to agent service...</span>
          </div>
        )}
      </form>

      <style>{`
        .copilot-chat {
          display: flex;
          flex-direction: column;
          height: 100%;
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }

        .chat-container {
          display: flex;
          flex: 1;
          overflow: hidden;
        }

        .messages-area {
          flex: 1;
          overflow-y: auto;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #6b7280;
          text-align: center;
        }

        .empty-icon {
          width: 64px;
          height: 64px;
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .empty-state h3 {
          font-size: 20px;
          font-weight: 600;
          margin-bottom: 8px;
          color: #374151;
        }

        .empty-state p {
          font-size: 14px;
          margin: 0;
        }

        .message {
          display: flex;
          gap: 12px;
          animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .message.user {
          flex-direction: row-reverse;
        }

        .message-avatar {
          flex-shrink: 0;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
        }

        .message.user .message-avatar {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .message.assistant .message-avatar {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }

        .message-avatar svg {
          width: 20px;
          height: 20px;
        }

        .message-content {
          flex: 1;
          max-width: 70%;
        }

        .message.user .message-content {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
        }

        .message-text {
          background: #f3f4f6;
          padding: 12px 16px;
          border-radius: 12px;
          font-size: 14px;
          line-height: 1.5;
          color: #374151;
        }

        .message.user .message-text {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .message-timestamp {
          font-size: 11px;
          color: #9ca3af;
          margin-top: 4px;
          padding: 0 4px;
        }

        .citations {
          margin-top: 12px;
          padding: 12px;
          background: #f9fafb;
          border-radius: 8px;
          border-left: 3px solid #667eea;
        }

        .citations h4 {
          font-size: 12px;
          font-weight: 600;
          color: #374151;
          margin: 0 0 8px 0;
        }

        .citation-item {
          display: flex;
          gap: 8px;
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 6px;
        }

        .citation-number {
          flex-shrink: 0;
          font-weight: 600;
          color: #667eea;
        }

        .citation-text {
          flex: 1;
          line-height: 1.4;
        }

        .typing-indicator {
          display: flex;
          gap: 4px;
          padding: 12px 16px;
          background: #f3f4f6;
          border-radius: 12px;
          width: fit-content;
        }

        .typing-indicator span {
          width: 8px;
          height: 8px;
          background: #9ca3af;
          border-radius: 50%;
          animation: bounce 1.4s infinite ease-in-out;
        }

        .typing-indicator span:nth-child(1) {
          animation-delay: -0.32s;
        }

        .typing-indicator span:nth-child(2) {
          animation-delay: -0.16s;
        }

        @keyframes bounce {
          0%, 80%, 100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1);
          }
        }

        .error-message {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 12px;
          background: #fee2e2;
          border-radius: 8px;
          color: #dc2626;
          font-size: 14px;
        }

        .error-icon {
          width: 20px;
          height: 20px;
          flex-shrink: 0;
        }

        .agent-state-sidebar {
          width: 320px;
          border-left: 1px solid #e5e7eb;
          overflow-y: auto;
          padding: 20px;
        }

        .input-area {
          border-top: 1px solid #e5e7eb;
          padding: 16px;
          background: white;
        }

        .input-wrapper {
          display: flex;
          gap: 8px;
        }

        .chat-input {
          flex: 1;
          padding: 12px 16px;
          border: 2px solid #e5e7eb;
          border-radius: 24px;
          font-size: 14px;
          outline: none;
          transition: border-color 0.2s;
        }

        .chat-input:focus {
          border-color: #667eea;
        }

        .chat-input:disabled {
          background: #f9fafb;
          cursor: not-allowed;
        }

        .send-button {
          width: 44px;
          height: 44px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border: none;
          color: white;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 0.2s, opacity 0.2s;
        }

        .send-button:hover:not(:disabled) {
          transform: scale(1.05);
        }

        .send-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .send-button svg {
          width: 20px;
          height: 20px;
        }

        .spinner {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .connection-warning {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 8px;
          padding: 8px 12px;
          background: #fef3c7;
          border-radius: 6px;
          color: #92400e;
          font-size: 12px;
        }

        .warning-icon {
          width: 16px;
          height: 16px;
          flex-shrink: 0;
        }
      `}</style>
    </div>
  );
}
