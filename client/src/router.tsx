import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import App from './App';
import { AuthPage } from './pages/AuthPage';
import { Layout } from './components/Layout';
import { DashboardPage } from './pages/DashboardPage';
import { ChatPage } from './pages/ChatPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { DataSourcesPage } from './pages/DataSourcesPage';
import { AgentsPage } from './pages/AgentsPage';
import { UsersPage } from './pages/UsersPage';

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
        path: '/',
        element: <Layout />,
        children: [
          {
            index: true,
            element: <DashboardPage />,
          },
          {
            path: 'chat',
            element: <ChatPage />,
          },
          {
            path: 'documents',
            element: <DocumentsPage />,
          },
          {
            path: 'data-sources',
            element: <DataSourcesPage />,
          },
          {
            path: 'agents',
            element: <AgentsPage />,
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
