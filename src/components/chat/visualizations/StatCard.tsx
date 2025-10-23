import React from 'react';
import { TrendingUp, TrendingDown, Minus, Sparkles } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'purple' | 'green' | 'orange' | 'red';
  sparklineData?: number[];
}

export function StatCard({ 
  title, 
  value, 
  change, 
  changeLabel = 'vs last period',
  icon,
  color = 'blue',
  sparklineData 
}: StatCardProps) {
  const colorClasses = {
    blue: {
      gradient: 'from-blue-500 to-cyan-500',
      bg: 'bg-blue-50',
      text: 'text-blue-700',
      shadow: 'shadow-blue-500/30',
    },
    purple: {
      gradient: 'from-purple-500 to-pink-500',
      bg: 'bg-purple-50',
      text: 'text-purple-700',
      shadow: 'shadow-purple-500/30',
    },
    green: {
      gradient: 'from-emerald-500 to-green-500',
      bg: 'bg-green-50',
      text: 'text-green-700',
      shadow: 'shadow-green-500/30',
    },
    orange: {
      gradient: 'from-amber-500 to-orange-500',
      bg: 'bg-orange-50',
      text: 'text-orange-700',
      shadow: 'shadow-orange-500/30',
    },
    red: {
      gradient: 'from-red-500 to-rose-500',
      bg: 'bg-red-50',
      text: 'text-red-700',
      shadow: 'shadow-red-500/30',
    },
  };

  const colors = colorClasses[color];
  const isPositive = change !== undefined && change > 0;
  const isNegative = change !== undefined && change < 0;
  const isNeutral = change !== undefined && change === 0;

  return (
    <div className="group bg-white rounded-2xl p-6 shadow-lg border border-gray-100 hover:shadow-xl transition-all duration-300 animate-scale-in hover:-translate-y-1">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{title}</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-bold text-gray-900 animate-fade-in">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </h3>
          </div>
        </div>
        
        {/* Icon */}
        <div className={`w-12 h-12 bg-gradient-to-br ${colors.gradient} rounded-xl flex items-center justify-center shadow-lg ${colors.shadow} group-hover:scale-110 transition-transform duration-300`}>
          {icon || <Sparkles size={24} className="text-white" />}
        </div>
      </div>

      {/* Change Indicator */}
      {change !== undefined && (
        <div className="flex items-center gap-2 mb-3">
          <div className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold ${
            isPositive ? 'bg-green-50 text-green-700' :
            isNegative ? 'bg-red-50 text-red-700' :
            'bg-gray-50 text-gray-700'
          }`}>
            {isPositive && <TrendingUp size={14} />}
            {isNegative && <TrendingDown size={14} />}
            {isNeutral && <Minus size={14} />}
            <span>{Math.abs(change)}%</span>
          </div>
          <span className="text-xs text-gray-500">{changeLabel}</span>
        </div>
      )}

      {/* Sparkline */}
      {sparklineData && sparklineData.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-end gap-1 h-12">
            {sparklineData.map((value, index) => {
              const maxValue = Math.max(...sparklineData);
              const height = (value / maxValue) * 100;
              return (
                <div
                  key={index}
                  className="flex-1 relative group/bar"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <div
                    className={`w-full bg-gradient-to-t ${colors.gradient} rounded-t transition-all duration-500 hover:opacity-80`}
                    style={{ height: `${height}%` }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-white/0 via-white/20 to-white/40 opacity-0 group-hover/bar:opacity-100 transition-opacity"></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
