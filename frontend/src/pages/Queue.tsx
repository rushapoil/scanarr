import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Download, Trash2 } from 'lucide-react'
import { queueApi } from '../api/queue'
import Spinner from '../components/common/Spinner'
import Badge from '../components/common/Badge'
import EmptyState from '../components/common/EmptyState'
import type { QueueItem, QueueStatus } from '../types'

const STATUS_VARIANT: Record<QueueStatus, string> = {
  queued: 'muted',
  downloading: 'info',
  completed: 'success',
  failed: 'danger',
  ignored: 'muted',
  paused: 'warning',
} as const

function formatSize(bytes?: number) {
  if (!bytes) return '—'
  if (bytes > 1e9) return `${(bytes / 1e9).toFixed(1)} GB`
  if (bytes > 1e6) return `${(bytes / 1e6).toFixed(0)} MB`
  return `${(bytes / 1e3).toFixed(0)} KB`
}

function QueueRow({ item }: { item: QueueItem }) {
  const qc = useQueryClient()
  const remove = useMutation({
    mutationFn: () => queueApi.remove(item.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['queue'] }),
  })

  return (
    <div className="px-5 py-3 flex items-center gap-3 border-b border-surface-border hover:bg-surface-hover text-sm">
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-200 truncate">
          {item.manga_title && `${item.manga_title} `}
          {item.chapter_number != null && `— Ch. ${item.chapter_number}`}
        </p>
        <p className="text-xs text-gray-500 truncate mt-0.5">{item.title}</p>
      </div>
      <div className="flex items-center gap-3 flex-shrink-0">
        {item.status === 'downloading' && (
          <div className="w-24">
            <div className="h-1.5 bg-surface-border rounded-full overflow-hidden">
              <div className="h-full bg-brand-500 transition-all" style={{ width: `${item.progress * 100}%` }} />
            </div>
            <p className="text-xs text-gray-500 text-right mt-0.5">{Math.round(item.progress * 100)}%</p>
          </div>
        )}
        <Badge variant={STATUS_VARIANT[item.status] as any}>{item.status}</Badge>
        <span className="text-xs text-gray-500 w-16 text-right">{formatSize(item.size)}</span>
        <span className="text-xs text-gray-500">{item.protocol}</span>
        <button
          onClick={() => remove.mutate()}
          className="p-1 text-gray-500 hover:text-red-400 transition-colors"
        >
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  )
}

export default function Queue() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['queue'],
    queryFn: () => queueApi.list(1, 50),
    refetchInterval: 5_000,
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-200">
          Download Queue {data && `(${data.total_count})`}
        </h2>
        <button className="btn-secondary text-sm" onClick={() => refetch()}>Refresh</button>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16"><Spinner /></div>
        ) : data?.items.length === 0 ? (
          <EmptyState
            icon={Download}
            title="Queue is empty"
            description="Downloads will appear here when chapters are grabbed"
          />
        ) : (
          <div>
            {data?.items.map((item) => <QueueRow key={item.id} item={item} />)}
          </div>
        )}
      </div>
    </div>
  )
}
