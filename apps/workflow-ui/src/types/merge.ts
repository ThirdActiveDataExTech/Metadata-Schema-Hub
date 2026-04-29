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

export interface MergeCreateResponse {
  merge: MergeDetail
  auto_published: boolean
  catalog_entry_id: number | null
}

export interface MergeListResponse {
  merges: MergeDetail[]
  total: number
  count: number
  limit: number
  offset: number
}

export type AgentDecision = 'approve' | 'reject' | 'defer'

export interface MergeRegenResult {
  agent_decision: AgentDecision
  agent_reason: string
  // approve/reject 시 merge 필드 포함
  id?: number
  decision?: MergeDecision
  decided_by?: string | null
  decided_at?: string | null
  target_entry_id?: number | null
  merge_id?: number
  catalog_entry_id?: number
}
