import type { APIResponse, EventListResponse, LineageGraph } from '../types'
import { apiFetch, CATALOG_SERVICE_URL } from './common'

const API_BASE = CATALOG_SERVICE_URL

export async function fetchLineageEvents(params?: {
  jobName?: string
  eventType?: string
  limit?: number
  offset?: number
}): Promise<EventListResponse> {
  const searchParams = new URLSearchParams()
  if (params?.jobName) searchParams.set('job_name', params.jobName)
  if (params?.eventType) searchParams.set('event_type', params.eventType)
  if (params?.limit) searchParams.set('limit', String(params.limit))
  if (params?.offset) searchParams.set('offset', String(params.offset))

  const url = `${API_BASE}/lineage/events?${searchParams.toString()}`
  const response = await apiFetch(url)
  const data: APIResponse<EventListResponse> = await response.json()
  return data.result
}

export async function fetchLineageGraph(snapshotId: string): Promise<LineageGraph> {
  const response = await apiFetch(`${API_BASE}/lineage/graph/${encodeURIComponent(snapshotId)}`)
  const data: APIResponse<LineageGraph> = await response.json()
  return data.result
}
