export type IngestionRunState = 'STORED' | 'DRAFTED' | 'FAILED'

export interface IngestionRun {
  run_id: number
  snapshot_id: string
  state: IngestionRunState
  mapping_version: string
  created_at: string
  error: string | null
  draft_id: number | null
}

export interface StoreResult {
  snapshot_id: string
  run_id: number
  metadata_count: number
  state: 'STORED'
}

export interface DraftCreationResult {
  draft: {
    id: number
    snapshot_id: string
    status: string
    title: string | null
  }
  run_id: number
  mapping_version: string
  state: 'DRAFTED'
}

export interface IngestionRunListResponse {
  runs: IngestionRun[]
  count: number
  limit: number
  offset: number
}
