import { useQuery } from '@tanstack/react-query'
import { Clock } from 'lucide-react'
import { format } from 'date-fns'
import { historyApi } from '../api/system'
import Spinner from '../components/common/Spinner'
import Badge from '../components/common/Badge'
import EmptyState from '../components/common/EmptyState'
import type { HistoryEventType } from '../types'

const EVENT_VARIANT: Record<HistoryEventType, string> = {
  grabbed: 'info',
  downloadFailed: 'danger',
  downloadImported: 'success',
  downloadIgnored: 'muted',
  chapterFileDeleted: 'warning',
} as const

function formatSize(bytes?: number) {
  if (!bytes) return null
  if (bytes > 1e9) return `${(bytes / 1e9).toFixed(1)} GB`
  return `${(bytes / 1e6).toFixed(0)} MB`
}

export default function History() {
  const { data, isLoading } = useQuery({
    queryKey: ['history'],
    queryFn: () => historyApi.list(1, 100),
  })

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">
        History {data && `(${data.total_count})`}
      </h2>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16"><Spinner /></div>
        ) : data?.items.length === 0 ? (
          <EmptyState icon={Clock} title="No history yet" />
        ) : (
          <div>
            {data?.items.map((item) => (
              <div
                key={item.id}
                className="px-5 py-3 flex items-center gap-3 border-b border-surface-border hover:bg-surface-hover text-sm"
              >
                <Badge variant={EVENT_VARIANT[item.event_type] as any} className="flex-shrink-0">
                  {item.event_type}
                </Badge>
                <div className="flex-1 min-w-0">
                  <p className="text-gray-200 truncate">
                    {item.manga_title ?? '—'}
                    {item.chapter_number != null && (
                      <span className="text-gray-400"> — Ch. {item.chapter_number}</span>
                    )}
                  </p>
                  {item.source_title && (
                    <p className="text-xs text-gray-500 truncate">{item.source_title}</p>
                  )}
                </div>
                <div className="flex items-center gap-3 flex-shrink-0 text-xs text-gray-500">
                  {item.indexer && <span>{item.indexer}</span>}
                  {formatSize(item.size) && <span>{formatSize(item.size)}</span>}
                  {item.language && <span className="uppercase">{item.language}</span>}
                  <span>{format(new Date(item.created_at), 'dd MMM HH:mm')}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
