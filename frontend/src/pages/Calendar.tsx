import { useQuery } from '@tanstack/react-query'
import { Calendar as CalIcon } from 'lucide-react'
import { format, isToday, isFuture } from 'date-fns'
import { calendarApi } from '../api/system'
import Spinner from '../components/common/Spinner'
import EmptyState from '../components/common/EmptyState'
import Badge from '../components/common/Badge'

export default function Calendar() {
  const { data: entries = [], isLoading } = useQuery({
    queryKey: ['calendar'],
    queryFn: () => calendarApi.list(),
  })

  // Group by date
  const grouped: Record<string, typeof entries> = {}
  for (const entry of entries) {
    const day = format(new Date(entry.release_date), 'yyyy-MM-dd')
    if (!grouped[day]) grouped[day] = []
    grouped[day].push(entry)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-200">Calendar</h2>

      {isLoading ? (
        <div className="flex justify-center py-16"><Spinner /></div>
      ) : entries.length === 0 ? (
        <EmptyState icon={CalIcon} title="No upcoming chapters" description="Add monitored mangas to see their release schedule here" />
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).sort(([a], [b]) => a.localeCompare(b)).map(([day, dayEntries]) => {
            const date = new Date(day)
            const isNow = isToday(date)
            const upcoming = isFuture(date) || isNow
            return (
              <div key={day}>
                <div className="flex items-center gap-3 mb-2">
                  <h3 className={`text-sm font-semibold ${isNow ? 'text-brand-400' : upcoming ? 'text-gray-300' : 'text-gray-500'}`}>
                    {isNow ? 'Today — ' : ''}{format(date, 'EEEE, MMMM d')}
                  </h3>
                  <div className="h-px flex-1 bg-surface-border" />
                </div>
                <div className="space-y-2">
                  {dayEntries.map((e) => (
                    <div key={e.chapter_id} className="card flex items-center gap-4 px-4 py-3">
                      {e.manga_cover && (
                        <img src={e.manga_cover} alt={e.manga_title} className="w-9 h-12 object-cover rounded" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-200">{e.manga_title}</p>
                        <p className="text-xs text-gray-500">
                          Chapter {e.chapter_number}
                          {e.chapter_title && ` — ${e.chapter_title}`}
                        </p>
                      </div>
                      <div className="flex-shrink-0">
                        {e.downloaded ? (
                          <Badge variant="success">Downloaded</Badge>
                        ) : upcoming ? (
                          <Badge variant="muted">Upcoming</Badge>
                        ) : (
                          <Badge variant="warning">Missing</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
