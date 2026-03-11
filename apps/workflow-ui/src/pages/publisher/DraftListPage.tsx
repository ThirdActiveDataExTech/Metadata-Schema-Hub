import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listDrafts } from '../../api'
import { StatusBadge, Pagination } from '../../components'
import type { DraftSummary } from '../../types'

export default function DraftListPage() {
  const [drafts, setDrafts] = useState<DraftSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [limit] = useState(20)
  const [offset, setOffset] = useState(0)

  useEffect(() => {
    loadDrafts()
  }, [offset])

  const loadDrafts = async () => {
    setLoading(true)
    try {
      const result = await listDrafts({ limit, offset })
      setDrafts(result.drafts)
      setTotal(result.count)
    } catch (err) {
      console.error('Failed to load drafts:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page draft-list-page">
      <div className="page-header">
        <h1>Draft Review</h1>
        <Link to="/admin/upload" className="btn btn-primary">
          New Upload
        </Link>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Status</th>
                <th>Snapshot ID</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {drafts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty-row">No drafts found</td>
                </tr>
              ) : (
                drafts.map(draft => (
                  <tr key={draft.id}>
                    <td>{draft.id}</td>
                    <td>{draft.title || '(No title)'}</td>
                    <td>
                      <StatusBadge status={draft.status} />
                    </td>
                    <td>
                      <code className="snapshot-id">{draft.snapshot_id.slice(0, 16)}...</code>
                    </td>
                    <td>{new Date(draft.created_at).toLocaleString()}</td>
                    <td>
                      <Link to={`/admin/drafts/${draft.id}`} className="btn btn-sm btn-secondary">
                        {draft.status === 'PENDING' ? 'Review' : 'View'}
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          <Pagination
            total={total}
            limit={limit}
            offset={offset}
            onPageChange={setOffset}
          />
        </>
      )}
    </div>
  )
}
