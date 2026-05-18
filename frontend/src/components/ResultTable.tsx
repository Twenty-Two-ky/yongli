import { TaskResult } from '../types'

export default function ResultTable({ results }: { results: TaskResult[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-500">
          <tr><th className="text-left p-2">步骤</th><th className="text-left p-2">方法</th><th className="text-left p-2">URL</th><th className="text-left p-2">状态码</th><th className="text-left p-2">耗时</th><th className="text-left p-2">结果</th></tr>
        </thead>
        <tbody>
          {results.map(r => (
            <tr key={r.id} className="border-t">
              <td className="p-2 text-gray-400">{r.step_index ?? '-'}</td>
              <td className="p-2 font-mono text-xs">{r.method}</td>
              <td className="p-2 text-xs truncate max-w-xs">{r.url}</td>
              <td className="p-2"><span className={`text-xs px-1.5 py-0.5 rounded ${r.status_code && r.status_code < 400 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>{r.status_code ?? 'ERR'}</span></td>
              <td className="p-2 text-xs">{r.latency_ms ? r.latency_ms + 'ms' : '-'}</td>
              <td className="p-2">{r.is_success ? <span className="text-green-600">✓</span> : <span className="text-red-600">✗</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
