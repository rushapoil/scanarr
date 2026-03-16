import api from './client'
import type { CalendarEntry, HistoryPage, SystemStatus } from '../types'

export const systemApi = {
  status: () =>
    api.get<SystemStatus>('/system/status').then((r) => r.data),

  diskSpace: () =>
    api.get<{ path: string; free_space: number; total_space: number; used_space: number }[]>('/system/diskspace').then((r) => r.data),

  tasks: () =>
    api.get<{ id: string; name: string; next_run_time?: string; trigger: string }[]>('/system/task').then((r) => r.data),

  runTask: (jobId: string) =>
    api.post(`/system/task/${jobId}/run`).then((r) => r.data),
}

export const calendarApi = {
  list: (start?: string, end?: string) =>
    api.get<CalendarEntry[]>('/calendar', { params: { start, end } }).then((r) => r.data),
}

export const historyApi = {
  list: (page = 1, pageSize = 50) =>
    api.get<HistoryPage>('/history', { params: { page, page_size: pageSize } }).then((r) => r.data),
}
