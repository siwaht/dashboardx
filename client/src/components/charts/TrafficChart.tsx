import { VictoryPie } from 'victory';
import { ResponsiveContainer } from 'recharts';

const trafficData = [
  { x: 'Search', y: 40 },
  { x: 'Direct', y: 30 },
  { x: 'Social', y: 20 },
  { x: 'Referral', y: 10 },
];

export function TrafficChart() {
  return (
    <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-6 h-96">
      <h2 className="text-xl font-semibold mb-4">Traffic Sources</h2>
      <ResponsiveContainer width="100%" height="100%">
        <VictoryPie
          data={trafficData}
          colorScale={['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b']}
          style={{
            labels: { fill: 'white', fontSize: 14 },
          }}
        />
      </ResponsiveContainer>
    </div>
  );
}
