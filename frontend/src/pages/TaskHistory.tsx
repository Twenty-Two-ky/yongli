import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Task, Environment } from '../types'
import { StatusBadge, formatTime } from './Dashboard'
import { Search } from 'lucide-react'

export default function TaskHistory() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [filters, setFilters] = useState({ status: '', task_type: '', env_id: '', search: '' })
  const [envs, setEnvs] = useState<Environment[]>([])
  const navigate = useNavigate()

  const load = async () => {
    const params: Record<string, string> = { page: String(page), page_size: '20' }
    if (filters.status) params.status = filters.status
    if (filters.task_type) params.task_type = filters.task_type
    if (filters.env_id) params.env_id = filters.env_id
    if (filters.search) params.search = filters.search
    const r = await api.getTasks(params)
    setTasks(r.items); setTotal(r.total)
  }

  useEffect(() => { api.getEnvironments().then(setEnvs) }, [])
  useEffect(() => { load() }, [page, filters])

  const filterChanged = (key: string, val: string) => { setFilters(f => ({ ...f, [key]: val })); setPage(1) }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-800">任务历史</h2>
      <div className="flex gap-3 flex-wrap">
        <select value={filters.status} onChange={e => filterChanged('status', e.target.value)} className="border border-gray-300 rounded p-2 text-sm">
          <option value="">全部状态</option>
          {['parsing','queued','running','completed','error','cancelled'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select value={filters.task_type} onChange={e => filterChanged('task_type', e.target.value)} className="border border-gray-300 rounded p-2 text-sm">
          <option value="">全部类型</option>
          <option value="single">单接口</option><option value="abnormal">异常输入</option><option value="stress">压测</option>
        </select>
        <select value={filters.env_id} onChange={e => filterChanged('env_id', e.target.value)} className="border border-gray-300 rounded p-2 text-sm">
          <option value="">全部环境</option>
          {envs.map(e => <option key={e.id} value={String(e.id)}>{e.name}</option>)}
        </select>
        <div className="relative">
          <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-gray-400" />
          <input placeholder="搜索指令..." value={filters.search} onChange={e => filterChanged('search', e.target.value)} className="border border-gray-300 rounded p-2 pl-7 text-sm" />
        </div>
      </div>
      <div className="bg-white rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-500">
            <tr><th className="text-left p-3 w-12">#</th><th className="text-left p-3">指令</th><th className="text-left p-3 w-20">类型</th><th className="text-left p-3 w-20">状态</th><th className="text-left p-3 w-24">时间</th></tr>
          </thead>
          <tbody>
            {tasks.map(t => (
              <tr key={t.id} className="border-t hover:bg-gray-50 cursor-pointer" onClick={() => navigate('/tasks/' + t.id)}>
                <td className="p-3 text-gray-400">{t.id}</td>
                <td className="p-3 truncate max-w-md">{t.natural_language}</td>
                <td className="p-3"><span className="text-xs px-2 py-0.5 rounded bg-gray-100">{t.task_type || '-'}</span></td>
                <td className="p-3"><StatusBadge status={t.status} /></td>
                <td className="p-3 text-gray-400 text-xs">{formatTime(t.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > 20 && (
        <div className="flex items-center justify-center gap-2">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-30">上一页</button>
          <span className="text-sm text-gray-500">{page} / {Math.ceil(total / 20)}</span>
          <button disabled={page * 20 >= total} onClick={() => setPage(p => p + 1)} className="px-3 py-1 border rounded text-sm disabled:opacity-30">下一页</button>
        </div>
      )}
    </div>
  )
}
