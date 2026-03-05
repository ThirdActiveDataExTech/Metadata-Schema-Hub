export interface LineageEvent {
  id: number
  eventTime: string
  eventType: 'START' | 'COMPLETE' | 'FAIL'
  runId: string
  jobName: string
  jobNamespace: string
  snapshotId: string | null
  draftId: number | null
  catalogEntryId: number | null
  ingestionRunId: number | null
  filename: string | null
}

export interface LineageGraph {
  snapshotId: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  eventCount: number
}

export interface GraphNode {
  id: string
  type: string
  job: string
  eventType: string
  eventTime: string
  draftId: number | null
  catalogEntryId: number | null
  filename: string | null
}

export interface GraphEdge {
  source: string
  target: string
  type: 'input' | 'output'
}

export interface EventListResponse {
  events: LineageEvent[]
  total: number
  limit: number
  offset: number
}
