import api from './client'
import type { QueuePage } from '../types'

export const queueApi = {
  list: (page = 1, pageSize = 20) =>
    api.get<QueuePage>('/queue', { params: { page, page_size: pageSize } }).then((r) => r.data),

  remove: (id: number, blacklist = false) =>
    api.delete(`/queue/${id}`, { params: { blacklist } }),
}
