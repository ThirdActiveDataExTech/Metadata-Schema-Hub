// Common fetch wrapper with X-Token header
const API_TOKEN = import.meta.env.VITE_API_TOKEN || 'wisenut'

export async function apiFetch(url: string, options?: RequestInit): Promise<Response> {
  return fetch(url, {
    ...options,
    headers: {
      'X-Token': API_TOKEN,
      ...options?.headers,
    },
  })
}
