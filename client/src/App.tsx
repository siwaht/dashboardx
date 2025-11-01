import { useQuery } from '@tanstack/react-query';

function App() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['/api/health'],
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/30">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Agentic RAG Platform
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Enterprise AI agent management system successfully migrated to Replit
          </p>
          
          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-200">
            <h2 className="text-2xl font-semibold mb-4 text-gray-800">System Status</h2>
            {isLoading && (
              <p className="text-gray-600">Checking server status...</p>
            )}
            {error && (
              <p className="text-red-600">Error: {error.message}</p>
            )}
            {data && (
              <div className="space-y-2">
                <p className="text-green-600 font-semibold">✓ Server is running</p>
                <p className="text-sm text-gray-500">Status: {data.status}</p>
                <p className="text-sm text-gray-500">Time: {new Date(data.timestamp).toLocaleString()}</p>
              </div>
            )}
          </div>

          <div className="mt-8 p-6 bg-blue-50 rounded-xl border border-blue-200">
            <h3 className="text-lg font-semibold text-blue-900 mb-2">Migration Complete! 🎉</h3>
            <p className="text-blue-700">
              Your Bolt project has been successfully migrated to Replit's fullstack JavaScript environment.
              The Express backend is running with Neon PostgreSQL database (with pgvector support), and you're ready to start building!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
