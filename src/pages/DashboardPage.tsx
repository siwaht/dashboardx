mport React, { useState } from 'react';
import { Sidebar } from '../components/layout/Sidebar';
import { ChatInterface } from '../components/chat/ChatInterface';
import { DocumentUpload } from '../components/documents/DocumentUpload';
import { DocumentList } from '../components/documents/DocumentList';
import { FileText, Database, Settings as SettingsIcon, Sparkles, Zap, Shield, Activity, Plug } from 'lucide-react';

type View = 'chat' | 'documents' | 'sources' | 'settings' | 'mcp';

export function DashboardPage() {
  const [currentView, setCurrentView] = useState<View>('chat');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [documentRefresh, setDocumentRefresh] = useState(0);

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setCurrentView('chat');
  };

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId);
    setCurrentView('chat');
  };

  const handleUploadComplete = () => {
    setDocumentRefresh((prev) => prev + 1);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/30">
      <Sidebar
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewChat={handleNewChat}
        onNavigate={setCurrentView}
        currentView={currentView}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        {currentView === 'chat' && (
          <div className="flex-1">
            <ChatInterface
              sessionId={currentSessionId}
              onNewSession={setCurrentSessionId}
            />
          </div>
        )}

        {currentView === 'documents' && (
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <div className="max-w-5xl mx-auto p-8 animate-fade-in">
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-500/30">
                    <FileText size={24} className="text-white" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-600 via-pink-600 to-rose-600 bg-clip-text text-transparent">
                      Documents
                    </h1>
                    <p className="text-gray-600">
                      Upload and manage your knowledge base documents
                    </p>
                  </div>
                </div>
              </div>

              <div className="mb-8">
                <DocumentUpload onUploadComplete={handleUploadComplete} />
              </div>

              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Sparkles size={20} className="text-purple-600" />
                  Your Documents
                </h2>
                <DocumentList refresh={documentRefresh} />
              </div>
            </div>
          </div>
        )}

        {currentView === 'sources' && (
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <div className="max-w-5xl mx-auto p-8 animate-fade-in">
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
                    <Database size={24} className="text-white" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 via-cyan-600 to-blue-600 bg-clip-text text-transparent">
                      Data Sources
                    </h1>
                    <p className="text-gray-600">
                      Connect external data sources for automated ingestion
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {[
                  { name: 'Amazon S3', type: 's3', icon: Database, color: 'from-orange-500 to-red-500', description: 'Sync files from S3 buckets' },
                  { name: 'SharePoint', type: 'sharepoint', icon: Database, color: 'from-blue-500 to-cyan-500', description: 'Connect to SharePoint sites' },
                  { name: 'Confluence', type: 'confluence', icon: Database, color: 'from-indigo-500 to-blue-500', description: 'Import Confluence pages' },
                  { name: 'Google Drive', type: 'google_drive', icon: Database, color: 'from-green-500 to-emerald-500', description: 'Access Google Drive files' },
                ].map((source, index) => (
                  <div
                    key={source.type}
                    style={{ animationDelay: `${index * 100}ms` }}
                    className="group relative p-6 bg-white border border-gray-200 rounded-2xl hover:shadow-xl hover:border-transparent transition-all duration-300 animate-fade-in-up overflow-hidden"
                  >
                    {/* Gradient background on hover */}
                    <div className={`absolute inset-0 bg-gradient-to-br ${source.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>
                    
                    <div className="relative flex items-start gap-4">
                      <div className={`flex-shrink-0 w-14 h-14 bg-gradient-to-br ${source.color} rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 group-hover:rotate-3 transition-all duration-300`}>
                        <source.icon size={24} className="text-white" />
                      </div>
                      <div className="flex-1">
                        <h3 className="font-bold text-gray-900 mb-1 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:bg-clip-text" style={{ backgroundImage: `linear-gradient(to right, var(--tw-gradient-stops))` }}>
                          {source.name}
                        </h3>
                        <p className="text-sm text-gray-600 mb-4">
                          {source.description}
                        </p>
                        <button className="group/btn inline-flex items-center gap-2 px-4 py-2 text-sm font-medium bg-gray-100 hover:bg-gradient-to-r hover:from-blue-600 hover:to-indigo-600 hover:text-white rounded-xl transition-all duration-300 hover:shadow-lg hover:scale-105">
                          <Zap size={14} className="group-hover/btn:animate-pulse" />
                          Configure
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {currentView === 'mcp' && (
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <div className="max-w-5xl mx-auto p-8 animate-fade-in">
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-violet-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg shadow-violet-500/30">
                    <Plug size={24} className="text-white" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-violet-600 via-purple-600 to-fuchsia-600 bg-clip-text text-transparent">
                      MCP Servers
                    </h1>
                    <p className="text-gray-600">
                      Manage Model Context Protocol server connections
                    </p>
                  </div>
                </div>
              </div>

              {/* Active Servers */}
              <div className="mb-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Sparkles size={20} className="text-violet-600" />
                  Active Servers
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {[
                    { 
                      name: 'Filesystem MCP', 
                      type: 'filesystem', 
                      status: 'connected',
                      description: 'Access local file system',
                      color: 'from-blue-500 to-cyan-500',
                      tools: 12
                    },
                    { 
                      name: 'GitHub MCP', 
                      type: 'github', 
                      status: 'connected',
                      description: 'Interact with GitHub repositories',
                      color: 'from-gray-700 to-gray-900',
                      tools: 8
                    },
                    { 
                      name: 'PostgreSQL MCP', 
                      type: 'postgres', 
                      status: 'disconnected',
                      description: 'Query PostgreSQL databases',
                      color: 'from-blue-600 to-indigo-600',
                      tools: 15
                    },
                    { 
                      name: 'Slack MCP', 
                      type: 'slack', 
                      status: 'connected',
                      description: 'Send messages and manage channels',
                      color: 'from-purple-500 to-pink-500',
                      tools: 6
                    },
                  ].map((server, index) => (
                    <div
                      key={server.type}
                      style={{ animationDelay: `${index * 100}ms` }}
                      className="group relative p-6 bg-white border border-gray-200 rounded-2xl hover:shadow-xl hover:border-transparent transition-all duration-300 animate-fade-in-up overflow-hidden"
                    >
                      {/* Gradient background on hover */}
                      <div className={`absolute inset-0 bg-gradient-to-br ${server.color} opacity-0 group-hover:opacity-5 transition-opacity duration-300`}></div>
                      
                      <div className="relative">
                        <div className="flex items-start justify-between mb-4">
                          <div className="flex items-start gap-4">
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            <div className="max-w-4xl mx-auto p-8 animate-fade-in">
              <div className="mb-8">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-gray-700 to-gray-900 rounded-2xl flex items-center justify-center shadow-lg shadow-gray-500/30">
                    <SettingsIcon size={24} className="text-white" />
                  </div>
                  <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-gray-700 via-gray-800 to-gray-900 bg-clip-text text-transparent">
                      Settings
                    </h1>
                    <p className="text-gray-600">
                      Manage your account and platform preferences
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                {/* Agent Configuration Card */}
                <div className="group bg-white rounded-2xl border border-gray-200 hover:shadow-xl hover:border-blue-200 transition-all duration-300 overflow-hidden">
                  <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-blue-50/50 to-indigo-50/50">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                        <Activity size={20} className="text-white" />
                      </div>
                      <h3 className="font-bold text-gray-900 text-lg">
                        Agent Configuration
                      </h3>
                    </div>
                  </div>
                  <div className="p-6 space-y-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-900 mb-3">
                        Temperature
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        defaultValue="0.7"
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                      />
                      <div className="flex justify-between mt-2">
                        <span className="text-xs text-gray-500">Focused (0)</span>
                        <span className="text-xs font-medium text-blue-600">0.7</span>
                        <span className="text-xs text-gray-500">Creative (1)</span>
                      </div>
                      <p className="text-xs text-gray-500 mt-2 flex items-center gap-1">
                        <Sparkles size={12} className="text-blue-500" />
                        Controls response creativity and randomness
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-900 mb-3">
                        Max Context Documents
                      </label>
                      <input
                        type="number"
                        defaultValue="5"
                        min="1"
                        max="20"
                        className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 font-medium"
                      />
                      <p className="text-xs text-gray-500 mt-2">
                        Maximum number of documents to retrieve per query
                      </p>
                    </div>
                  </div>
                </div>

                {/* Security & Privacy Card */}
                <div className="group bg-white rounded-2xl border border-gray-200 hover:shadow-xl hover:border-green-200 transition-all duration-300 overflow-hidden">
                  <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-green-50/50 to-emerald-50/50">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg">
                        <Shield size={20} className="text-white" />
                      </div>
                      <h3 className="font-bold text-gray-900 text-lg">
                        Security & Privacy
                      </h3>
                    </div>
                  </div>
                  <div className="p-6 space-y-4">
                    <label className="group/item flex items-center gap-4 p-4 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer">
                      <input 
                        type="checkbox" 
                        defaultChecked 
                        className="w-5 h-5 rounded border-gray-300 text-green-600 focus:ring-green-500 cursor-pointer" 
                      />
                      <div className="flex-1">
                        <span className="text-sm font-medium text-gray-900 block">
                          Enable Row Level Security (RLS)
                        </span>
                        <span className="text-xs text-gray-500">
                          Enforce tenant isolation at database level
                        </span>
                      </div>
                    </label>
                    <label className="group/item flex items-center gap-4 p-4 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer">
                      <input 
                        type="checkbox" 
                        defaultChecked 
                        className="w-5 h-5 rounded border-gray-300 text-green-600 focus:ring-green-500 cursor-pointer" 
                      />
                      <div className="flex-1">
                        <span className="text-sm font-medium text-gray-900 block">
                          Log Data Access Attempts
                        </span>
                        <span className="text-xs text-gray-500">
                          Track all document and data access for audit
                        </span>
                      </div>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
