import React, { useState } from 'react';
import { Lightbulb, ChevronDown, ChevronUp, FileText, CheckCircle2 } from 'lucide-react';

interface InsightCardProps {
  title: string;
  content: string;
  confidence?: number;
  sources?: string[];
  category?: 'insight' | 'recommendation' | 'warning' | 'info';
  expandable?: boolean;
}

export function InsightCard({ 
  title, 
  content, 
  confidence, 
  sources = [],
  category = 'insight',
  expandable = true 
}: InsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const categoryConfig = {
    insight: {
      icon: Lightbulb,
      gradient: 'from-amber-500 to-orange-500',
      bg: 'bg-amber-50',
      border: 'border-amber-200',
      text: 'text-amber-700',
      shadow: 'shadow-amber-500/20',
    },
    recommendation: {
      icon: CheckCircle2,
      gradient: 'from-emerald-500 to-green-500',
      bg: 'bg-green-50',
      border: 'border-green-200',
      text: 'text-green-700',
      shadow: 'shadow-green-500/20',
    },
    warning: {
      icon: Lightbulb,
      gradient: 'from-red-500 to-rose-500',
      bg: 'bg-red-50',
      border: 'border-red-200',
      text: 'text-red-700',
      shadow: 'shadow-red-500/20',
    },
    info: {
      icon: Lightbulb,
      gradient: 'from-blue-500 to-cyan-500',
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      text: 'text-blue-700',
      shadow: 'shadow-blue-500/20',
    },
  };

  const config = categoryConfig[category];
  const Icon = config.icon;

  return (
    <div className={`bg-white rounded-2xl border-2 ${config.border} shadow-lg hover:shadow-xl transition-all duration-300 animate-scale-in overflow-hidden`}>
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className={`flex-shrink-0 w-12 h-12 bg-gradient-to-br ${config.gradient} rounded-xl flex items-center justify-center shadow-lg ${config.shadow}`}>
            <Icon size={24} className="text-white" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-3 mb-2">
              <h4 className="text-lg font-bold text-gray-900">{title}</h4>
              
              {/* Confidence Score */}
              {confidence !== undefined && (
                <div className={`flex-shrink-0 px-3 py-1 ${config.bg} rounded-full`}>
                  <span className={`text-xs font-bold ${config.text}`}>
                    {Math.round(confidence * 100)}% confident
                  </span>
                </div>
              )}
            </div>

            {/* Main Content */}
            <p className="text-gray-700 leading-relaxed">
              {expandable && content.length > 150 && !isExpanded
                ? `${content.substring(0, 150)}...`
                : content}
            </p>

            {/* Expand Button */}
            {expandable && content.length > 150 && (
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="mt-3 flex items-center gap-1 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
              >
                {isExpanded ? (
                  <>
                    <span>Show less</span>
                    <ChevronUp size={16} />
                  </>
                ) : (
                  <>
                    <span>Read more</span>
                    <ChevronDown size={16} />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Sources */}
      {sources.length > 0 && (
        <div className={`px-5 py-4 ${config.bg} border-t ${config.border}`}>
          <div className="flex items-start gap-2">
            <FileText size={16} className={`${config.text} mt-0.5 flex-shrink-0`} />
            <div className="flex-1 min-w-0">
              <p className={`text-xs font-semibold ${config.text} mb-2`}>
                Sources ({sources.length})
              </p>
              <div className="flex flex-wrap gap-2">
                {sources.slice(0, 3).map((source, index) => (
                  <button
                    key={index}
                    className="inline-flex items-center px-2.5 py-1 bg-white border border-gray-200 rounded-lg text-xs text-gray-700 hover:border-gray-300 hover:shadow-sm transition-all duration-200"
                  >
                    {source.length > 30 ? `${source.substring(0, 30)}...` : source}
                  </button>
                ))}
                {sources.length > 3 && (
                  <span className="inline-flex items-center px-2.5 py-1 text-xs text-gray-500">
                    +{sources.length - 3} more
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
