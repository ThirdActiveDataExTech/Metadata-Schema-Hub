import { useState, useRef, useCallback, useEffect } from 'react'
import type { AgentSSEEvent } from '../api/sse'

interface AgentStreamState {
  events: AgentSSEEvent[]
  isRunning: boolean
  sidebarVisible: boolean
  error: string | null
}

export function useAgentStream() {
  const [state, setState] = useState<AgentStreamState>({
    events: [],
    isRunning: false,
    sidebarVisible: false,
    error: null,
  })
  const abortRef = useRef<AbortController | null>(null)
  const resolveRef = useRef<((event: AgentSSEEvent | null) => void) | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const start = useCallback(
    (streamFn: (signal: AbortSignal) => Promise<void>): Promise<AgentSSEEvent | null> => {
      // Abort any previous stream
      abortRef.current?.abort()

      const controller = new AbortController()
      abortRef.current = controller

      setState({
        events: [],
        isRunning: true,
        sidebarVisible: true,
        error: null,
      })

      return new Promise<AgentSSEEvent | null>((resolve) => {
        resolveRef.current = resolve
        streamFn(controller.signal).finally(() => {
          setState((prev) => ({ ...prev, isRunning: false }))
          if (resolveRef.current === resolve) {
            resolveRef.current = null
          }
        })
      })
    },
    [],
  )

  const addEvent = useCallback((event: AgentSSEEvent) => {
    setState((prev) => ({ ...prev, events: [...prev.events, event] }))
    if (event.type === 'final_response' && resolveRef.current) {
      resolveRef.current(event)
      resolveRef.current = null
    }
  }, [])

  const setError = useCallback((error: string) => {
    setState((prev) => ({ ...prev, error, isRunning: false }))
    if (resolveRef.current) {
      resolveRef.current(null)
      resolveRef.current = null
    }
  }, [])

  const onComplete = useCallback(() => {
    setState((prev) => ({ ...prev, isRunning: false }))
  }, [])

  const openSidebar = useCallback(() => {
    setState((prev) => ({ ...prev, sidebarVisible: true }))
  }, [])

  const closeSidebar = useCallback(() => {
    setState((prev) => ({ ...prev, sidebarVisible: false }))
  }, [])

  const abort = useCallback(() => {
    abortRef.current?.abort()
    setState((prev) => ({ ...prev, isRunning: false }))
  }, [])

  return {
    ...state,
    start,
    addEvent,
    setError,
    onComplete,
    openSidebar,
    closeSidebar,
    abort,
  }
}
