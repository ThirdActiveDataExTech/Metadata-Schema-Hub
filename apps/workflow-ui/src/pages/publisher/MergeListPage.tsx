import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { listMerges } from '../../api'
import { StatusBadge, Pagination } from '../../components'
import type { MergeDetail } from '../../types'

export default function MergeListPage() {
  const [merges, setMerges] = useState<MergeDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [limit] = useState(20)
  const [offset, setOffset] = useState(0)

  useEffect(() => {
    loadMerges()
  }, [offset])

  const loadMerges = async () => {
    setLoading(true)
    try {
      const result = await listMerges({ limit, offset })
      setMerges(result.merges)
      setTotal(result.total)
    } catch (err) {
      console.error('Failed to load merges:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatScore = (score: number) => `${(score * 100).toFixed(1)}%`

  return (
    <div className="page merge-list-page">
      <div className="page-header">
        <h1>Merge Review</h1>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Draft ID</th>
                <th>Target Entry</th>
                <th>Score</th>
                <th>Decision</th>
                <th>Decided By</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {merges.length === 0 ? (
                <tr>
                  <td colSpan={8} className="empty-row">No merges found</td>
                </tr>
              ) : (
                merges.map(merge => (
                  <tr key={merge.id}>
                    <td>{merge.id}</td>
                    <td>
                      <Link to={`/admin/drafts/${merge.draft_id}`} className="link">
                        #{merge.draft_id}
                      </Link>
                    </td>
                    <td>
                      {merge.target_entry_id ? (
                        <Link to={`/catalog/${merge.target_entry_id}`} className="link">
                          #{merge.target_entry_id}
                        </Link>
                      ) : (
                        <span className="empty">New entry</span>
                      )}
                    </td>
                    <td>
                      <span className={`score-text ${merge.mapping_score >= 0.9 ? 'high' : merge.mapping_score >= 0.5 ? 'medium' : 'low'}`}>
                        {formatScore(merge.mapping_score)}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={merge.decision} />
                    </td>
                    <td>{merge.decided_by || '-'}</td>
                    <td>{new Date(merge.created_at).toLocaleString()}</td>
                    <td>
                      <Link to={`/admin/merges/${merge.id}`} className="btn btn-sm btn-secondary">
                        {merge.decision === 'PENDING' ? 'Review' : 'View'}
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
