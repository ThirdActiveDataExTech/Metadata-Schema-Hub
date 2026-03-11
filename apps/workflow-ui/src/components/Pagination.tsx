interface PaginationProps {
  total: number
  limit: number
  offset: number
  onPageChange: (offset: number) => void
}

export default function Pagination({ total, limit, offset, onPageChange }: PaginationProps) {
  const currentPage = Math.floor(offset / limit) + 1
  const totalPages = Math.ceil(total / limit)

  if (totalPages <= 1) return null

  return (
    <div className="pagination">
      <button
        className="pagination-btn"
        onClick={() => onPageChange(Math.max(0, offset - limit))}
        disabled={offset === 0}
      >
        Previous
      </button>
      <span className="pagination-info">
        Page {currentPage} of {totalPages}
      </span>
      <button
        className="pagination-btn"
        onClick={() => onPageChange(offset + limit)}
        disabled={offset + limit >= total}
      >
        Next
      </button>
    </div>
  )
}
