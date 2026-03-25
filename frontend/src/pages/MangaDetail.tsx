import { useParams, useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, BookOpen, Eye, EyeOff, Search, Trash2 } from 'lucide-react'
import { mangaApi } from '../api/mangas'
import Spinner from '../components/common/Spinner'
import Badge from '../components/common/Badge'
import ChapterRow from '../components/manga/ChapterRow'

export default function MangaDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()
  const mangaId = Number(id)

  const { data: manga, isLoading } = useQuery({
    queryKey: ['manga', mangaId],
    queryFn: () => mangaApi.get(mangaId),
    enabled: !!mangaId,
  })

  const toggleMonitor = useMutation({
    mutationFn: () => mangaApi.update(mangaId, { monitored: !manga?.monitored }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['manga', mangaId] }),
  })

  const triggerSearch = useMutation({
    mutationFn: () => mangaApi.triggerSearch(mangaId),
  })

  const deleteManga = useMutation({
    mutationFn: () => mangaApi.delete(mangaId),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['mangas'] }); navigate('/library') },
  })

  if (isLoading) return <div className="flex justify-center py-20"><Spinner size="lg" /></div>
  if (!manga) return <div className="text-gray-400 text-center py-20">Manga not found</div>

  const pct = manga.chapter_count
    ? Math.round((manga.downloaded_chapter_count / manga.chapter_count) * 100)
    : 0

  return (
    <div className="space-y-6">
      {/* Back */}
      <button
        onClick={() => navigate('/library')}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-gray-200"
      >
        <ArrowLeft size={16} /> Back to Library
      </button>

      {/* Header */}
      <div className="card overflow-hidden">
        <div className="flex gap-6 p-6">
          {/* Cover */}
          <div className="w-36 flex-shrink-0">
            {manga.cover_url || manga.cover_local ? (
              <img
                src={manga.cover_local || manga.cover_url}
                alt={manga.title}
                className="w-full rounded-lg object-cover shadow-lg"
              />
            ) : (
              <div className="w-full aspect-[2/3] rounded-lg bg-surface-border flex items-center justify-center">
                <BookOpen size={32} className="text-gray-600" strokeWidth={1} />
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-100 flex-1">{manga.title}</h1>
              <div className="flex gap-2 flex-shrink-0">
                <button
                  onClick={() => toggleMonitor.mutate()}
                  className="btn-secondary text-xs"
                  disabled={toggleMonitor.isPending}
                >
                  {manga.monitored ? <Eye size={14} /> : <EyeOff size={14} />}
                  {manga.monitored ? 'Monitored' : 'Unmonitored'}
                </button>
                <button
                  onClick={() => triggerSearch.mutate()}
                  className="btn-secondary text-xs"
                  disabled={triggerSearch.isPending}
                >
                  <Search size={14} /> Search
                </button>
                <button
                  onClick={() => { if (confirm('Delete this manga?')) deleteManga.mutate() }}
                  className="btn-danger text-xs"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>

            {manga.author && <p className="text-gray-400 text-sm mb-1">{manga.author}</p>}

            <div className="flex flex-wrap gap-2 mb-3">
              <Badge variant={manga.status === 'ongoing' ? 'success' : manga.status === 'completed' ? 'info' as 'muted' : 'warning'}>
                {manga.status}
              </Badge>
              {manga.year && <Badge variant="muted">{manga.year}</Badge>}
              {manga.genres.slice(0, 4).map((g) => (
                <Badge key={g.id} variant="muted">{g.genre}</Badge>
              ))}
            </div>

            {manga.synopsis && (
              <p className="text-sm text-gray-400 line-clamp-3 mb-3">{manga.synopsis}</p>
            )}

            {/* Progress bar */}
            <div>
              <div className="flex justify-between text-xs text-gray-500 mb-1">
                <span>{manga.downloaded_chapter_count} / {manga.chapter_count} chapters</span>
                <span>{pct}%</span>
              </div>
              <div className="h-1.5 bg-surface-border rounded-full overflow-hidden">
                <div className="h-full bg-brand-500 transition-all" style={{ width: `${pct}%` }} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Chapters */}
      <div className="card overflow-hidden">
        <div className="px-5 py-3 border-b border-surface-border flex items-center justify-between">
          <h2 className="font-semibold text-gray-200">Chapters ({manga.chapter_count})</h2>
          <div className="flex gap-2 text-xs text-gray-500">
            <span className="text-green-400">{manga.downloaded_chapter_count} downloaded</span>
            <span>·</span>
            <span>{manga.monitored_chapter_count} monitored</span>
          </div>
        </div>
        <div className="divide-y divide-surface-border">
          {manga.chapters.length === 0 && (
            <p className="px-5 py-8 text-center text-sm text-gray-500">No chapters yet — trigger a search to find them</p>
          )}
          {manga.chapters.map((ch) => (
            <ChapterRow key={ch.id} chapter={ch} mangaId={mangaId} />
          ))}
        </div>
      </div>
    </div>
  )
}
