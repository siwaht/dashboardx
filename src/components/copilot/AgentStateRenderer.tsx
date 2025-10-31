/**
 * Agent State Renderer Component
 * 
 * Displays real-time agent reasoning state, including:
 * - Current step in the workflow
 * - Agent thoughts and reasoning
 * - Tools being used
 * - Progress indicator
 */

import React from 'react';
import { useCopilotAgent } from '../../hooks/useCopilotAgent';

interface AgentStateRendererProps {
  className?: string;
}

export function AgentStateRenderer({ className = '' }: AgentStateRendererProps) {
  const { agentState, isProcessing, isConnected } = useCopilotAgent();

  if (!isConnected) {
    return (
      <div className={`agent-state-renderer ${className}`}>
        <div className="connection-status disconnected">
          <div className="status-indicator"></div>
          <span>Connecting to agent...</span>
        </div>
      </div>
    );
  }

  if (!isProcessing && !agentState) {
    return null;
  }

  return (
    <div className={`agent-state-renderer ${className}`}>
      {/* Connection Status */}
      <div className="connection-status connected">
        <div className="status-indicator"></div>
        <span>Agent Active</span>
      </div>

      {/* Current Step */}
      {agentState?.step && (
        <div className="current-step">
          <div className="step-header">
            <span className="step-label">Current Step:</span>
            <span className="step-value">{formatStep(agentState.step)}</span>
          </div>
          {agentState.message && (
            <p className="step-message">{agentState.message}</p>
          )}
        </div>
      )}

      {/* Progress Bar */}
      {agentState?.progress !== undefined && (
        <div className="progress-container">
          <div className="progress-bar-wrapper">
            <div 
              className="progress-bar"
              style={{ width: `${agentState.progress}%` }}
            >
              <span className="progress-text">{agentState.progress}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Agent Thoughts */}
      {agentState?.all_thoughts && agentState.all_thoughts.length > 0 && (
        <div className="agent-thoughts">
          <h4 className="thoughts-header">
            <svg className="icon" viewBox="0 0 20 20" fill="currentColor">
              <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
              <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd" />
            </svg>
            Agent Reasoning
          </h4>
          <div className="thoughts-list">
            {agentState.all_thoughts.map((thought: string, idx: number) => (
              <div key={idx} className="thought-item">
                <span className="thought-number">{idx + 1}</span>
                <span className="thought-text">{thought}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tools Used */}
      {agentState?.tools_used && agentState.tools_used.length > 0 && (
        <div className="tools-used">
          <h4 className="tools-header">
            <svg className="icon" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
            </svg>
            Tools Used
          </h4>
          <div className="tools-list">
            {agentState.tools_used.map((tool: string, idx: number) => (
              <span key={idx} className="tool-badge">
                {formatToolName(tool)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Processing Indicator */}
      {isProcessing && (
        <div className="processing-indicator">
          <div className="spinner"></div>
          <span>Agent is thinking...</span>
        </div>
      )}

      <style>{`
        .agent-state-renderer {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 12px;
          padding: 20px;
          color: white;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .connection-status {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 16px;
          font-size: 14px;
          font-weight: 500;
        }

        .status-indicator {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          animation: pulse 2s infinite;
        }

        .connected .status-indicator {
          background-color: #10b981;
        }

        .disconnected .status-indicator {
          background-color: #ef4444;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .current-step {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 16px;
        }

        .step-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .step-label {
          font-size: 12px;
          opacity: 0.8;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .step-value {
          font-size: 14px;
          font-weight: 600;
        }

        .step-message {
          font-size: 13px;
          opacity: 0.9;
          margin: 0;
        }

        .progress-container {
          margin-bottom: 16px;
        }

        .progress-bar-wrapper {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 8px;
          height: 24px;
          overflow: hidden;
          position: relative;
        }

        .progress-bar {
          background: linear-gradient(90deg, #10b981 0%, #059669 100%);
          height: 100%;
          transition: width 0.3s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 8px;
        }

        .progress-text {
          font-size: 12px;
          font-weight: 600;
          color: white;
        }

        .agent-thoughts,
        .tools-used {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          padding: 12px;
          margin-bottom: 16px;
        }

        .thoughts-header,
        .tools-header {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          font-weight: 600;
          margin-bottom: 12px;
        }

        .icon {
          width: 16px;
          height: 16px;
        }

        .thoughts-list {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .thought-item {
          display: flex;
          gap: 12px;
          font-size: 13px;
          line-height: 1.5;
        }

        .thought-number {
          flex-shrink: 0;
          width: 20px;
          height: 20px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: 600;
        }

        .thought-text {
          flex: 1;
          opacity: 0.9;
        }

        .tools-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .tool-badge {
          background: rgba(255, 255, 255, 0.2);
          padding: 4px 12px;
          border-radius: 12px;
          font-size: 12px;
          font-weight: 500;
        }

        .processing-indicator {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 12px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          font-size: 14px;
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

// Helper functions
function formatStep(step: string): string {
  return step
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function formatToolName(tool: string): string {
  return tool
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
