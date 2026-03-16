import { NavLink } from 'react-router-dom'
import {
  BookOpen,
  Calendar,
  Clock,
  Download,
  LayoutDashboard,
  Settings,
} from 'lucide-react'
import { clsx } from 'clsx'

const NAV = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/library',   icon: BookOpen,        label: 'Library' },
  { to: '/calendar',  icon: Calendar,        label: 'Calendar' },
  { to: '/queue',     icon: Download,        label: 'Queue' },
  { to: '/history',   icon: Clock,           label: 'History' },
  { to: '/settings',  icon: Settings,        label: 'Settings' },
]

export default function Sidebar() {
  return (
    <aside className="w-56 flex-shrink-0 bg-surface-card border-r border-surface-border flex flex-col">
      {/* Logo */}
      <div className="h-14 flex items-center px-5 border-b border-surface-border">
        <span className="text-brand-400 font-bold text-lg tracking-tight">
          ⛩ Scanarr
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-0.5 px-2">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-600/20 text-brand-400'
                  : 'text-gray-400 hover:bg-surface-hover hover:text-gray-200',
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Version */}
      <div className="px-4 py-3 border-t border-surface-border">
        <p className="text-xs text-gray-600">v0.1.0</p>
      </div>
    </aside>
  )
}
