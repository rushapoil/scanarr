import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Library from './pages/Library'
import MangaDetail from './pages/MangaDetail'
import Calendar from './pages/Calendar'
import Queue from './pages/Queue'
import History from './pages/History'
import Settings from './pages/Settings'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="library" element={<Library />} />
        <Route path="manga/:id" element={<MangaDetail />} />
        <Route path="calendar" element={<Calendar />} />
        <Route path="queue" element={<Queue />} />
        <Route path="history" element={<History />} />
        <Route path="settings/*" element={<Settings />} />
      </Route>
    </Routes>
  )
}
