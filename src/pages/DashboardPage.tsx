import React, { useState } from 'react';
import { EnhancedChatInterface } from '../components/chat/EnhancedChatInterface';
import { DocumentManagement } from '../components/documents/DocumentManagement';
import { UserManagement } from '../components/admin/UserManagement';
import { Settings } from '../components/settings/Settings';
import { Sidebar } from '../components/layout/Sidebar';
import { DataSources } from '../components/data/DataSources';
import { MCP } from '../components/mcp/MCP';
import { useAuth } from '../contexts/AuthContext';

export function DashboardPage() {
  const [currentView, setCurrentView] = useState<'chat' | 'documents' | 'sources' | 'mcp' | 'users' | 'settings'>('chat');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const { profile } = useAuth();

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setCurrentView('chat');
  };

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setCurrentView('chat');
  };

  const renderContent = () => {
    switch (currentView) {
      case 'chat':
        return <EnhancedChatInterface sessionId={currentSessionId} onNewSession={handleSessionSelect} />;
      case 'documents':
        return <DocumentManagement />;
      case 'sources':
        return <DataSources />;
      case 'mcp':
        return <MCP />;
      case 'users':
        return <UserManagement />;
      case 'settings':
        return <Settings />;
      default:
        return <div>Select a view</div>;
    }
  };

  if (!profile) {
    return <div>Loading...</div>;
  }

  return (
    <div className="flex h-screen bg-gray-100 font-sans">
      <Sidebar
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewChat={handleNewChat}
        onNavigate={setCurrentView}
        currentView={currentView}
      />
      <main className="flex-1 overflow-y-auto">
        {renderContent()}
      </main>
    </div>
  );
}
