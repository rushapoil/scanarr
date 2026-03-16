import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BookOpen, Plus, Search } from 'lucide-react'
import { mangaApi } from '../api/mangas'
import MangaCard from '../components/manga/MangaCard'
import AddMangaModal from '../components/manga/AddMangaModal'
import Spinner from '../components/common/Spinner'
import EmptyState from '../components/common/EmptyState'

export default function Library() {
  const [addOpen, setAddOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState<'all' | 'monitored' | 'unmonitored'>('all')

  const { data: mangas = [], isLoading } = useQuery({
    queryKey: ['mangas'],
    queryFn: () => mangaApi.list(),
  })

  const filtered = mangas.filter((m) => {
    const matchSearch = m.title.toLowerCase().includes(search.toLowerCase())
    const matchFilter =
      filter === 'all' ||
      (filter === 'monitored' && m.monitored) ||
      (filter === 'unmonitored' && !m.monitored)
    return matchSearch && matchFilter
  })

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            className="input pl-9"
            placeholder="Filter library…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="flex rounded-md overflow-hidden border border-surface-border">
          {(['all', 'monitored', 'unmonitored'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 text-xs font-medium transition-colors capitalize ${
                filter === f
                  ? 'bg-brand-600 text-white'
                  : 'bg-surface-card text-gray-400 hover:text-gray-200 hover:bg-surface-hover'
              }`}
            >
              {f}
            </button>
          ))}
        </div>

        <button className="btn-primary" onClick={() => setAddOpen(true)}>
          <Plus size={16} /> Add Manga
        </button>
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={BookOpen}
          title="No mangas in your library"
          description="Add a manga to start tracking chapters"
          action={
            <button className="btn-primary" onClick={() => setAddOpen(true)}>
              <Plus size={16} /> Add Manga
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 gap-4">
          {filtered.map((m) => <MangaCard key={m.id} manga={m} />)}
        </div>
      )}

      <AddMangaModal open={addOpen} onClose={() => setAddOpen(false)} />
    </div>
  )
}
