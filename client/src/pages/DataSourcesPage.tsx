import { useQuery, useMutation } from '@tanstack/react-query';
import { Database, Plus, Trash2, RefreshCw, Loader2 } from 'lucide-react';
import { queryClient, apiRequest } from '@/lib/queryClient';
import type { DataSource } from '@shared/schema';
import { getDemoConfig } from '@/lib/demoConfig';

export function DataSourcesPage() {
  const { data: config } = useQuery({
    queryKey: ['/api/demo/config'],
    queryFn: getDemoConfig,
  });

  const { data: dataSources = [], isLoading } = useQuery<DataSource[]>({
    queryKey: ['/api/data-sources', config?.tenantId],
    enabled: !!config,
  });

  const createDataSource = useMutation({
    mutationFn: async (data: any) => {
      return apiRequest(`/api/data-sources`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/data-sources', config?.tenantId] });
    },
  });

  const deleteDataSource = useMutation({
    mutationFn: async (id: string) => {
      return apiRequest(`/api/data-sources/${id}`, { method: 'DELETE' });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/data-sources', config?.tenantId] });
    },
  });

  const handleCreate = () => {
    if (!config) return;
    const name = prompt('Enter data source name:');
    if (!name) return;
    const type = prompt('Enter type (postgres/mysql/api/csv):') || 'api';

    createDataSource.mutate({
      tenantId: config.tenantId,
      name,
      type,
      status: 'inactive',
      config: {},
    });
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" data-testid="text-page-title">Data Sources</h1>
          <p className="text-gray-400 mt-1">Connect external data sources</p>
        </div>
        <button
          onClick={handleCreate}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          data-testid="button-create-source"
        >
          <Plus className="w-5 h-5" />
          Add Data Source
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : dataSources.length === 0 ? (
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-12 text-center" data-testid="text-empty-state">
          <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">No data sources yet</h3>
          <p className="text-gray-400 mb-4">Connect databases, APIs, or file systems</p>
          <button
            onClick={handleCreate}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5" />
            Add Data Source
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dataSources.map((source) => (
            <div
              key={source.id}
              className="bg-[#161b22] border border-[#30363d] rounded-lg p-4 hover:border-blue-500 transition-colors"
              data-testid={`card-source-${source.id}`}
            >
              <div className="flex items-start justify-between mb-3">
                <Database className="w-8 h-8 text-green-600" />
                <div className="flex gap-1">
                  <button
                    className="p-1 text-gray-400 hover:text-blue-600 rounded"
                    data-testid={`button-sync-${source.id}`}
                  >
                    <RefreshCw className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteDataSource.mutate(source.id)}
                    className="p-1 text-gray-400 hover:text-red-600 rounded"
                    data-testid={`button-delete-${source.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <h3 className="font-semibold mb-1" data-testid={`text-name-${source.id}`}>
                {source.name}
              </h3>
              <div className="flex items-center gap-2 text-sm mb-2">
                <span className={`px-2 py-1 rounded text-xs ${
                  source.status === 'active' ? 'bg-green-100 text-green-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {source.status}
                </span>
                <span className="text-gray-500">• {source.type}</span>
              </div>
              {source.lastSync && (
                <p className="text-xs text-gray-400">
                  Last sync: {new Date(source.lastSync).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
