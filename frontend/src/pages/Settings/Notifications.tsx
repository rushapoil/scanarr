import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Bell, Plus, Trash2 } from 'lucide-react'
import { settingsApi } from '../../api/settings'
import Spinner from '../../components/common/Spinner'
import Badge from '../../components/common/Badge'
import EmptyState from '../../components/common/EmptyState'

export default function NotificationsSettings() {
  const qc = useQueryClient()
  const { data: notifs = [], isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: settingsApi.listNotifications,
  })

  const remove = useMutation({
    mutationFn: (id: number) => settingsApi.deleteNotification(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
  })

  if (isLoading) return <Spinner />

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-gray-200">Notifications</h3>
        <button className="btn-primary text-sm" disabled>
          <Plus size={14} /> Add — coming soon
        </button>
      </div>

      {notifs.length === 0 ? (
        <EmptyState icon={Bell} title="No notifications configured" description="Add Discord, Telegram, or webhook notifications" />
      ) : (
        <div className="space-y-2">
          {notifs.map((n) => (
            <div key={n.id} className="card flex items-center gap-4 px-4 py-3">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-200">{n.name}</p>
                <p className="text-xs text-gray-500 capitalize">{n.type}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={n.enabled ? 'success' : 'muted'}>{n.enabled ? 'On' : 'Off'}</Badge>
                <button onClick={() => remove.mutate(n.id)} className="p-1.5 text-gray-500 hover:text-red-400 transition-colors">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
