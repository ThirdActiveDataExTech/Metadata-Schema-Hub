export interface CatalogEntrySummary {
  id: number
  title: string | null
  issued: string | null
  modified: string | null
  identifier: string
  publisher: string | null
  keyword: string[] | null
  theme: string[] | null
  landing_page: string | null
  access_url: string | null
  external_ids: string[] | null
  ingested_at: string | null
  updated_at: string | null
}

export interface CatalogEntryDetail extends CatalogEntrySummary {
  description: string | null
  latest_snapshot_id: string | null
}

export interface SearchParams {
  query?: string
  keyword?: string[]
  theme?: string[]
  date_field?: 'issued' | 'modified' | 'ingested_at' | 'updated_at'
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
  sort_field?: string
  sort_order?: 'asc' | 'desc'
}

export interface CatalogListResponse {
  entries: CatalogEntrySummary[]
  total?: number
}
