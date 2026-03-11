export interface LineageEvent {
  id: number
  eventTime: string | null
  eventType: 'START' | 'COMPLETE' | 'FAIL'
  jobName: string
  inputRefs: string[]
  outputRefs: string[]
  // Extracted context from refs
  snapshotId: string | null
  draftId: number | null
  catalogEntryId: number | null
  filename: string | null
  errorMessage: string | null
}

export interface LineageGraph {
  snapshotId?: string
  entityId?: string
  nodes: GraphNode[]
  edges: GraphEdge[]
  eventCount: number
}

// Union type for graph nodes - can be run or dataset
export interface GraphNode {
  id: string
  type: 'run' | 'dataset'
  // Run node fields
  job?: string
  eventType?: string
  eventTime?: string
  draftId?: number | null
  catalogEntryId?: number | null
  filename?: string | null
  // Dataset node fields
  name?: string
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

// Type guards for node types
export function isRunNode(node: GraphNode): node is GraphNode & { type: 'run' } {
  return node.type === 'run'
}

export function isDatasetNode(node: GraphNode): node is GraphNode & { type: 'dataset' } {
  return node.type === 'dataset'
}
