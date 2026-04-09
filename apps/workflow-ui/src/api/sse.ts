import { apiFetch } from './common'

export interface AgentSSEEvent {
  type: 'node_complete' | 'final_response' | 'error'
  node: string | null
  data: Record<string, unknown>
  timestamp?: string
}

export type SSEEventHandler = (event: AgentSSEEvent) => void

/**
 * Consume SSE events from a POST endpoint using native fetch + ReadableStream.
 * No external dependencies required.
 */
export async function streamAgentSSE(
  url: string,
  options: {
    onEvent: SSEEventHandler
    onComplete: () => void
    onError: (error: string) => void
    signal?: AbortSignal
  },
): Promise<void> {
  const { onEvent, onComplete, onError, signal } = options

  let response: Response
  try {
    response = await apiFetch(url, { method: 'POST', signal })
  } catch (err) {
    if (signal?.aborted) return
    onError(err instanceof Error ? err.message : 'Failed to connect')
    return
  }

  if (!response.ok) {
    try {
      const error = await response.json()
      onError(error.detail || error.message || `HTTP ${response.status}`)
    } catch {
      onError(`HTTP ${response.status}`)
    }
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    onError('No response body')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // Split on double newline (SSE frame delimiter)
      while (buffer.includes('\n\n')) {
        const idx = buffer.indexOf('\n\n')
        const frame = buffer.slice(0, idx)
        buffer = buffer.slice(idx + 2)

        // Parse SSE frame: extract data: lines
        const lines = frame.split('\n')
        let dataStr = ''
        for (const line of lines) {
          if (line.startsWith('data:')) {
            dataStr += line.slice(5).trim()
          }
        }

        if (dataStr) {
          try {
            const event: AgentSSEEvent = JSON.parse(dataStr)
            onEvent(event)
          } catch {
            // Skip unparseable frames
          }
        }
      }
    }
    onComplete()
  } catch (err) {
    if (signal?.aborted) return
    onError(err instanceof Error ? err.message : 'Stream read error')
  }
}
