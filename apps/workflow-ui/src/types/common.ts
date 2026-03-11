export interface APIResponse<T> {
  code: string
  message: string
  result: T
  description: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}
