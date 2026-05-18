import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { Environment } from '../types'
import { Play, Zap } from 'lucide-react'

const EXAMPLES = [
  { label: '单接口验证', text: '测试登录接口 /api/v1/login，使用账号 admin/123456，校验返回码是否为 200' },
  { label: '异常输入', text: '对搜索接口 /api/v1/search 的 keyword 参数分别传入空值、超长字符串、特殊字符等异常输入，观察接口返回是否符合预期' },
  { label: '并发压测', text: '对查询接口 /api/v1/search 模拟高并发流量，每秒发送 100 个请求，持续 1 分钟，统计成功率与平均响应时间' },
]

export default function TaskCreator() {
  const [text, setText] = useState('')
  const [envs, setEnvs] = useState<Environment[]>([])
  const [envId, setEnvId] = useState<number | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => { api.getEnvironments().then(setEnvs).catch(console.error) }, [])

  const allOffline = envs.length > 0 && envs.every(e => e.status !== 'online')

  const handleSubmit = async () => {
    if (!text.trim()) return
    setSubmitting(true); setError('')
    try {
      const task = await api.createTask({ natural_language: text, environment_id: envId || undefined })
      navigate('/tasks/' + task.id)
    } catch (err: any) {
      setError(err.message || '创建失败')
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h2 className="text-lg font-semibold text-gray-800">创建测试任务</h2>
      <div>
        <label className="text-sm text-gray-600 mb-2 block">选择环境</label>
        <select value={envId || ''} onChange={e => setEnvId(e.target.value ? Number(e.target.value) : null)} className="w-full border border-gray-300 rounded-lg p-2 text-sm">
          <option value="">🤖 AI 自动选择（推荐）</option>
          {envs.map(e => <option key={e.id} value={e.id} disabled={e.status !== 'online'}>{e.status === 'online' ? '●' : '○'} {e.name} ({e.base_url})</option>)}
        </select>
      </div>
      <div>
        <label className="text-sm text-gray-600 mb-2 block">自然语言指令</label>
        <textarea value={text} onChange={e => setText(e.target.value)} rows={4} placeholder="用自然语言描述你要测试什么..." className="w-full border border-gray-300 rounded-lg p-3 text-sm resize-none" disabled={submitting || allOffline} />
        {allOffline && <p className="text-sm text-red-500 mt-1">所有环境离线，无法创建任务</p>}
      </div>
      {error && <div className="text-sm text-red-600 bg-red-50 p-2 rounded">{error}</div>}
      <button onClick={handleSubmit} disabled={submitting || !text.trim() || allOffline} className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
        <Play size={16} /> {submitting ? '创建中...' : '执行任务'}
      </button>
      <div>
        <h3 className="text-sm font-semibold text-gray-500 mb-3">快速示例</h3>
        <div className="grid grid-cols-3 gap-3">
          {EXAMPLES.map(ex => (
            <div key={ex.label} className="bg-white border border-gray-200 rounded-lg p-3 cursor-pointer hover:border-blue-300 hover:shadow-sm transition" onClick={() => setText(ex.text)}>
              <div className="flex items-center gap-2 mb-1"><Zap size={14} className="text-amber-500" /><span className="text-sm font-semibold text-gray-700">{ex.label}</span></div>
              <p className="text-xs text-gray-500 line-clamp-3">{ex.text}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
