import { ScatterChart as RechartsScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

interface ScatterChartProps {
  data: Array<{
    x: number
    y: number
    size?: number
    name?: string
    [key: string]: any
  }>
  xLabel?: string
  yLabel?: string
  height?: number
}

export default function ScatterChart({ data, xLabel, yLabel, height = 400 }: ScatterChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsScatterChart
        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" className="stroke-gray-300 dark:stroke-gray-600" />
        <XAxis 
          type="number" 
          dataKey="x" 
          name={xLabel}
          label={{ value: xLabel, position: 'insideBottom', offset: -5 }}
          className="text-gray-600 dark:text-gray-400"
        />
        <YAxis 
          type="number" 
          dataKey="y" 
          name={yLabel}
          label={{ value: yLabel, angle: -90, position: 'insideLeft' }}
          className="text-gray-600 dark:text-gray-400"
        />
        <Tooltip 
          cursor={{ strokeDasharray: '3 3' }}
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
          }}
        />
        <Scatter 
          name="Clientes" 
          data={data} 
          fill="#3b82f6"
        />
      </RechartsScatterChart>
    </ResponsiveContainer>
  )
}
