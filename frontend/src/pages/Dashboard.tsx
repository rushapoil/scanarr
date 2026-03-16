import { useQuery } from '@tanstack/react-query'
import { BookOpen, Download, Clock, HardDrive } from 'lucide-react'
import { mangaApi } from '../api/mangas'
import { historyApi, systemApi } from '../api/system'
import { queueApi } from '../api/queue'
import Spinner from '../components/common/Spinner'
import Badge from '../components/common/Badge'
import { format } from 'date-fns'

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: string | number; icon: React.ElementType; color: string
}) {
  return (
    <div className="card p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={22} />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-100">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data: mangas = [], isLoading: loadingMangas } = useQuery({
    queryKey: ['mangas'],
    queryFn: () => mangaApi.list(),
  })
  const { data: queue } = useQuery({
    queryKey: ['queue'],
    queryFn: () => queueApi.list(1, 5),
    refetchInterval: 10_000,
  })
  const { data: history } = useQuery({
    queryKey: ['history'],
    queryFn: () => historyApi.list(1, 10),
  })
  const { data: diskSpaces = [] } = useQuery({
    queryKey: ['diskspace'],
    queryFn: systemApi.diskSpace,
  })

  const totalChapters = mangas.reduce((sum, m) => sum + m.chapter_count, 0)
  const downloaded = mangas.reduce((sum, m) => sum + m.downloaded_chapter_count, 0)
  const activeDownloads = queue?.items.filter(i => i.status === 'downloading').length ?? 0

  if (loadingMangas) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Mangas" value={mangas.length} icon={BookOpen} color="bg-brand-900/50 text-brand-400" />
        <StatCard label="Chapters total" value={totalChapters} icon={BookOpen} color="bg-indigo-900/50 text-indigo-400" />
        <StatCard label="Downloaded" value={downloaded} icon={Download} color="bg-green-900/50 text-green-400" />
        <StatCard label="Active downloads" value={activeDownloads} icon={Download} color="bg-yellow-900/50 text-yellow-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent activity */}
        <div className="card">
          <div className="px-5 py-3 border-b border-surface-border">
            <h2 className="font-semibold text-gray-200 flex items-center gap-2">
              <Clock size={16} className="text-brand-400" /> Recent Activity
            </h2>
          </div>
          <div className="divide-y divide-surface-border">
            {history?.items.length === 0 && (
              <p className="px-5 py-8 text-center text-sm text-gray-500">No activity yet</p>
            )}
            {history?.items.map((item) => (
              <div key={item.id} className="px-5 py-3 flex items-center gap-3">
                <Badge
                  variant={
                    item.event_type === 'downloadImported' ? 'success'
                    : item.event_type === 'grabbed' ? 'info'
                    : item.event_type === 'downloadFailed' ? 'danger'
                    : 'muted'
                  }
                >
                  {item.event_type}
                </Badge>
                <span className="text-sm text-gray-300 truncate flex-1">
                  {item.manga_title} {item.chapter_number != null && `— Ch. ${item.chapter_number}`}
                </span>
                <span className="text-xs text-gray-600 flex-shrink-0">
                  {format(new Date(item.created_at), 'HH:mm')}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Disk space */}
        <div className="card">
          <div className="px-5 py-3 border-b border-surface-border">
            <h2 className="font-semibold text-gray-200 flex items-center gap-2">
              <HardDrive size={16} className="text-brand-400" /> Disk Space
            </h2>
          </div>
          <div className="p-5 space-y-4">
            {diskSpaces.length === 0 && (
              <p className="text-sm text-gray-500">No folders configured</p>
            )}
            {diskSpaces.map((d) => {
              const usedPct = Math.round((d.used_space / d.total_space) * 100)
              const freeGB = (d.free_space / 1e9).toFixed(1)
              const totalGB = (d.total_space / 1e9).toFixed(1)
              return (
                <div key={d.path}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-300 font-mono text-xs">{d.path}</span>
                    <span className="text-gray-500 text-xs">{freeGB} GB free / {totalGB} GB</span>
                  </div>
                  <div className="h-2 bg-surface-border rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${usedPct > 90 ? 'bg-red-500' : usedPct > 75 ? 'bg-yellow-500' : 'bg-brand-500'}`}
                      style={{ width: `${usedPct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
