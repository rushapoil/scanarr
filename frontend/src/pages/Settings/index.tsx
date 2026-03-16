import { NavLink, Routes, Route, Navigate } from 'react-router-dom'
import { clsx } from 'clsx'
import ProwlarrSettings from './Prowlarr'
import DownloadClientsSettings from './DownloadClients'
import QualityProfilesSettings from './QualityProfiles'
import NotificationsSettings from './Notifications'
import GeneralSettings from './General'

const TABS = [
  { to: 'general',          label: 'General' },
  { to: 'prowlarr',         label: 'Prowlarr' },
  { to: 'downloadclients',  label: 'Download Clients' },
  { to: 'qualityprofiles',  label: 'Quality Profiles' },
  { to: 'notifications',    label: 'Notifications' },
]

export default function Settings() {
  return (
    <div className="space-y-4">
      {/* Tab bar */}
      <div className="flex gap-0.5 border-b border-surface-border">
        {TABS.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
                isActive
                  ? 'border-brand-500 text-brand-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200',
              )
            }
          >
            {label}
          </NavLink>
        ))}
      </div>

      <Routes>
        <Route index element={<Navigate to="general" replace />} />
        <Route path="general"         element={<GeneralSettings />} />
        <Route path="prowlarr"        element={<ProwlarrSettings />} />
        <Route path="downloadclients" element={<DownloadClientsSettings />} />
        <Route path="qualityprofiles" element={<QualityProfilesSettings />} />
        <Route path="notifications"   element={<NotificationsSettings />} />
      </Routes>
    </div>
  )
}
