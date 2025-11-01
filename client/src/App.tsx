import { Route, Switch } from 'wouter';
import { useAuth } from './contexts/SimpleAuthContext';
import { Layout } from './components/Layout';
import { LoginPage } from './pages/LoginPage';
import { ChatPage } from './pages/ChatPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { AgentsPage } from './pages/AgentsPage';
import { DataSourcesPage } from './pages/DataSourcesPage';
import { AnalyticsPage } from './pages/AnalyticsPage';

function App() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage />;
  }

  return (
    <Layout>
      <Switch>
        <Route path="/" component={ChatPage} />
        <Route path="/documents" component={DocumentsPage} />
        <Route path="/agents" component={AgentsPage} />
        <Route path="/data-sources" component={DataSourcesPage} />
        <Route path="/analytics" component={AnalyticsPage} />
        <Route>404 - Page not found</Route>
      </Switch>
    </Layout>
  );
}

export default App;
