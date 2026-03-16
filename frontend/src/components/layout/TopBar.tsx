import { useLocation } from 'react-router-dom'
import { Bell, RefreshCw } from 'lucide-react'
import { useQueryClient } from '@tanstack/react-query'

const TITLES: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/library': 'Library',
  '/calendar': 'Calendar',
  '/queue': 'Queue',
  '/history': 'History',
  '/settings': 'Settings',
}

export default function TopBar() {
  const location = useLocation()
  const queryClient = useQueryClient()

  const title =
    Object.entries(TITLES).find(([path]) => location.pathname.startsWith(path))?.[1] ||
    'Scanarr'

  return (
    <header className="h-14 flex items-center justify-between px-6 border-b border-surface-border bg-surface-card flex-shrink-0">
      <h1 className="text-lg font-semibold text-gray-100">{title}</h1>

      <div className="flex items-center gap-2">
        <button
          onClick={() => queryClient.invalidateQueries()}
          className="p-2 rounded-md text-gray-400 hover:text-gray-200 hover:bg-surface-hover transition-colors"
          title="Refresh"
        >
          <RefreshCw size={16} />
        </button>
        <button className="p-2 rounded-md text-gray-400 hover:text-gray-200 hover:bg-surface-hover transition-colors">
          <Bell size={16} />
        </button>
      </div>
    </header>
  )
}
