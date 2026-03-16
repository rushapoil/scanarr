// ── Manga ─────────────────────────────────────────────────────────────────────

export interface Genre {
  id: number
  genre: string
}

export interface Manga {
  id: number
  title: string
  title_slug: string
  title_alt: string[]
  mangadex_id?: string
  author?: string
  artist?: string
  synopsis?: string
  cover_url?: string
  cover_local?: string
  status: 'ongoing' | 'completed' | 'hiatus' | 'cancelled' | 'upcoming'
  year?: number
  publisher?: string
  monitored: boolean
  monitor_status: string
  quality_profile_id?: number
  language_profile_id?: number
  root_folder_path: string
  chapter_count: number
  monitored_chapter_count: number
  downloaded_chapter_count: number
  added_at: string
  updated_at: string
  genres: Genre[]
}

export interface MangaDetail extends Manga {
  chapters: ChapterBrief[]
}

export interface ChapterBrief {
  id: number
  chapter_number: number
  volume_number?: number
  title?: string
  monitored: boolean
  downloaded: boolean
  release_date?: string
}

export interface MangaDexResult {
  mangadex_id: string
  title: string
  title_alt: string[]
  author?: string
  artist?: string
  synopsis?: string
  cover_url?: string
  status: string
  year?: number
  genres: string[]
  already_in_library: boolean
}

// ── Chapter ───────────────────────────────────────────────────────────────────

export interface ChapterFile {
  id: number
  path: string
  size?: number
  format?: string
  language?: string
  scanlator_group?: string
}

export interface Chapter {
  id: number
  manga_id: number
  chapter_number: number
  volume_number?: number
  title?: string
  mangadex_id?: string
  monitored: boolean
  downloaded: boolean
  ignored: boolean
  release_date?: string
  download_date?: string
  language?: string
  scanlator_group?: string
  files: ChapterFile[]
}

// ── Queue ─────────────────────────────────────────────────────────────────────

export type QueueStatus = 'queued' | 'downloading' | 'completed' | 'failed' | 'ignored' | 'paused'

export interface QueueItem {
  id: number
  manga_id?: number
  chapter_id?: number
  title: string
  protocol: 'torrent' | 'usenet'
  quality?: string
  language?: string
  scanlator_group?: string
  size?: number
  status: QueueStatus
  progress: number
  error_message?: string
  added_at: string
  started_at?: string
  completed_at?: string
  manga_title?: string
  chapter_number?: number
  indexer_name?: string
  client_name?: string
}

export interface QueuePage {
  total_count: number
  page: number
  page_size: number
  items: QueueItem[]
}

// ── History ───────────────────────────────────────────────────────────────────

export type HistoryEventType =
  | 'grabbed'
  | 'downloadFailed'
  | 'downloadImported'
  | 'downloadIgnored'
  | 'chapterFileDeleted'

export interface HistoryItem {
  id: number
  manga_id?: number
  chapter_id?: number
  event_type: HistoryEventType
  source_title?: string
  indexer?: string
  download_client?: string
  quality?: string
  language?: string
  size?: number
  created_at: string
  manga_title?: string
  chapter_number?: number
}

export interface HistoryPage {
  total_count: number
  page: number
  page_size: number
  items: HistoryItem[]
}

// ── Settings ──────────────────────────────────────────────────────────────────

export interface ProwlarrConfig {
  id: number
  url: string
  enabled: boolean
  last_sync?: string
}

export interface Indexer {
  id: number
  prowlarr_id?: number
  name: string
  protocol: 'torrent' | 'usenet'
  type?: string
  priority: number
  enabled: boolean
}

export interface DownloadClient {
  id: number
  name: string
  type: string
  host: string
  port: number
  use_ssl: boolean
  url_base?: string
  username?: string
  category: string
  priority: number
  enabled: boolean
  is_default: boolean
}

export interface QualityProfileItem {
  id: number
  quality: string
  allowed: boolean
  priority: number
}

export interface QualityProfile {
  id: number
  name: string
  is_default: boolean
  items: QualityProfileItem[]
}

export interface LanguageProfile {
  id: number
  name: string
  languages: string[]
}

export interface NamingConfig {
  id: number
  rename_chapters: boolean
  replace_illegal_chars: boolean
  folder_format: string
  chapter_format: string
}

export interface Notification {
  id: number
  name: string
  type: string
  on_grab: boolean
  on_download: boolean
  on_upgrade: boolean
  on_rename: boolean
  on_chapter_delete: boolean
  on_health_issue: boolean
  enabled: boolean
}

export interface RootFolder {
  id: number
  path: string
  free_space?: number
  is_default: boolean
}

// ── System ────────────────────────────────────────────────────────────────────

export interface SystemStatus {
  app_name: string
  version: string
  is_debug: boolean
  db_path: string
  config_dir: string
  data_dir: string
  os_name: string
  os_version: string
  runtime_version: string
  startup_time: string
}

export interface CalendarEntry {
  chapter_id: number
  manga_id: number
  manga_title: string
  manga_cover?: string
  chapter_number: number
  chapter_title?: string
  release_date: string
  downloaded: boolean
}
