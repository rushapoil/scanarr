import { CheckCircle2, Circle, Download, Eye, EyeOff, Search } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { clsx } from 'clsx'
import { format } from 'date-fns'
import { chapterApi } from '../../api/chapters'
import type { ChapterBrief } from '../../types'

interface Props {
  chapter: ChapterBrief
  mangaId: number
}

export default function ChapterRow({ chapter, mangaId }: Props) {
  const qc = useQueryClient()

  const toggleMonitor = useMutation({
    mutationFn: () => chapterApi.update(chapter.id, { monitored: !chapter.monitored }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['manga', mangaId] }),
  })

  const triggerSearch = useMutation({
    mutationFn: () => chapterApi.search(chapter.id),
  })

  return (
    <div
      className={clsx(
        'flex items-center gap-3 px-4 py-2.5 border-b border-surface-border hover:bg-surface-hover transition-colors text-sm',
        !chapter.monitored && 'opacity-50',
      )}
    >
      {/* Status icon */}
      <div className="w-5 flex-shrink-0">
        {chapter.downloaded ? (
          <CheckCircle2 size={16} className="text-green-400" />
        ) : (
          <Circle size={16} className="text-gray-600" />
        )}
      </div>

      {/* Chapter number + title */}
      <div className="flex-1 min-w-0">
        <span className="font-medium text-gray-200">
          Chapter {chapter.chapter_number}
        </span>
        {chapter.title && (
          <span className="text-gray-400 ml-2 truncate">{chapter.title}</span>
        )}
      </div>

      {/* Release date */}
      <div className="text-gray-500 text-xs w-24 text-right flex-shrink-0">
        {chapter.release_date ? format(new Date(chapter.release_date), 'dd MMM yyyy') : '—'}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 flex-shrink-0">
        <button
          onClick={() => toggleMonitor.mutate()}
          className="p-1 rounded text-gray-500 hover:text-gray-300 transition-colors"
          title={chapter.monitored ? 'Unmonitor' : 'Monitor'}
        >
          {chapter.monitored ? <Eye size={14} /> : <EyeOff size={14} />}
        </button>
        {!chapter.downloaded && (
          <button
            onClick={() => triggerSearch.mutate()}
            className="p-1 rounded text-gray-500 hover:text-brand-400 transition-colors"
            title="Search"
          >
            <Search size={14} />
          </button>
        )}
      </div>
    </div>
  )
}
