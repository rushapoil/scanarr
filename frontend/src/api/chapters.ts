import api from './client'
import type { Chapter } from '../types'

export const chapterApi = {
  listByManga: (mangaId: number) =>
    api.get<Chapter[]>(`/chapter/manga/${mangaId}`).then((r) => r.data),

  get: (id: number) =>
    api.get<Chapter>(`/chapter/${id}`).then((r) => r.data),

  update: (id: number, body: { monitored?: boolean; ignored?: boolean }) =>
    api.put<Chapter>(`/chapter/${id}`, body).then((r) => r.data),

  search: (id: number) =>
    api.post(`/chapter/${id}/search`).then((r) => r.data),
}
