import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { listIngestionRuns, createDraft } from '../../api'
import { StatusBadge, Pagination } from '../../components'
import type { IngestionRun } from '../../types'

export default function IngestionRunsPage() {
  const navigate = useNavigate()
  const [runs, setRuns] = useState<IngestionRun[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [stateFilter, setStateFilter] = useState<string>('')
  const [limit] = useState(20)
  const [offset, setOffset] = useState(0)
  const [creatingDraft, setCreatingDraft] = useState<number | null>(null)

  useEffect(() => {
    loadRuns()
  }, [stateFilter, offset])

  const loadRuns = async () => {
    setLoading(true)
    try {
      const result = await listIngestionRuns({
        state: stateFilter || undefined,
        limit,
        offset,
      })
      setRuns(result.runs)
      setTotal(result.count)
    } catch (err) {
      console.error('Failed to load ingestion runs:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateDraft = async (runId: number) => {
    setCreatingDraft(runId)
    try {
      const result = await createDraft(runId)
      navigate(`/admin/drafts/${result.draft.id}`)
    } catch (err) {
      console.error('Failed to create draft:', err)
      alert(err instanceof Error ? err.message : 'Failed to create draft')
    } finally {
      setCreatingDraft(null)
    }
  }

  return (
    <div className="page ingestion-runs-page">
      <div className="page-header">
        <h1>Ingestion Runs</h1>
        <Link to="/admin/upload" className="btn btn-primary">
          New Upload
        </Link>
      </div>

      <div className="filter-bar">
        <label>
          State:
          <select
            value={stateFilter}
            onChange={(e) => {
              setStateFilter(e.target.value)
              setOffset(0)
            }}
          >
            <option value="">All</option>
            <option value="STORED">STORED</option>
            <option value="DRAFTED">DRAFTED</option>
            <option value="FAILED">FAILED</option>
          </select>
        </label>
      </div>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Snapshot ID</th>
                <th>State</th>
                <th>Draft ID</th>
                <th>Created At</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty-row">No ingestion runs found</td>
                </tr>
              ) : (
                runs.map(run => (
                  <tr key={run.run_id}>
                    <td>{run.run_id}</td>
                    <td>
                      <code className="snapshot-id">{run.snapshot_id.slice(0, 16)}...</code>
                    </td>
                    <td>
                      <StatusBadge status={run.state} />
                    </td>
                    <td>
                      {run.draft_id ? (
                        <Link to={`/admin/drafts/${run.draft_id}`}>#{run.draft_id}</Link>
                      ) : '-'}
                    </td>
                    <td>{new Date(run.created_at).toLocaleString()}</td>
                    <td>
                      {run.state === 'STORED' && (
                        <button
                          onClick={() => handleCreateDraft(run.run_id)}
                          disabled={creatingDraft === run.run_id}
                          className="btn btn-sm btn-primary"
                        >
                          {creatingDraft === run.run_id ? 'Creating...' : 'Create Draft'}
                        </button>
                      )}
                      {run.state === 'FAILED' && run.error && (
                        <span className="error-text" title={run.error}>
                          Error
                        </span>
                      )}
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
