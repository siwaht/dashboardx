import React, { useState } from 'react';
import { Upload, FileText, X, Loader2, CheckCircle, Cloud, Sparkles } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { supabase } from '../../lib/supabase';

export function DocumentUpload({ onUploadComplete }: { onUploadComplete?: () => void }) {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const { profile } = useAuth();

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const files = Array.from(e.dataTransfer.files);
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const files = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...files]);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (!profile || selectedFiles.length === 0) return;

    setUploading(true);
    setUploadSuccess(false);

    try {
      for (const file of selectedFiles) {
        // Generate unique file path
        const fileExt = file.name.split('.').pop();
        const fileName = `${profile.tenant_id}/${Date.now()}-${Math.random().toString(36).substring(7)}.${fileExt}`;
        
        // Upload file to Supabase Storage
        const { data: uploadData, error: uploadError } = await supabase.storage
          .from('documents')
          .upload(fileName, file, {
            cacheControl: '3600',
            upsert: false
          });

        if (uploadError) throw uploadError;

        // Get public URL
        const { data: { publicUrl } } = supabase.storage
          .from('documents')
          .getPublicUrl(fileName);

        // Create database record
        const { error: dbError } = await supabase.from('documents').insert({
          tenant_id: profile.tenant_id,
          title: file.name,
          file_type: file.type || 'unknown',
          file_size: file.size,
          file_path: fileName,
          file_url: publicUrl,
          status: 'pending',
          uploaded_by: profile.id,
        });

        if (dbError) {
          // Rollback: delete uploaded file if database insert fails
          await supabase.storage.from('documents').remove([fileName]);
          throw dbError;
        }
      }

      setUploadSuccess(true);
      setTimeout(() => {
        setSelectedFiles([]);
        setUploadSuccess(false);
        onUploadComplete?.();
      }, 2000);
    } catch (error) {
      console.error('Error uploading files:', error);
      alert('Failed to upload files. Please try again.');
    } finally {
      setUploading(false);
    }
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

  return (
    <div className="space-y-6">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 overflow-hidden ${
          dragActive
            ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 scale-[1.02]'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gradient-to-br hover:from-blue-50/50 hover:to-indigo-50/50'
        }`}
      >
        {/* Animated background effect */}
        <div className={`absolute inset-0 bg-gradient-to-br from-blue-500/5 via-purple-500/5 to-indigo-500/5 transition-opacity duration-300 ${dragActive ? 'opacity-100' : 'opacity-0'}`}></div>
        
        <div className="relative z-10">
          <div className="relative inline-block mb-6">
            <div className={`absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full blur-xl opacity-30 transition-all duration-300 ${dragActive ? 'scale-110 opacity-50' : ''}`}></div>
            <div className={`relative w-20 h-20 mx-auto bg-gradient-to-br from-blue-500 via-purple-500 to-indigo-600 rounded-2xl flex items-center justify-center shadow-xl transition-all duration-300 ${dragActive ? 'scale-110 rotate-6' : 'hover:scale-105'}`}>
              <Cloud size={40} className="text-white" />
            </div>
          </div>
          
          <h3 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            {dragActive ? 'Drop your files here' : 'Upload Documents'}
          </h3>
          <p className="text-gray-600 mb-2">
            Drag and drop files here, or click to browse
          </p>
          <p className="text-sm text-gray-500 mb-6 flex items-center justify-center gap-2">
            <Sparkles size={14} className="text-blue-500" />
            Supports PDF, DOCX, TXT, CSV, JSON and more
          </p>
          
          <label className="inline-block">
            <input
              type="file"
              multiple
              onChange={handleFileSelect}
              className="hidden"
              accept=".pdf,.doc,.docx,.txt,.csv,.json"
            />
            <span className="group inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-500 hover:to-indigo-500 cursor-pointer transition-all duration-300 shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40 hover:scale-105 active:scale-95 font-medium">
              <Upload size={18} className="transition-transform group-hover:-translate-y-0.5" />
              Select Files
            </span>
          </label>
        </div>
      </div>

      {selectedFiles.length > 0 && (
        <div className="space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 flex items-center gap-2">
              <FileText size={18} className="text-blue-600" />
              Selected Files ({selectedFiles.length})
            </h3>
            <button
              onClick={() => setSelectedFiles([])}
              className="text-sm text-gray-500 hover:text-red-600 transition-colors"
            >
              Clear all
            </button>
          </div>
          
          <div className="space-y-2">
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                style={{ animationDelay: `${index * 50}ms` }}
                className="group flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-xl hover:shadow-lg hover:border-blue-200 transition-all duration-300 animate-slide-in-left"
              >
                <div className={`flex-shrink-0 w-12 h-12 bg-gradient-to-br ${getFileIcon(file.name)} rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform`}>
                  <FileText size={20} className="text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                    {file.name}
                  </p>
                  <div className="flex items-center gap-3 text-sm text-gray-500">
                    <span>{(file.size / 1024).toFixed(2)} KB</span>
                    <span className="w-1 h-1 rounded-full bg-gray-300"></span>
                    <span className="uppercase">{file.name.split('.').pop()}</span>
                  </div>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="flex-shrink-0 p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all duration-300 hover:scale-110"
                >
                  <X size={18} />
                </button>
              </div>
            ))}
          </div>

          <button
            onClick={uploadFiles}
            disabled={uploading || uploadSuccess}
            className="group w-full flex items-center justify-center gap-3 px-6 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-lg shadow-blue-500/30 hover:shadow-xl hover:shadow-blue-500/40 hover:scale-[1.02] active:scale-95 disabled:hover:scale-100 font-medium text-lg relative overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700"></div>
            
            {uploading ? (
              <>
                <Loader2 size={20} className="animate-spin relative z-10" />
                <span className="relative z-10">Uploading...</span>
              </>
            ) : uploadSuccess ? (
              <>
                <CheckCircle size={20} className="relative z-10" />
                <span className="relative z-10">Upload Complete!</span>
              </>
            ) : (
              <>
                <Upload size={20} className="relative z-10 transition-transform group-hover:-translate-y-0.5" />
                <span className="relative z-10">
                  Upload {selectedFiles.length} {selectedFiles.length === 1 ? 'file' : 'files'}
                </span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
