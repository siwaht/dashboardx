import React, { useEffect, useState } from 'react';
import { FileText, Trash2, Clock, CheckCircle, XCircle, Loader2, Download, Eye, Sparkles } from 'lucide-react';
import { supabase } from '../../lib/supabase';
import type { Database } from '../../lib/database.types';

type Document = Database['public']['Tables']['documents']['Row'];

export function DocumentList({ refresh }: { refresh?: number }) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    loadDocuments();
  }, [refresh]);

  const loadDocuments = async () => {
    setLoading(true);
    const { data, error } = await supabase
      .from('documents')
      .select('*')
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error loading documents:', error);
    } else {
      setDocuments(data || []);
    }
    setLoading(false);
  };

  const deleteDocument = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    setDeletingId(id);
    const { error } = await supabase.from('documents').delete().eq('id', id);

    if (error) {
      console.error('Error deleting document:', error);
    } else {
      loadDocuments();
    }
    setDeletingId(null);
  };

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={20} className="text-green-500" />;
      case 'failed':
        return <XCircle size={20} className="text-red-500" />;
      case 'processing':
        return <Loader2 size={20} className="text-blue-500 animate-spin" />;
      default:
        return <Clock size={20} className="text-amber-500" />;
    }
  };

  const getStatusBadge = (status: Document['status']) => {
    const styles = {
      pending: 'badge-warning',
      processing: 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/30',
      completed: 'badge-success',
      failed: 'badge-error',
    };

    return (
      <span
        className={`px-3 py-1 text-xs font-semibold rounded-full ${styles[status]} animate-fade-in`}
      >
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  const getFileIcon = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase();
    const iconColors: Record<string, string> = {
      pdf: 'from-red-500 to-rose-500',
      doc: 'from-blue-500 to-cyan-500',
      docx: 'from-blue-500 to-cyan-500',
      txt: 'from-gray-500 to-slate-500',
      csv: 'from-green-500 to-emerald-500',
      json: 'from-yellow-500 to-amber-500',
    };
    return iconColors[ext || ''] || 'from-purple-500 to-pink-500';
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="relative">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full blur-xl opacity-30 animate-pulse"></div>
          <Loader2 size={48} className="relative animate-spin text-blue-600" />
        </div>
        <p className="mt-4 text-gray-600 font-medium">Loading documents...</p>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-16 animate-fade-in">
        <div className="relative inline-block mb-6">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full blur-2xl opacity-20"></div>
          <div className="relative w-20 h-20 mx-auto bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-xl">
            <FileText size={40} className="text-white" />
          </div>
        </div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">No documents yet</h3>
        <p className="text-gray-600 mb-6">Upload your first document to get started</p>
        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
          <Sparkles size={14} className="text-blue-500" />
          <span>Documents will appear here once uploaded</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {documents.map((doc, index) => (
        <div
          key={doc.id}
          style={{ animationDelay: `${index * 50}ms` }}
          className="group relative flex items-center gap-4 p-5 bg-white border border-gray-200 rounded-2xl hover:shadow-xl hover:border-blue-200 transition-all duration-300 animate-fade-in-up overflow-hidden"
        >
          {/* Gradient background on hover */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-50/0 via-purple-50/0 to-indigo-50/0 group-hover:from-blue-50/50 group-hover:via-purple-50/30 group-hover:to-indigo-50/50 transition-all duration-300 rounded-2xl"></div>
          
          {/* File Icon */}
          <div className={`relative flex-shrink-0 w-14 h-14 bg-gradient-to-br ${getFileIcon(doc.title)} rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-300`}>
            <FileText size={24} className="text-white" />
          </div>

          {/* Status Icon */}
          <div className="relative flex-shrink-0 w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center group-hover:bg-white transition-colors">
            {getStatusIcon(doc.status)}
          </div>

          {/* Document Info */}
          <div className="relative flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                {doc.title}
              </h3>
              {getStatusBadge(doc.status)}
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              {doc.file_type && (
                <span className="flex items-center gap-1.5 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                  <span className="uppercase">{doc.file_type.split('/').pop()}</span>
                </span>
              )}
              {doc.file_size && (
                <span className="flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
                  {(doc.file_size / 1024).toFixed(2)} KB
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                {new Date(doc.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="relative flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <button
              className="p-2.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-xl transition-all duration-300 hover:scale-110"
              title="View document"
            >
              <Eye size={18} />
            </button>
            <button
              className="p-2.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-xl transition-all duration-300 hover:scale-110"
              title="Download document"
            >
              <Download size={18} />
            </button>
            <button
              onClick={() => deleteDocument(doc.id)}
              disabled={deletingId === doc.id}
              className="p-2.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-xl transition-all duration-300 hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Delete document"
            >
              {deletingId === doc.id ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Trash2 size={18} />
              )}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
