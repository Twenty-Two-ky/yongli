import { Worker } from '../types'
import { Circle } from 'lucide-react'

export default function WorkerCard({ worker }: { worker: Worker }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-3 shadow-sm">
      <div className="flex items-center gap-2">
        <Circle size={10} fill={worker.status === 'online' ? '#22c55e' : '#ef4444'} stroke={worker.status === 'online' ? '#22c55e' : '#ef4444'} />
        <span className="font-semibold text-sm text-gray-800">{worker.name}</span>
        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{worker.status === 'online' ? '在线' : '离线'}</span>
        {worker.current_task_id && <span className="text-xs text-blue-600">执行中: #{worker.current_task_id}</span>}
      </div>
    </div>
  )
}
