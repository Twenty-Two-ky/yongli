import { Environment } from '../types'
import { Circle, Wifi, Edit2, Trash2 } from 'lucide-react'

export default function EnvironmentCard({ env, onCheck, onEdit, onDelete }: {
  env: Environment; onCheck: (id: number) => void; onEdit: (env: Environment) => void; onDelete: (id: number) => void;
}) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Circle size={10} fill={env.status === 'online' ? '#22c55e' : '#9ca3af'} stroke={env.status === 'online' ? '#22c55e' : '#9ca3af'} />
          <span className="font-semibold text-gray-800">{env.name}</span>
        </div>
        <div className="flex gap-1">
          <button onClick={() => onCheck(env.id)} className="p-1 hover:bg-gray-100 rounded" title="健康检查"><Wifi size={14} /></button>
          <button onClick={() => onEdit(env)} className="p-1 hover:bg-gray-100 rounded" title="编辑"><Edit2 size={14} /></button>
          <button onClick={() => onDelete(env.id)} className="p-1 hover:bg-red-50 rounded text-red-400" title="删除"><Trash2 size={14} /></button>
        </div>
      </div>
      <div className="text-sm text-gray-500 space-y-1">
        <div>{env.base_url}</div>
        <div className="text-xs text-gray-400">health: {env.health_check_path}</div>
      </div>
    </div>
  )
}
