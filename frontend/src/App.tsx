import { Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import TaskCreator from './pages/TaskCreator'
import TaskHistory from './pages/TaskHistory'
import TaskDetail from './pages/TaskDetail'
import { Activity, Play, List } from 'lucide-react'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 flex items-center h-14 gap-6">
          <h1 className="text-lg font-bold text-gray-800">API 自动化测试平台</h1>
          <NavLink to="/" className={({isActive}) => `flex items-center gap-1 text-sm ${isActive ? 'text-blue-600 font-semibold' : 'text-gray-600 hover:text-gray-900'}`}><Activity size={16} />总览</NavLink>
          <NavLink to="/create" className={({isActive}) => `flex items-center gap-1 text-sm ${isActive ? 'text-blue-600 font-semibold' : 'text-gray-600 hover:text-gray-900'}`}><Play size={16} />创建任务</NavLink>
          <NavLink to="/history" className={({isActive}) => `flex items-center gap-1 text-sm ${isActive ? 'text-blue-600 font-semibold' : 'text-gray-600 hover:text-gray-900'}`}><List size={16} />任务历史</NavLink>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/create" element={<TaskCreator />} />
          <Route path="/history" element={<TaskHistory />} />
          <Route path="/tasks/:id" element={<TaskDetail />} />
        </Routes>
      </main>
    </div>
  )
}
