export type MergeDecision = 'PENDING' | 'APPROVED' | 'REJECTED'

export interface MergeCandidate {
  entry_id: number
  overlap_ids: string[]
  updated_at: string | null
}

export interface MergeRecommendation {
  entry_id: number
  reason: string
}

export interface MergeDecided {
  entry_id: number
  decided_by: string
}

export interface MergeEvidence {
  searched_external_ids: string[]
  candidates: MergeCandidate[]
  recommended: MergeRecommendation | null
  decided: MergeDecided | null
}

export interface MergeDetail {
  id: number
  draft_id: number
  target_entry_id: number | null
  merge_evidence: MergeEvidence
  mapping_score: number
  decision: MergeDecision
  decided_at: string | null
  decided_by: string | null
  created_at: string
  updated_at: string
  // approve 응답에만 포함
  catalog_entry_id?: number
  catalog_entry_identifier?: string
}

export interface MergeListResponse {
  merges: MergeDetail[]
  count: number
  limit: number
  offset: number
}
