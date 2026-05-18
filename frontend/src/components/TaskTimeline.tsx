import { TimelineEvent } from '../types'
import { Circle, CheckCircle2, Clock, AlertCircle } from 'lucide-react'

export default function TaskTimeline({ events }: { events: TimelineEvent[] }) {
  const icons: Record<string, any> = { created: Clock, parsed: CheckCircle2, started: Circle, completed: CheckCircle2 }
  return (
    <div className="space-y-2">
      {events.map((e, i) => {
        const Icon = icons[e.event] || Circle
        return (
          <div key={i} className="flex items-center gap-3 text-sm">
            <Icon size={14} className="text-gray-400" />
            <span className="text-gray-600 capitalize">{e.event}</span>
            <span className="text-gray-400 text-xs">{new Date(e.time + 'Z').toLocaleTimeString('zh-CN', { hour12: false })}</span>
          </div>
        )
      })}
    </div>
  )
}
