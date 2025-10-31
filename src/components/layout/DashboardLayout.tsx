import React from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Sidebar } from './Sidebar';

type View = 'chat' | 'documents' | 'sources' | 'settings' | 'mcp' | 'users';

export function DashboardLayout() {
  const [currentSessionId, setCurrentSessionId] = React.useState<string | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  const handleNewChat = () => {
    setCurrentSessionId(null);
    navigate('/dashboard/chat');
  };

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    navigate('/dashboard/chat');
  };

  const currentView = (location.pathname.split('/').pop() || 'chat') as View;

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/30">
      <Sidebar
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewChat={handleNewChat}
        onNavigate={(view) => navigate(`/dashboard/${view}`)}
        currentView={currentView}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Outlet context={{ currentSessionId, setCurrentSessionId }} />
      </div>
    </div>
  );
}
