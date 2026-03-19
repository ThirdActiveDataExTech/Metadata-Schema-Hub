// Runtime config from window.__ENV__ (injected at container startup)
// Fallback to Vite env for local dev, then to defaults
declare global {
  interface Window {
    __ENV__?: {
      CATALOG_SERVICE_URL?: string
      INGESTION_SERVICE_URL?: string
      API_TOKEN?: string
    }
  }
}

const getEnv = (key: string, fallback: string): string => {
  const runtimeValue = window.__ENV__?.[key as keyof typeof window.__ENV__]
  // Skip placeholder values (not replaced by envsubst)
  if (runtimeValue && !runtimeValue.startsWith('${')) {
    return runtimeValue
  }
  return fallback
}

// API Base URLs
export const CATALOG_SERVICE_URL = getEnv('CATALOG_SERVICE_URL', import.meta.env.VITE_CATALOG_SERVICE_URL || 'http://localhost:8084')
export const INGESTION_SERVICE_URL = getEnv('INGESTION_SERVICE_URL', import.meta.env.VITE_INGESTION_SERVICE_URL || 'http://localhost:8085')

// Common fetch wrapper with X-Token header
const API_TOKEN = getEnv('API_TOKEN', import.meta.env.VITE_API_TOKEN || 'wisenut')

export async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  return fetch(url, {
    ...options,
    headers: {
      'X-Token': API_TOKEN,
      ...options?.headers,
    },
  })
}
