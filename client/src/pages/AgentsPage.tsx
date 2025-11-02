import { useQuery, useMutation } from '@tanstack/react-query';
import { Bot, Plus, Play, Trash2, Loader2 } from 'lucide-react';
import { queryClient, apiRequest } from '@/lib/queryClient';
import type { CustomAgent } from '@shared/schema';
import { getDemoConfig } from '@/lib/demoConfig';

export function AgentsPage() {
  const { data: config } = useQuery({
    queryKey: ['/api/demo/config'],
    queryFn: getDemoConfig,
  });

  const { data: agents = [], isLoading } = useQuery<CustomAgent[]>({
    queryKey: ['/api/agents', config?.tenantId],
    queryFn: () => apiRequest(`/api/agents?tenantId=${config?.tenantId}`),
    enabled: !!config,
  });

  const createAgent = useMutation({
    mutationFn: async (data: any) => {
      return apiRequest(`/api/agents`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/agents', config?.tenantId] });
    },
  });

  const deleteAgent = useMutation({
    mutationFn: async (id: string) => {
      return apiRequest(`/api/agents/${id}`, { method: 'DELETE' });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/agents', config?.tenantId] });
    },
  });

  const executeAgent = useMutation({
    mutationFn: async (agentId: string) => {
      if (!config) throw new Error('Config not loaded');
      return apiRequest(`/api/agents/${agentId}/execute`, {
        method: 'POST',
        body: JSON.stringify({
          tenantId: config.tenantId,
          userId: config.userId,
          inputData: { query: 'Test execution' },
          status: 'running',
        }),
      });
    },
    onSuccess: () => {
      alert('Agent execution started successfully!');
    },
  });

  const handleCreateAgent = () => {
    if (!config) return;
    const name = prompt('Enter agent name:');
    if (!name) return;

    createAgent.mutate({
      tenantId: config.tenantId,
      userId: config.userId,
      name,
      agentType: 'custom',
      description: 'Custom agent for data analysis',
      config: {},
      capabilities: {},
      status: 'active',
    });
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" data-testid="text-page-title">Agents</h1>
          <p className="text-gray-600 mt-1">Manage your AI agents</p>
        </div>
        <button
          onClick={handleCreateAgent}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          data-testid="button-create-agent"
        >
          <Plus className="w-5 h-5" />
          Create Agent
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : agents.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center" data-testid="text-empty-state">
          <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No agents yet</h3>
          <p className="text-gray-600 mb-4">Create your first AI agent to automate tasks</p>
          <button
            onClick={handleCreateAgent}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5" />
            Create Agent
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <div
              key={agent.id}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
              data-testid={`card-agent-${agent.id}`}
            >
              <div className="flex items-start justify-between mb-3">
                <Bot className="w-8 h-8 text-purple-600" />
                <div className="flex gap-1">
                  <button
                    onClick={() => executeAgent.mutate(agent.id)}
                    disabled={executeAgent.isPending}
                    className="p-1 text-gray-400 hover:text-green-600 rounded disabled:opacity-50"
                    data-testid={`button-run-${agent.id}`}
                  >
                    <Play className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => deleteAgent.mutate(agent.id)}
                    className="p-1 text-gray-400 hover:text-red-600 rounded"
                    data-testid={`button-delete-${agent.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1" data-testid={`text-name-${agent.id}`}>
                {agent.name}
              </h3>
              {agent.description && (
                <p className="text-sm text-gray-600 mb-2">{agent.description}</p>
              )}
              <div className="flex items-center gap-2 text-sm">
                <span className={`px-2 py-1 rounded text-xs ${
                  agent.status === 'active' ? 'bg-green-100 text-green-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {agent.status}
                </span>
                <span className="text-gray-500">• {agent.agentType}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
