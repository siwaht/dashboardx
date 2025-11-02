import { useQuery, useMutation } from '@tanstack/react-query';
import { Upload, FileText, Trash2, Loader2 } from 'lucide-react';
import { queryClient, apiRequest } from '@/lib/queryClient';
import type { Document } from '@shared/schema';
import { getDemoConfig } from '@/lib/demoConfig';

export function DocumentsPage() {
  const { data: config } = useQuery({
    queryKey: ['/api/demo/config'],
    queryFn: getDemoConfig,
  });

  const { data: documents = [], isLoading } = useQuery<Document[]>({
    queryKey: ['/api/documents', config?.tenantId],
    queryFn: () => apiRequest(`/api/documents?tenantId=${config?.tenantId}`),
    enabled: !!config,
  });

  const deleteDocument = useMutation({
    mutationFn: async (id: string) => {
      return apiRequest(`/api/documents/${id}`, { method: 'DELETE' });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/documents', config?.tenantId] });
    },
  });

  const createDocument = useMutation({
    mutationFn: async (data: any) => {
      return apiRequest(`/api/documents`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/documents', config?.tenantId] });
    },
  });

  const handleUpload = () => {
    if (!config) return;
    
    // Create file input element
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.txt,.md,.docx';
    
    input.onchange = (e: Event) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      
      createDocument.mutate({
        tenantId: config.tenantId,
        title: file.name,
        status: 'processing',
        fileType: file.type || 'application/octet-stream',
        fileSize: file.size,
        metadata: { originalName: file.name, size: file.size },
      });
    };
    
    input.click();
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900" data-testid="text-page-title">Documents</h1>
          <p className="text-gray-600 mt-1">Manage your document library</p>
        </div>
        <button
          onClick={handleUpload}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          data-testid="button-upload"
        >
          <Upload className="w-5 h-5" />
          Upload Document
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
        </div>
      ) : documents.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-12 text-center" data-testid="text-empty-state">
          <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No documents yet</h3>
          <p className="text-gray-600 mb-4">Upload your first document to get started with RAG</p>
          <button
            onClick={handleUpload}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Upload className="w-5 h-5" />
            Upload Document
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md transition-shadow"
              data-testid={`card-document-${doc.id}`}
            >
              <div className="flex items-start justify-between mb-3">
                <FileText className="w-8 h-8 text-blue-600" />
                <button
                  onClick={() => deleteDocument.mutate(doc.id)}
                  className="p-1 text-gray-400 hover:text-red-600 rounded"
                  data-testid={`button-delete-${doc.id}`}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <h3 className="font-semibold text-gray-900 mb-1" data-testid={`text-title-${doc.id}`}>
                {doc.title}
              </h3>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <span className={`px-2 py-1 rounded text-xs ${
                  doc.status === 'completed' ? 'bg-green-100 text-green-700' :
                  doc.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {doc.status}
                </span>
                {doc.fileType && <span>• {doc.fileType}</span>}
              </div>
              {doc.createdAt && (
                <p className="text-xs text-gray-400 mt-2">
                  {new Date(doc.createdAt).toLocaleDateString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
