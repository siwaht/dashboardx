import { createBrowserRouter, RouterProvider, useOutletContext } from 'react-router-dom';
import App from './App';
import { AuthPage } from './pages/AuthPage';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { ChatInterface } from './components/chat/ChatInterface';
import { DocumentUpload } from './components/documents/DocumentUpload';
import { DocumentList } from './components/documents/DocumentList';
import { UsersPage } from './pages/UsersPage';
import React from 'react';

type DashboardContext = {
  currentSessionId: string | null;
  setCurrentSessionId: React.Dispatch<React.SetStateAction<string | null>>;
};

function ChatRoute() {
  const { currentSessionId, setCurrentSessionId } = useOutletContext<DashboardContext>();
  return <ChatInterface sessionId={currentSessionId} onNewSession={setCurrentSessionId} />;
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <App />,
    children: [
      {
        path: 'auth',
        element: <AuthPage />,
      },
      {
        path: 'dashboard',
        element: <DashboardLayout />,
        children: [
          {
            path: 'chat',
            element: <ChatRoute />,
          },
          {
            path: 'documents',
            element: (
              <div className="flex-1 overflow-y-auto custom-scrollbar">
                <div className="max-w-5xl mx-auto p-8 animate-fade-in">
                  <div className="mb-8">
                    <DocumentUpload onUploadComplete={() => {}} />
                  </div>
                  <div>
                    <DocumentList refresh={0} />
                  </div>
                </div>
              </div>
            ),
          },
          {
            path: 'users',
            element: <UsersPage />,
          },
          {
            path: 'settings',
            element: <div>Settings Page</div>,
          },
        ],
      },
    ],
  },
]);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
