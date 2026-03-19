import type { APIResponse, StoreResult, DraftCreationResult, IngestionRun, IngestionRunListResponse, PublishResult, DiscardResult, MetadataEntryOption, DraftFieldsUpdatePayload, DraftDetail } from '../types'
import { apiFetch, INGESTION_SERVICE_URL } from './common'

const INGESTION_API_BASE = INGESTION_SERVICE_URL

export async function storeMetadata(file: File): Promise<StoreResult> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiFetch(`${INGESTION_API_BASE}/ingestion/store`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.description || 'Failed to store metadata')
  }

  const data: APIResponse<StoreResult> = await response.json()
  return data.result
}

export async function createDraft(runId: number): Promise<DraftCreationResult> {
  const response = await apiFetch(`${INGESTION_API_BASE}/ingestion/draft/${runId}`, {
    method: 'POST',
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.description || 'Failed to create draft')
  }

  const data: APIResponse<DraftCreationResult> = await response.json()
  return data.result
}

export async function listIngestionRuns(params?: { state?: string; limit?: number; offset?: number }): Promise<IngestionRunListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.state) searchParams.set('state', params.state)
  if (params?.limit) searchParams.set('limit', String(params.limit))
  if (params?.offset) searchParams.set('offset', String(params.offset))

  const url = `${INGESTION_API_BASE}/ingestion/runs?${searchParams.toString()}`
  const response = await apiFetch(url)
  const data: APIResponse<IngestionRunListResponse> = await response.json()
  return data.result
}

export async function getIngestionRun(runId: number): Promise<IngestionRun> {
  const response = await apiFetch(`${INGESTION_API_BASE}/ingestion/runs/${runId}`)
  const data: APIResponse<IngestionRun> = await response.json()
  return data.result
}

export async function publishDraft(draftId: number): Promise<PublishResult> {
  const response = await apiFetch(`${INGESTION_API_BASE}/draft/entries/${draftId}/publish`, {
    method: 'POST',
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.description || 'Failed to publish draft')
  }

  const data: APIResponse<PublishResult> = await response.json()
  return data.result
}

export async function discardDraft(draftId: number): Promise<DiscardResult> {
  const response = await apiFetch(`${INGESTION_API_BASE}/draft/entries/${draftId}/discard`, {
    method: 'POST',
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.description || 'Failed to discard draft')
  }

  const data: APIResponse<DiscardResult> = await response.json()
  return data.result
}

export async function getMetadataOptions(draftId: number): Promise<MetadataEntryOption[]> {
  const response = await apiFetch(`${INGESTION_API_BASE}/draft/entries/${draftId}/metadata-options`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.description || 'Failed to get metadata options')
  }

  const data: APIResponse<MetadataEntryOption[]> = await response.json()
  return data.result
}

export async function updateDraftFields(draftId: number, payload: DraftFieldsUpdatePayload): Promise<DraftDetail> {
  const response = await apiFetch(`${INGESTION_API_BASE}/draft/entries/${draftId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.description || 'Failed to update draft')
  }

  const data: APIResponse<DraftDetail> = await response.json()
  return data.result
}
