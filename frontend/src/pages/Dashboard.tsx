import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Environment, Worker, Task, StatsSummary } from '../types'
import EnvironmentCard from '../components/EnvironmentCard'
import WorkerCard from '../components/WorkerCard'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Plus, AlertTriangle } from 'lucide-react'

export default function Dashboard() {
  const [envs, setEnvs] = useState<Environment[]>([])
  const [workers, setWorkers] = useState<Worker[]>([])
  const [recentTasks, setRecentTasks] = useState<Task[]>([])
  const [stats, setStats] = useState<StatsSummary | null>(null)
  const [chartData, setChartData] = useState<any[]>([])
  const navigate = useNavigate()

  const load = async () => {
    try {
      const [e, w, t, s] = await Promise.all([api.getEnvironments(), api.getWorkers(), api.getTasks({ page_size: '5' }), api.getStats()])
      setEnvs(e); setWorkers(w); setRecentTasks(t.items); setStats(s);
    } catch (err) { console.error(err) }
  }

  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t) }, [])

  const handleCheck = async (id: number) => { await api.checkEnvironment(id); load() }
  const handleEdit = (env: Environment) => { /* inline edit or modal — simplified */ }
  const handleDelete = async (id: number) => { if (confirm('确认删除此环境？')) { await api.deleteEnvironment(id); load() } }

  const allWorkersOffline = workers.length > 0 && workers.every(w => w.status !== 'online')

  return (
    <div className="space-y-6">
      {allWorkersOffline && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2 text-amber-700 text-sm">
          <AlertTriangle size={16} /> 当前无可用 Worker，新任务将进入队列等待
        </div>
      )}

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-gray-700">环境</h2>
          <button onClick={() => {/* open create modal */}} className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800"><Plus size={14} />添加环境</button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          {envs.map(e => <EnvironmentCard key={e.id} env={e} onCheck={handleCheck} onEdit={handleEdit} onDelete={handleDelete} />)}
        </div>
      </section>

      <section>
        <h2 className="text-base font-semibold text-gray-700 mb-3">Worker 节点</h2>
        <div className="grid grid-cols-3 gap-3">
          {workers.map(w => <WorkerCard key={w.id} worker={w} />)}
        </div>
      </section>

      {stats && (
        <section>
          <h2 className="text-base font-semibold text-gray-700 mb-3">全局统计</h2>
          <div className="grid grid-cols-4 gap-3">
            <div className="bg-white rounded-lg border p-3 text-center"><div className="text-2xl font-bold text-blue-600">{stats.today_tasks}</div><div className="text-xs text-gray-500 mt-1">今日任务</div></div>
            <div className="bg-white rounded-lg border p-3 text-center"><div className="text-2xl font-bold text-green-600">{(stats.overall_success_rate * 100).toFixed(1)}%</div><div className="text-xs text-gray-500 mt-1">成功率</div></div>
            <div className="bg-white rounded-lg border p-3 text-center"><div className="text-2xl font-bold text-gray-700">{stats.avg_latency_ms.toFixed(0)}ms</div><div className="text-xs text-gray-500 mt-1">平均延迟</div></div>
            <div className="bg-white rounded-lg border p-3 text-center"><div className="text-2xl font-bold text-red-500">{stats.failed_tasks}</div><div className="text-xs text-gray-500 mt-1">失败任务</div></div>
          </div>
        </section>
      )}

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-gray-700">最近任务</h2>
          <button onClick={() => navigate('/history')} className="text-sm text-blue-600 hover:text-blue-800">查看全部 →</button>
        </div>
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-500">
              <tr><th className="text-left p-3 w-12">#</th><th className="text-left p-3">指令</th><th className="text-left p-3 w-20">类型</th><th className="text-left p-3 w-20">状态</th><th className="text-left p-3 w-24">时间</th></tr>
            </thead>
            <tbody>
              {recentTasks.map(t => (
                <tr key={t.id} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => navigate('/tasks/' + t.id)}>
                  <td className="p-3 text-gray-400">{t.id}</td>
                  <td className="p-3 truncate max-w-xs">{t.natural_language}</td>
                  <td className="p-3"><span className="text-xs px-2 py-0.5 rounded bg-gray-100">{t.task_type || '-'}</span></td>
                  <td className="p-3"><StatusBadge status={t.status} /></td>
                  <td className="p-3 text-gray-400 text-xs">{formatTime(t.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = { parsing: 'bg-yellow-100 text-yellow-700', queued: 'bg-blue-100 text-blue-700', running: 'bg-purple-100 text-purple-700', completed: 'bg-green-100 text-green-700', error: 'bg-red-100 text-red-700', cancelled: 'bg-gray-100 text-gray-500' }
  const labels: Record<string, string> = { parsing: '解析中', queued: '排队中', running: '执行中', completed: '已完成', error: '异常', cancelled: '已取消' }
  return <span className={`text-xs px-2 py-0.5 rounded-full ${colors[status] || ''}`}>{labels[status] || status}</span>
}

function formatTime(ts: string) { const d = new Date(ts); return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }
export { StatusBadge, formatTime }
