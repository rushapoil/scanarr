import api from './client'
import type {
  DownloadClient,
  Indexer,
  LanguageProfile,
  NamingConfig,
  Notification,
  ProwlarrConfig,
  QualityProfile,
  RootFolder,
} from '../types'

export const settingsApi = {
  // Prowlarr
  getProwlarr: () => api.get<ProwlarrConfig>('/settings/prowlarr').then((r) => r.data),
  saveProwlarr: (body: { url: string; api_key: string; enabled: boolean }) =>
    api.put<ProwlarrConfig>('/settings/prowlarr', body).then((r) => r.data),
  testProwlarr: () => api.post('/settings/prowlarr/test').then((r) => r.data),
  syncIndexers: () => api.post('/settings/prowlarr/sync-indexers').then((r) => r.data),

  // Indexers
  listIndexers: () => api.get<Indexer[]>('/settings/indexer').then((r) => r.data),

  // Download clients
  listClients: () => api.get<DownloadClient[]>('/settings/downloadclient').then((r) => r.data),
  addClient: (body: Partial<DownloadClient> & { password?: string; api_key?: string }) =>
    api.post<DownloadClient>('/settings/downloadclient', body).then((r) => r.data),
  updateClient: (id: number, body: Partial<DownloadClient> & { password?: string; api_key?: string }) =>
    api.put<DownloadClient>(`/settings/downloadclient/${id}`, body).then((r) => r.data),
  deleteClient: (id: number) => api.delete(`/settings/downloadclient/${id}`),
  testClient: (id: number) => api.post(`/settings/downloadclient/${id}/test`).then((r) => r.data),

  // Quality profiles
  listQualityProfiles: () => api.get<QualityProfile[]>('/settings/qualityprofile').then((r) => r.data),

  // Language profiles
  listLanguageProfiles: () => api.get<LanguageProfile[]>('/settings/languageprofile').then((r) => r.data),

  // Naming
  getNaming: () => api.get<NamingConfig>('/settings/naming').then((r) => r.data),
  updateNaming: (body: Partial<NamingConfig>) =>
    api.put<NamingConfig>('/settings/naming', body).then((r) => r.data),

  // Notifications
  listNotifications: () => api.get<Notification[]>('/settings/notification').then((r) => r.data),
  addNotification: (body: Omit<Notification, 'id'> & { settings: Record<string, string> }) =>
    api.post<Notification>('/settings/notification', body).then((r) => r.data),
  deleteNotification: (id: number) => api.delete(`/settings/notification/${id}`),

  // Root folders
  listRootFolders: () => api.get<RootFolder[]>('/settings/rootfolder').then((r) => r.data),
}
