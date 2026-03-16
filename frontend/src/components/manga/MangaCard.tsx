import { Link } from 'react-router-dom'
import { BookOpen, EyeOff } from 'lucide-react'
import { clsx } from 'clsx'
import type { Manga } from '../../types'
import Badge from '../common/Badge'

interface Props {
  manga: Manga
}

const STATUS_BADGE: Record<string, { label: string; variant: 'success' | 'muted' | 'warning' | 'danger' }> = {
  ongoing: { label: 'Ongoing', variant: 'success' },
  completed: { label: 'Completed', variant: 'info' as 'muted' },
  hiatus: { label: 'Hiatus', variant: 'warning' },
  cancelled: { label: 'Cancelled', variant: 'danger' },
  upcoming: { label: 'Upcoming', variant: 'muted' },
}

export default function MangaCard({ manga }: Props) {
  const status = STATUS_BADGE[manga.status] ?? STATUS_BADGE.ongoing
  const pct = manga.chapter_count
    ? Math.round((manga.downloaded_chapter_count / manga.chapter_count) * 100)
    : 0

  return (
    <Link
      to={`/manga/${manga.id}`}
      className={clsx(
        'card flex flex-col overflow-hidden hover:border-brand-600/60 transition-colors group',
        !manga.monitored && 'opacity-60',
      )}
    >
      {/* Cover */}
      <div className="relative aspect-[2/3] bg-surface-border overflow-hidden flex-shrink-0">
        {manga.cover_url || manga.cover_local ? (
          <img
            src={manga.cover_local || manga.cover_url}
            alt={manga.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <BookOpen size={32} className="text-gray-600" strokeWidth={1} />
          </div>
        )}
        {!manga.monitored && (
          <div className="absolute top-2 right-2">
            <EyeOff size={14} className="text-gray-400" />
          </div>
        )}
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-surface-border">
          <div
            className="h-full bg-brand-500 transition-all"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Info */}
      <div className="p-3 flex flex-col gap-1 flex-1">
        <h3 className="text-sm font-medium text-gray-200 line-clamp-2 leading-snug">
          {manga.title}
        </h3>
        <div className="flex items-center gap-2 mt-auto pt-1">
          <Badge variant={status.variant as any}>{status.label}</Badge>
          <span className="text-xs text-gray-500 ml-auto">
            {manga.downloaded_chapter_count}/{manga.chapter_count}
          </span>
        </div>
      </div>
    </Link>
  )
}
