import api from './client'
import type { Manga, MangaDetail, MangaDexResult } from '../types'

export const mangaApi = {
  list: (params?: { monitored?: boolean; status?: string }) =>
    api.get<Manga[]>('/manga', { params }).then((r) => r.data),

  get: (id: number) =>
    api.get<MangaDetail>(`/manga/${id}`).then((r) => r.data),

  add: (body: { title: string; mangadex_id?: string; monitored?: boolean; monitor_status?: string; root_folder_path?: string; quality_profile_id?: number; language_profile_id?: number }) =>
    api.post<Manga>('/manga', body).then((r) => r.data),

  update: (id: number, body: Partial<Manga>) =>
    api.put<Manga>(`/manga/${id}`, body).then((r) => r.data),

  delete: (id: number, deleteFiles = false) =>
    api.delete(`/manga/${id}`, { params: { delete_files: deleteFiles } }),

  search: (term: string) =>
    api.get<MangaDexResult[]>('/manga/lookup/search', { params: { term } }).then((r) => r.data),

  triggerSearch: (id: number) =>
    api.post(`/manga/${id}/search`).then((r) => r.data),
}
