import { Task } from '../types'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function StressDashboard({ task }: { task: Task }) {
  const metrics = [
    { label: '成功率', value: ((1 - task.error_rate) * 100).toFixed(1) + '%', color: 'text-green-600' },
    { label: '实际 QPS', value: (task.total_count / 60).toFixed(0), color: 'text-blue-600' },
    { label: '平均延迟', value: task.avg_latency_ms.toFixed(0) + 'ms', color: 'text-gray-700' },
    { label: 'P50', value: task.p50_latency_ms.toFixed(0) + 'ms', color: 'text-gray-700' },
    { label: 'P95', value: task.p95_latency_ms.toFixed(0) + 'ms', color: 'text-gray-700' },
    { label: 'P99', value: task.p99_latency_ms.toFixed(0) + 'ms', color: 'text-gray-700' },
  ]

  const latencyData = [
    { name: 'Min', ms: task.min_latency_ms },
    { name: 'P50', ms: task.p50_latency_ms },
    { name: 'Avg', ms: task.avg_latency_ms },
    { name: 'P95', ms: task.p95_latency_ms },
    { name: 'P99', ms: task.p99_latency_ms },
    { name: 'Max', ms: task.max_latency_ms },
  ]

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-6 gap-3">
        {metrics.map(m => (
          <div key={m.label} className="bg-white border rounded-lg p-3 text-center">
            <div className={`text-lg font-bold ${m.color}`}>{m.value}</div>
            <div className="text-xs text-gray-500">{m.label}</div>
          </div>
        ))}
      </div>
      <div className="bg-white border rounded-lg p-4">
        <h4 className="text-sm font-semibold text-gray-600 mb-3">延迟分布</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={latencyData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" tick={{ fontSize: 12 }} /><YAxis tick={{ fontSize: 12 }} /><Tooltip /><Bar dataKey="ms" fill="#3b82f6" /></BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
