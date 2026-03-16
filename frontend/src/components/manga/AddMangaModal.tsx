import { useState } from 'react'
import { Search, Plus, Check } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import Modal from '../common/Modal'
import Spinner from '../common/Spinner'
import { mangaApi } from '../../api/mangas'
import { settingsApi } from '../../api/settings'
import type { MangaDexResult } from '../../types'

interface Props {
  open: boolean
  onClose: () => void
}

export default function AddMangaModal({ open, onClose }: Props) {
  const [term, setTerm] = useState('')
  const [debouncedTerm, setDebouncedTerm] = useState('')
  const qc = useQueryClient()

  // Debounce search term
  const handleInput = (v: string) => {
    setTerm(v)
    clearTimeout((window as any)._searchTimer)
    ;(window as any)._searchTimer = setTimeout(() => setDebouncedTerm(v), 500)
  }

  const { data: results = [], isFetching } = useQuery({
    queryKey: ['manga-search', debouncedTerm],
    queryFn: () => mangaApi.search(debouncedTerm),
    enabled: debouncedTerm.length >= 2,
    staleTime: 60_000,
  })

  const { data: rootFolders = [] } = useQuery({
    queryKey: ['root-folders'],
    queryFn: settingsApi.listRootFolders,
  })

  const addMutation = useMutation({
    mutationFn: (result: MangaDexResult) =>
      mangaApi.add({
        title: result.title,
        mangadex_id: result.mangadex_id,
        monitored: true,
        monitor_status: 'all',
        root_folder_path: rootFolders[0]?.path || '/manga',
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['mangas'] })
    },
  })

  return (
    <Modal open={open} onClose={onClose} title="Add Manga" size="xl">
      {/* Search input */}
      <div className="relative mb-4">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          type="text"
          className="input pl-9"
          placeholder="Search MangaDex…"
          value={term}
          onChange={(e) => handleInput(e.target.value)}
          autoFocus
        />
        {isFetching && (
          <Spinner size="sm" className="absolute right-3 top-1/2 -translate-y-1/2" />
        )}
      </div>

      {/* Results */}
      <div className="space-y-2 max-h-[60vh] overflow-y-auto">
        {results.length === 0 && debouncedTerm.length >= 2 && !isFetching && (
          <p className="text-center text-gray-500 py-8 text-sm">No results found</p>
        )}
        {results.map((r) => (
          <div
            key={r.mangadex_id}
            className="flex gap-3 p-3 rounded-lg bg-surface-hover border border-surface-border hover:border-brand-600/50 transition-colors"
          >
            {r.cover_url && (
              <img
                src={r.cover_url}
                alt={r.title}
                className="w-12 h-16 object-cover rounded flex-shrink-0"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate">{r.title}</p>
              <p className="text-xs text-gray-500 mt-0.5">
                {r.author && `${r.author} · `}
                {r.year && `${r.year} · `}
                {r.status}
              </p>
              {r.synopsis && (
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">{r.synopsis}</p>
              )}
            </div>
            <div className="flex items-center flex-shrink-0">
              {r.already_in_library ? (
                <span className="flex items-center gap-1 text-xs text-green-400">
                  <Check size={14} /> In library
                </span>
              ) : (
                <button
                  className="btn-primary text-xs px-3 py-1.5"
                  onClick={() => addMutation.mutate(r)}
                  disabled={addMutation.isPending}
                >
                  {addMutation.isPending ? <Spinner size="sm" /> : <Plus size={14} />}
                  Add
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </Modal>
  )
}
