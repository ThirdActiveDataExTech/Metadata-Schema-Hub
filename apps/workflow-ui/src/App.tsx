import { useState, useEffect, useCallback } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  MarkerType,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { fetchLineageEvents, fetchLineageGraph } from './api'
import type { LineageEvent, LineageGraph } from './types'

function App() {
  const [events, setEvents] = useState<LineageEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [searchId, setSearchId] = useState('')
  const [selectedSnapshot, setSelectedSnapshot] = useState<string | null>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])

  // Load recent events on mount
  useEffect(() => {
    loadEvents()
  }, [])

  const loadEvents = async () => {
    setLoading(true)
    try {
      const data = await fetchLineageEvents({ limit: 50 })
      setEvents(data.events)
    } catch (err) {
      console.error('Failed to load events:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadGraph = useCallback(async (snapshotId: string) => {
    setLoading(true)
    setSelectedSnapshot(snapshotId)
    try {
      const graph = await fetchLineageGraph(snapshotId)
      const { flowNodes, flowEdges } = convertToFlowGraph(graph)
      setNodes(flowNodes)
      setEdges(flowEdges)
    } catch (err) {
      console.error('Failed to load graph:', err)
    } finally {
      setLoading(false)
    }
  }, [setNodes, setEdges])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (searchId.trim()) {
      await loadGraph(searchId.trim())
    }
  }

  const handleEventClick = (event: LineageEvent) => {
    if (event.snapshotId) {
      setSearchId(event.snapshotId)
      loadGraph(event.snapshotId)
    }
  }

  // Group events by snapshot for sidebar
  const groupedSnapshots = events.reduce((acc, event) => {
    if (event.snapshotId) {
      if (!acc[event.snapshotId]) {
        acc[event.snapshotId] = []
      }
      acc[event.snapshotId].push(event)
    }
    return acc
  }, {} as Record<string, LineageEvent[]>)

  return (
    <div className="app">
      <header className="header">
        <h1>Workflow Lineage Viewer</h1>
        <form className="search-form" onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Enter snapshot ID..."
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>
      </header>

      <div className="main-content">
        <aside className="sidebar">
          <h2>Recent Snapshots</h2>
          {loading && !events.length ? (
            <div className="loading">Loading...</div>
          ) : (
            <div className="event-list">
              {Object.entries(groupedSnapshots).map(([snapshotId, snapEvents]) => {
                const latestEvent = snapEvents[0]
                const filename = snapEvents.find(e => e.filename)?.filename
                return (
                  <div
                    key={snapshotId}
                    className={`event-item ${selectedSnapshot === snapshotId ? 'selected' : ''}`}
                    onClick={() => handleEventClick(latestEvent)}
                  >
                    {filename && <div className="filename">{filename}</div>}
                    <div className="job-name">{snapshotId.slice(0, 16)}...</div>
                    <span className={`event-type ${latestEvent.eventType}`}>
                      {latestEvent.eventType}
                    </span>
                    <div className="event-time">
                      {snapEvents.length} event(s) • {new Date(latestEvent.eventTime).toLocaleString()}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </aside>

        <div className="graph-container">
          {nodes.length > 0 ? (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              fitView
              fitViewOptions={{ padding: 0.2 }}
            >
              <Background />
              <Controls />
              <MiniMap />
            </ReactFlow>
          ) : (
            <div className="empty-state">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
              </svg>
              <p>Select a snapshot from the sidebar or search by ID</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function convertToFlowGraph(graph: LineageGraph): { flowNodes: Node[]; flowEdges: Edge[] } {
  const flowNodes: Node[] = []
  const flowEdges: Edge[] = []
  const nodeSet = new Set<string>()

  // Position calculation
  let runY = 0
  const runX = 300
  const datasetPositions: Record<string, { x: number; y: number }> = {}
  let inputY = 0
  let outputY = 0

  // Add run nodes
  graph.nodes.forEach((node) => {
    const nodeType = node.job.includes('store')
      ? 'store-phase'
      : node.job.includes('publish')
        ? 'publish'
        : node.job.includes('discard')
          ? 'discard'
          : 'draft-phase'

    const details: string[] = []
    if (node.filename) details.push(node.filename)
    if (node.draftId) details.push(`Draft #${node.draftId}`)
    if (node.catalogEntryId) details.push(`Entry #${node.catalogEntryId}`)

    flowNodes.push({
      id: node.id,
      position: { x: runX, y: runY },
      data: {
        label: (
          <div className={`workflow-node ${nodeType}`}>
            <div className="node-label">{node.job.split('.').pop()}</div>
            <div className="node-type">{node.eventType} • {new Date(node.eventTime).toLocaleTimeString()}</div>
            {details.length > 0 && <div className="node-details">{details.join(' • ')}</div>}
          </div>
        ),
      },
      type: 'default',
    })
    nodeSet.add(node.id)
    runY += 120
  })

  // Add dataset nodes from edges
  graph.edges.forEach((edge) => {
    const datasetId = edge.type === 'input' ? edge.source : edge.target

    if (!nodeSet.has(datasetId) && datasetId.includes('/')) {
      const isInput = edge.type === 'input'
      const x = isInput ? 50 : 550
      const y = isInput ? inputY : outputY

      if (isInput) inputY += 80
      else outputY += 80

      datasetPositions[datasetId] = { x, y }

      flowNodes.push({
        id: datasetId,
        position: { x, y },
        data: {
          label: (
            <div className="workflow-node dataset">
              <div className="node-label">{datasetId.split('/').pop()}</div>
              <div className="node-type">{isInput ? 'Input' : 'Output'}</div>
            </div>
          ),
        },
        type: 'default',
      })
      nodeSet.add(datasetId)
    }

    flowEdges.push({
      id: `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: edge.type === 'input' ? '#48bb78' : '#4299e1' },
      animated: edge.type === 'output',
    })
  })

  return { flowNodes, flowEdges }
}

export default App
