import type { APIResponse, CatalogEntrySummary, CatalogEntryDetail, SearchParams, DraftDetail, DraftListResponse } from '../types'
import { apiFetch } from './common'

const API_BASE = '/api/v1/catalog-service'

export async function searchCatalogEntries(params?: SearchParams): Promise<CatalogEntrySummary[]> {
  const searchParams = new URLSearchParams()
  if (params?.query) searchParams.set('query', params.query)
  if (params?.keyword) params.keyword.forEach((k: string) => searchParams.append('keyword', k))
  if (params?.theme) params.theme.forEach((t: string) => searchParams.append('theme', t))
  if (params?.date_field) searchParams.set('date_field', params.date_field)
  if (params?.date_from) searchParams.set('date_from', params.date_from)
  if (params?.date_to) searchParams.set('date_to', params.date_to)
  if (params?.limit) searchParams.set('limit', String(params.limit))
  if (params?.offset) searchParams.set('offset', String(params.offset))
  if (params?.sort_field) searchParams.set('sort_field', params.sort_field)
  if (params?.sort_order) searchParams.set('sort_order', params.sort_order)

  const url = `${API_BASE}/catalog/entries?${searchParams.toString()}`
  const response = await apiFetch(url)
  const data: APIResponse<CatalogEntrySummary[]> = await response.json()
  return data.result
}

export async function getCatalogEntry(id: number): Promise<CatalogEntryDetail> {
  const response = await apiFetch(`${API_BASE}/catalog/entries/${id}`)
  const data: APIResponse<CatalogEntryDetail> = await response.json()
  return data.result
}

export async function getCatalogEntryRdf(id: number): Promise<Record<string, unknown>> {
  const response = await apiFetch(`${API_BASE}/catalog/entries/${id}/rdf`)
  const data: APIResponse<Record<string, unknown>> = await response.json()
  return data.result
}

export function getCatalogEntryRdfDownloadUrl(id: number): string {
  return `${API_BASE}/catalog/entries/${id}/rdf/download`
}

export function getCatalogExportCsvUrl(limit?: number): string {
  const params = limit ? `?limit=${limit}` : ''
  return `${API_BASE}/catalog/export/csv${params}`
}

// Draft read APIs (from catalog-service)
export async function listDrafts(params?: { snapshot_id?: string; limit?: number; offset?: number }): Promise<DraftListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.snapshot_id) searchParams.set('snapshot_id', params.snapshot_id)
  if (params?.limit) searchParams.set('limit', String(params.limit))
  if (params?.offset) searchParams.set('offset', String(params.offset))

  const url = `${API_BASE}/draft/entries?${searchParams.toString()}`
  const response = await apiFetch(url)
  const data: APIResponse<DraftListResponse> = await response.json()
  return data.result
}

export async function getDraft(id: number): Promise<DraftDetail> {
  const response = await apiFetch(`${API_BASE}/draft/entries/${id}`)
  const data: APIResponse<DraftDetail> = await response.json()
  return data.result
}
