import type { APIResponse, MergeCreateResponse, MergeDetail, MergeListResponse, MergeRegenResult } from '../types'
import type { SSEEventHandler } from './sse'
import { apiFetch, INGESTION_SERVICE_URL } from './common'
import { streamAgentSSE } from './sse'

const BASE = INGESTION_SERVICE_URL

export async function executeMergePhase(draftId: number): Promise<MergeCreateResponse> {
  const response = await apiFetch(`${BASE}/ingestion/merge/${draftId}`, {
    method: 'POST',
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.description || 'Failed to execute merge phase')
  }

  const data: APIResponse<MergeCreateResponse> = await response.json()
  return data.result
}

export async function listMerges(params?: { limit?: number; offset?: number }): Promise<MergeListResponse> {
  const sp = new URLSearchParams()
  if (params?.limit) sp.set('limit', String(params.limit))
  if (params?.offset) sp.set('offset', String(params.offset))

  const response = await apiFetch(`${BASE}/merge/entries?${sp.toString()}`)
  const data: APIResponse<MergeListResponse> = await response.json()
  return data.result
}

export async function getMerge(mergeId: number): Promise<MergeDetail> {
  const response = await apiFetch(`${BASE}/merge/entries/${mergeId}`)
  const data: APIResponse<MergeDetail> = await response.json()
  return data.result
}

export async function getMergeByDraft(draftId: number): Promise<MergeDetail> {
  const response = await apiFetch(`${BASE}/merge/entries/by-draft/${draftId}`)
  const data: APIResponse<MergeDetail> = await response.json()
  return data.result
}

export async function approveMerge(mergeId: number, decidedBy: string, targetEntryId?: number): Promise<MergeDetail> {
  const body: Record<string, unknown> = { decided_by: decidedBy }
  if (targetEntryId !== undefined) body.target_entry_id = targetEntryId

  const response = await apiFetch(`${BASE}/merge/entries/${mergeId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.description || 'Failed to approve merge')
  }

  const data: APIResponse<MergeDetail> = await response.json()
  return data.result
}

export async function rejectMerge(mergeId: number, decidedBy: string): Promise<MergeDetail> {
  const response = await apiFetch(`${BASE}/merge/entries/${mergeId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decided_by: decidedBy }),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.description || 'Failed to reject merge')
  }

  const data: APIResponse<MergeDetail> = await response.json()
  return data.result
}

export async function regenMergeAnalysis(mergeId: number): Promise<MergeRegenResult> {
  const response = await apiFetch(`${BASE}/merge/entries/${mergeId}/regen`, {
    method: 'POST',
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.message || error.description || 'Agent merge analysis failed')
  }

  const data: APIResponse<MergeRegenResult> = await response.json()
  return data.result
}

export async function streamMergeRegen(
  mergeId: number,
  handlers: { onEvent: SSEEventHandler; onComplete: () => void; onError: (msg: string) => void; signal?: AbortSignal },
): Promise<void> {
  return streamAgentSSE(`${BASE}/merge/entries/${mergeId}/regen/stream`, handlers)
}
