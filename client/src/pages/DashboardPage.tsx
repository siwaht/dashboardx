import { SalesChart } from '@/components/charts/SalesChart';
import { TrafficChart } from '@/components/charts/TrafficChart';

const metricData = [
  { title: 'Total Revenue', value: '$45,231.89', change: '+20.1% from last month' },
  { title: 'Subscriptions', value: '+2350', change: '+180.1% from last month' },
  { title: 'Sales', value: '+12,234', change: '+19% from last month' },
  { title: 'Active Now', value: '+573', change: '+201 since last hour' },
];

export function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Dashboard</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metricData.map((metric) => (
          <div key={metric.title} className="bg-[#161b22] border border-[#30363d] rounded-lg p-6">
            <h3 className="text-gray-400 text-sm font-medium">{metric.title}</h3>
            <p className="text-2xl font-bold mt-1">{metric.value}</p>
            <p className="text-xs text-gray-500 mt-2">{metric.change}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <SalesChart />
        <TrafficChart />
      </div>
    </div>
  );
}
