import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getMerge, approveMerge, rejectMerge, getDraft } from '../../api'
import { StatusBadge, TagList } from '../../components'
import type { MergeDetail, DraftDetail } from '../../types'

const AUTO_PUBLISH_THRESHOLD = 0.90

export default function MergeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [merge, setMerge] = useState<MergeDetail | null>(null)
  const [draft, setDraft] = useState<DraftDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [approving, setApproving] = useState(false)
  const [rejecting, setRejecting] = useState(false)
  const [catalogEntryId, setCatalogEntryId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (id) loadData(Number(id))
  }, [id])

  const loadData = async (mergeId: number) => {
    setLoading(true)
    try {
      const mergeData = await getMerge(mergeId)
      setMerge(mergeData)
      // Load linked draft
      try {
        const draftData = await getDraft(mergeData.draft_id)
        setDraft(draftData)
      } catch {
        // Draft may not be accessible via catalog service
      }
    } catch (err) {
      console.error('Failed to load merge:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async () => {
    if (!merge) return
    const decidedBy = prompt('Enter your user ID for approval:')
    if (!decidedBy) return

    setApproving(true)
    setError(null)
    try {
      const updated = await approveMerge(merge.id, decidedBy)
      setCatalogEntryId(updated.catalog_entry_id ?? null)
      setMerge(updated)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve')
    } finally {
      setApproving(false)
    }
  }

  const handleReject = async () => {
    if (!merge || !confirm('Are you sure you want to reject this merge?')) return
    const decidedBy = prompt('Enter your user ID for rejection:')
    if (!decidedBy) return

    setRejecting(true)
    setError(null)
    try {
      const updated = await rejectMerge(merge.id, decidedBy)
      setMerge(updated)
      alert('Merge rejected')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject')
    } finally {
      setRejecting(false)
    }
  }

  const formatScore = (score: number) => `${(score * 100).toFixed(1)}%`

  if (loading) {
    return <div className="page"><div className="loading">Loading...</div></div>
  }

  if (!merge) {
    return (
      <div className="page">
        <div className="error-state">
          <p>Merge not found</p>
          <Link to="/admin/merges" className="btn btn-secondary">Back to Merges</Link>
        </div>
      </div>
    )
  }

  const isPending = merge.decision === 'PENDING'
  const evidence = merge.merge_evidence

  return (
    <div className="page merge-detail-page">
      <div className="page-header">
        <Link to="/admin/merges" className="back-link">Back to Merges</Link>
        <div className="header-actions">
          {isPending && (
            <>
              <button
                onClick={handleReject}
                disabled={rejecting}
                className="btn btn-danger"
              >
                {rejecting ? 'Rejecting...' : 'Reject'}
              </button>
              <button
                onClick={handleApprove}
                disabled={approving}
                className="btn btn-primary"
              >
                {approving ? 'Approving...' : 'Approve'}
              </button>
            </>
          )}
          {catalogEntryId && (
            <Link to={`/catalog/${catalogEntryId}`} className="btn btn-success">
              View Catalog Entry #{catalogEntryId}
            </Link>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="merge-detail">
        <div className="merge-header">
          <h1>Merge #{merge.id}</h1>
          <StatusBadge status={merge.decision} />
        </div>

        <div className="merge-two-column">
          {/* Left: Merge Info */}
          <div className="merge-column">
            <h2>Merge Information</h2>

            {/* Score */}
            <div className="merge-score-section">
              <div className="score-label">Mapping Score</div>
              <div className="score-display">
                <div className="score-bar-container">
                  <div
                    className={`score-bar-fill ${merge.mapping_score >= AUTO_PUBLISH_THRESHOLD ? 'above-threshold' : 'below-threshold'}`}
                    style={{ width: `${Math.min(merge.mapping_score * 100, 100)}%` }}
                  />
                  <div className="threshold-line" style={{ left: `${AUTO_PUBLISH_THRESHOLD * 100}%` }} />
                </div>
                <div className="score-values">
                  <span className={`score-text ${merge.mapping_score >= AUTO_PUBLISH_THRESHOLD ? 'high' : 'low'}`}>
                    {formatScore(merge.mapping_score)}
                  </span>
                  <span className="threshold-label">Threshold: {formatScore(AUTO_PUBLISH_THRESHOLD)}</span>
                </div>
              </div>
            </div>

            {/* Evidence */}
            <div className="merge-evidence-section">
              <h3>Entity Match Evidence</h3>

              <div className="evidence-field">
                <span className="evidence-label">Searched External IDs</span>
                {evidence.searched_external_ids.length > 0 ? (
                  <TagList items={evidence.searched_external_ids} variant="external-id" />
                ) : (
                  <span className="empty">None</span>
                )}
              </div>

              <div className="evidence-field">
                <span className="evidence-label">Candidates ({evidence.candidates.length})</span>
                {evidence.candidates.length > 0 ? (
                  <div className="merge-candidates-list">
                    {evidence.candidates.map((c, i) => (
                      <div key={i} className={`merge-candidate-item ${evidence.recommended?.entry_id === c.entry_id ? 'is-recommended' : ''} ${evidence.decided?.entry_id === c.entry_id ? 'is-decided' : ''}`}>
                        <div className="candidate-header">
                          <Link to={`/catalog/${c.entry_id}`} className="link">
                            Entry #{c.entry_id}
                          </Link>
                          {evidence.recommended?.entry_id === c.entry_id && <span className="badge recommended">Recommended</span>}
                          {evidence.decided?.entry_id === c.entry_id && <span className="badge decided">Decided</span>}
                        </div>
                        <div className="candidate-overlap">
                          Overlap: {c.overlap_ids.join(', ')}
                        </div>
                        {c.updated_at && (
                          <div className="candidate-date">
                            Updated: {new Date(c.updated_at).toLocaleString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="empty">No matching entries found (new entity)</span>
                )}
              </div>

              {evidence.decided && (
                <div className="evidence-field">
                  <span className="evidence-label">Decision</span>
                  <div className="decided-info">
                    Target: Entry #{evidence.decided.entry_id} | By: {evidence.decided.decided_by}
                  </div>
                </div>
              )}
            </div>

            {/* Metadata */}
            <div className="merge-meta">
              <dl>
                <dt>Decision</dt>
                <dd><StatusBadge status={merge.decision} /></dd>
                <dt>Decided By</dt>
                <dd>{merge.decided_by || '-'}</dd>
                <dt>Decided At</dt>
                <dd>{merge.decided_at ? new Date(merge.decided_at).toLocaleString() : '-'}</dd>
                <dt>Target Entry</dt>
                <dd>
                  {merge.target_entry_id ? (
                    <Link to={`/catalog/${merge.target_entry_id}`} className="link">#{merge.target_entry_id}</Link>
                  ) : 'New entry'}
                </dd>
                <dt>Created At</dt>
                <dd>{new Date(merge.created_at).toLocaleString()}</dd>
              </dl>
            </div>
          </div>

          {/* Right: Linked Draft */}
          <div className="merge-column">
            <h2>Linked Draft</h2>
            {draft ? (
              <div className="linked-draft-card">
                <div className="draft-card-header">
                  <Link to={`/admin/drafts/${draft.id}`} className="link">
                    Draft #{draft.id}
                  </Link>
                  <StatusBadge status={draft.status} />
                </div>
                <div className="draft-card-body">
                  <dl>
                    <dt>Title</dt>
                    <dd>{draft.title || '(No title)'}</dd>
                    <dt>Description</dt>
                    <dd className="description-text">{draft.description || '-'}</dd>
                    <dt>Publisher</dt>
                    <dd>{draft.publisher || '-'}</dd>
                    <dt>Issued</dt>
                    <dd>{draft.issued || '-'}</dd>
                    <dt>Modified</dt>
                    <dd>{draft.modified || '-'}</dd>
                    {draft.keyword && draft.keyword.length > 0 && (
                      <>
                        <dt>Keywords</dt>
                        <dd><TagList items={draft.keyword} variant="keyword" /></dd>
                      </>
                    )}
                    {draft.theme && draft.theme.length > 0 && (
                      <>
                        <dt>Theme</dt>
                        <dd><TagList items={draft.theme} variant="theme" /></dd>
                      </>
                    )}
                    {draft.external_ids && draft.external_ids.length > 0 && (
                      <>
                        <dt>External IDs</dt>
                        <dd><TagList items={draft.external_ids} variant="external-id" /></dd>
                      </>
                    )}
                    <dt>Snapshot ID</dt>
                    <dd><code className="snapshot-id">{draft.snapshot_id}</code></dd>
                  </dl>
                </div>
              </div>
            ) : (
              <div className="linked-draft-card">
                <p>
                  Draft #{merge.draft_id} —{' '}
                  <Link to={`/admin/drafts/${merge.draft_id}`} className="link">View Draft</Link>
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
