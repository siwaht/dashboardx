import React from 'react';
import { ChartCard } from './ChartCard';
import { StatCard } from './StatCard';
import { InsightCard } from './InsightCard';
import { DollarSign, Users, TrendingUp, FileText } from 'lucide-react';

/**
 * Demo component showcasing various data visualizations
 * This demonstrates how AI responses can include interactive charts, stats, and insights
 */
export function VisualizationDemo() {
  // Sample data for charts
  const salesData = [
    { label: 'Q1 2024', value: 45000 },
    { label: 'Q2 2024', value: 52000 },
    { label: 'Q3 2024', value: 61000 },
    { label: 'Q4 2024', value: 58000 },
  ];

  const regionData = [
    { label: 'North America', value: 125000 },
    { label: 'Europe', value: 98000 },
    { label: 'Asia Pacific', value: 87000 },
    { label: 'Latin America', value: 45000 },
  ];

  // Sample sparkline data
  const sparklineData = [45, 52, 48, 61, 58, 65, 70];

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
          Sales Analysis Report
        </h2>
        <p className="text-gray-600">
          Here's a comprehensive analysis of your sales data based on the uploaded documents
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Revenue"
          value="$216K"
          change={12.5}
          changeLabel="vs last quarter"
          icon={<DollarSign size={24} className="text-white" />}
          color="blue"
          sparklineData={sparklineData}
        />
        <StatCard
          title="Active Customers"
          value="1,284"
          change={8.2}
          changeLabel="vs last month"
          icon={<Users size={24} className="text-white" />}
          color="purple"
          sparklineData={[120, 135, 128, 142, 138, 145, 150]}
        />
        <StatCard
          title="Growth Rate"
          value="23.4%"
          change={5.1}
          changeLabel="vs last year"
          icon={<TrendingUp size={24} className="text-white" />}
          color="green"
          sparklineData={[15, 18, 20, 19, 22, 21, 23]}
        />
        <StatCard
          title="Documents Analyzed"
          value="47"
          change={0}
          changeLabel="in this session"
          icon={<FileText size={24} className="text-white" />}
          color="orange"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ChartCard
          title="Quarterly Sales Performance"
          description="Revenue trends across quarters"
          data={salesData}
          type="bar"
          trend="up"
          trendValue="+15.2%"
        />
        <ChartCard
          title="Sales by Region"
          description="Geographic distribution of revenue"
          data={regionData}
          type="bar"
          trend="up"
          trendValue="+8.7%"
        />
      </div>

      {/* Insights */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-gray-900">AI-Generated Insights</h3>
        
        <InsightCard
          title="Strong Q3 Performance"
          content="The third quarter showed exceptional growth with a 17% increase compared to Q2. This surge can be attributed to the successful product launch in August and expanded market presence in the Asia Pacific region. The momentum continued into early Q4, though there was a slight seasonal dip in December."
          confidence={0.92}
          sources={['Q3_Sales_Report.pdf', 'Product_Launch_Analysis.xlsx', 'Regional_Performance.docx']}
          category="insight"
        />

        <InsightCard
          title="Recommendation: Focus on North America"
          content="North America represents 35% of total revenue and shows the highest growth potential. Consider allocating additional marketing budget to this region for Q1 2025. Historical data suggests a 20-25% ROI on marketing investments in this market."
          confidence={0.87}
          sources={['Market_Analysis_2024.pdf', 'Budget_Allocation.xlsx']}
          category="recommendation"
        />

        <InsightCard
          title="Customer Retention Improving"
          content="Customer retention rate has increased from 78% to 85% over the past six months. The implementation of the new customer success program and improved onboarding process are showing positive results."
          confidence={0.94}
          sources={['Customer_Metrics_Dashboard.pdf', 'Retention_Analysis.xlsx']}
          category="info"
        />
      </div>

      {/* Action Items */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200">
        <h3 className="text-lg font-bold text-gray-900 mb-4">Suggested Next Steps</h3>
        <ul className="space-y-3">
          {[
            'Review Q4 performance in detail to understand the December dip',
            'Prepare Q1 2025 marketing budget with focus on North America',
            'Schedule customer success team review meeting',
            'Analyze competitor activity in Asia Pacific region',
          ].map((item, index) => (
            <li key={index} className="flex items-start gap-3 group">
              <div className="flex-shrink-0 w-6 h-6 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center text-white text-xs font-bold group-hover:scale-110 transition-transform">
                {index + 1}
              </div>
              <span className="text-gray-700 group-hover:text-gray-900 transition-colors">
                {item}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
