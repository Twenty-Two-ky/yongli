import { useState } from 'react'
import { Task } from '../types'
import { api } from '../api'

export default function TaskCompare({ currentTask }: { currentTask: Task }) {
  const [compareId, setCompareId] = useState('')
  const [other, setOther] = useState<Task | null>(null)
  const [error, setError] = useState('')

  const loadCompare = async () => {
    if (!compareId) return
    try { const t = await api.getTask(Number(compareId)); setOther(t); setError('') } catch { setError('任务未找到') }
  }

  return (
    <div className="border-t pt-4 mt-4">
      <h4 className="text-sm font-semibold text-gray-700 mb-3">跨环境对比</h4>
      <div className="flex gap-2 mb-3">
        <input value={compareId} onChange={e => setCompareId(e.target.value)} placeholder="输入对比任务 ID" className="border rounded p-1 text-sm w-36" />
        <button onClick={loadCompare} className="text-sm bg-gray-100 px-3 py-1 rounded hover:bg-gray-200">对比</button>
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
      {other && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded p-3">
            <div className="text-xs text-gray-500 mb-1">当前任务 #{currentTask.id} ({currentTask.environment?.name})</div>
            <div className="text-sm">成功率: {((1 - currentTask.error_rate) * 100).toFixed(1)}%</div>
            <div className="text-sm">平均延迟: {currentTask.avg_latency_ms.toFixed(0)}ms</div>
            <div className="text-sm">AI 分析: {currentTask.ai_analysis?.summary || '-'}</div>
          </div>
          <div className="bg-green-50 rounded p-3">
            <div className="text-xs text-gray-500 mb-1">对比任务 #{other.id} ({other.environment?.name})</div>
            <div className="text-sm">成功率: {((1 - other.error_rate) * 100).toFixed(1)}%</div>
            <div className="text-sm">平均延迟: {other.avg_latency_ms.toFixed(0)}ms</div>
            <div className="text-sm">AI 分析: {other.ai_analysis?.summary || '-'}</div>
          </div>
        </div>
      )}
    </div>
  )
}
