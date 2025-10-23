import React from 'react';
import { BarChart3, TrendingUp, TrendingDown, Download } from 'lucide-react';

interface DataPoint {
  label: string;
  value: number;
  color?: string;
}

interface ChartCardProps {
  title: string;
  description?: string;
  data: DataPoint[];
  type?: 'bar' | 'line' | 'pie';
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
}

export function ChartCard({ 
  title, 
  description, 
  data, 
  type = 'bar',
  trend,
  trendValue 
}: ChartCardProps) {
  const maxValue = Math.max(...data.map(d => d.value));
  
  const getBarColor = (index: number) => {
    const colors = [
      'from-blue-500 to-cyan-500',
      'from-purple-500 to-pink-500',
      'from-indigo-500 to-blue-500',
      'from-emerald-500 to-green-500',
      'from-amber-500 to-orange-500',
    ];
    return colors[index % colors.length];
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300 animate-scale-in">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30">
              <BarChart3 size={20} className="text-white" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">{title}</h3>
          </div>
          {description && (
            <p className="text-sm text-gray-600 ml-13">{description}</p>
          )}
        </div>
        
        {/* Trend Indicator */}
        {trend && trendValue && (
          <div className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-semibold ${
            trend === 'up' ? 'bg-green-50 text-green-700' :
            trend === 'down' ? 'bg-red-50 text-red-700' :
            'bg-gray-50 text-gray-700'
          }`}>
            {trend === 'up' ? <TrendingUp size={16} /> : 
             trend === 'down' ? <TrendingDown size={16} /> : null}
            <span>{trendValue}</span>
          </div>
        )}
      </div>

      {/* Chart Area */}
      <div className="space-y-4">
        {data.map((item, index) => (
          <div key={index} className="group animate-fade-in-up" style={{ animationDelay: `${index * 100}ms` }}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">{item.label}</span>
              <span className="text-sm font-bold text-gray-900">{item.value.toLocaleString()}</span>
            </div>
            <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`absolute inset-y-0 left-0 bg-gradient-to-r ${getBarColor(index)} rounded-full transition-all duration-1000 ease-out shadow-lg`}
                style={{ 
                  width: `${(item.value / maxValue) * 100}%`,
                  transitionDelay: `${index * 100}ms`
                }}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/30 to-white/0 animate-shimmer"></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Actions */}
      <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between">
        <button className="text-sm text-gray-600 hover:text-blue-600 font-medium transition-colors">
          View Details
        </button>
        <button className="flex items-center gap-2 text-sm text-gray-600 hover:text-blue-600 font-medium transition-colors">
          <Download size={14} />
          Export
        </button>
      </div>
    </div>
  );
}
