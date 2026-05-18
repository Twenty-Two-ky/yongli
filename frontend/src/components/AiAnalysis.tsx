export default function AiAnalysis({ analysis }: { analysis: any }) {
  if (!analysis) return <div className="text-sm text-gray-400">任务完成后自动生成分析...</div>
  const cats = analysis.failure_categories || []
  return (
    <div className="space-y-3">
      <div className="text-sm font-semibold text-gray-700">分析摘要</div>
      <p className="text-sm text-gray-600">{analysis.summary}</p>
      {cats.length > 0 && (
        <div className="space-y-2">
          {cats.map((c: any, i: number) => (
            <div key={i} className="bg-gray-50 rounded p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-semibold text-gray-700">{c.category}</span>
                <span className="text-xs bg-gray-200 px-2 py-0.5 rounded-full">{c.count} 条</span>
              </div>
              {c.sample_errors?.slice(0, 3).map((err: string, j: number) => (
                <div key={j} className="text-xs text-red-600 font-mono mt-1">{err}</div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
