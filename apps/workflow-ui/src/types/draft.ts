export type DraftStatus = 'PENDING' | 'PUBLISHED' | 'DISCARDED'

export interface MappingCandidate {
  metadata_column: string
  correlation: number
  value: string | null
}

export interface MappingEvidence {
  [fieldName: string]: {
    selected: MappingCandidate
    alternatives: MappingCandidate[]
  }
}

export interface DraftSummary {
  id: number
  snapshot_id: string
  mapping_version: string
  status: DraftStatus
  title: string | null
  created_at: string
}

export interface DraftDetail extends DraftSummary {
  description: string | null
  issued: string | null
  modified: string | null
  publisher: string | null
  keyword: string[] | null
  theme: string[] | null
  landing_page: string | null
  access_url: string | null
  mapping_evidence: MappingEvidence
  updated_at: string
}

export interface DraftListResponse {
  drafts: DraftSummary[]
  count: number
  limit: number
  offset: number
}

export interface PublishResult {
  catalog_entry_id: number
  identifier: string
  title: string
  latest_snapshot_id: string
}

export interface DiscardResult {
  id: number
  status: 'DISCARDED'
}
