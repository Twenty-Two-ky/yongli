import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Task, TaskResult } from '../types'
import { StatusBadge, formatTime } from './Dashboard'
import TaskTimeline from '../components/TaskTimeline'
import ResultTable from '../components/ResultTable'
import StressDashboard from '../components/StressDashboard'
import AiAnalysis from '../components/AiAnalysis'
import TaskCompare from '../components/TaskCompare'
import { Play, RefreshCw, AlertCircle } from 'lucide-react'

export default function TaskDetail() {
  const { id } = useParams<{ id: string }>()
  const [task, setTask] = useState<Task | null>(null)
  const [results, setResults] = useState<TaskResult[]>([])
  const [sseError, setSseError] = useState(false)
  const [showRerunModal, setShowRerunModal] = useState(false)
  const [rerunEnvId, setRerunEnvId] = useState(0)
  const eventSourceRef = useRef<EventSource | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!id) return
    const es = api.taskStream(Number(id))
    es.onmessage = (e) => {
      try { const t = JSON.parse(e.data); setTask(t) } catch {}
      setSseError(false)
    }
    es.onerror = () => setSseError(true)
    eventSourceRef.current = es
    // Also load results
    api.getTaskResults(Number(id)).then(r => setResults(r.items)).catch(() => {})
    return () => { es.close() }
  }, [id])

  const handleRerun = async () => {
    if (!task) return
    try { const newTask = await api.rerunTask(task.id, rerunEnvId); navigate('/tasks/' + newTask.id) } catch {}
    setShowRerunModal(false)
  }

  if (!task) return <div className="text-center text-gray-400 py-12">加载中...</div>

  return (
    <div className="space-y-6">
      {sseError && <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 p-2 rounded"><AlertCircle size={14} />连接断开，重连中...</div>}

      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">任务 #{task.id} 详情</h2>
          <p className="text-sm text-gray-500 mt-1">{task.natural_language}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => { setRerunEnvId(0); setShowRerunModal(true) }} className="flex items-center gap-1 text-sm bg-gray-100 px-3 py-1.5 rounded hover:bg-gray-200"><RefreshCw size={14} />重跑</button>
          <button onClick={() => { setShowRerunModal(true) }} className="flex items-center gap-1 text-sm bg-blue-100 text-blue-700 px-3 py-1.5 rounded hover:bg-blue-200"><Play size={14} />跨环境重跑</button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="text-xs text-gray-500 mb-1">环境</div>
          <div className="text-sm font-semibold">{task.environment?.name || '-'} ({task.environment?.base_url})</div>
        </div>
        <div className="bg-white rounded-lg border p-4">
          <div className="text-xs text-gray-500 mb-1">状态</div>
          <StatusBadge status={task.status} />
        </div>
      </div>

      {task.status === 'error' && task.ai_analysis?.summary && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-700">{task.ai_analysis.summary}</p>
        </div>
      )}

      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">执行时间线</h3>
        <TaskTimeline events={task.timeline} />
      </div>

      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">执行结果</h3>
        {task.task_type === 'stress' ? (
          <StressDashboard task={task} />
        ) : (
          results.length > 0 ? <ResultTable results={results} /> : <p className="text-sm text-gray-400">暂无结果数据</p>
        )}
      </div>

      <div className="bg-white rounded-lg border p-4">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">AI 分析</h3>
        <AiAnalysis analysis={task.ai_analysis} />
      </div>

      <TaskCompare currentTask={task} />

      {showRerunModal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 shadow-xl">
            <h3 className="text-lg font-semibold mb-4">跨环境重跑</h3>
            <p className="text-sm text-gray-500 mb-3">选择目标环境（复用已解析的动作，不重新调用 LLM）</p>
            <select value={rerunEnvId || task.environment_id} onChange={e => setRerunEnvId(Number(e.target.value))} className="w-full border rounded p-2 text-sm mb-4">
              <option value={task.environment_id}>{task.environment?.name} (当前)</option>
              {/* load other envs dynamically — simplified */}
            </select>
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowRerunModal(false)} className="px-4 py-2 text-sm border rounded">取消</button>
              <button onClick={handleRerun} className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700">确认重跑</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
