import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getDraft, publishDraft, discardDraft } from '../../api'
import { StatusBadge } from '../../components'
import type { DraftDetail, MappingCandidate } from '../../types'

export default function DraftDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [draft, setDraft] = useState<DraftDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [publishing, setPublishing] = useState(false)
  const [discarding, setDiscarding] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      loadDraft(Number(id))
    }
  }, [id])

  const loadDraft = async (draftId: number) => {
    setLoading(true)
    try {
      const data = await getDraft(draftId)
      setDraft(data)
    } catch (err) {
      console.error('Failed to load draft:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePublish = async () => {
    if (!id || !confirm('Are you sure you want to publish this draft?')) return

    setPublishing(true)
    setError(null)

    try {
      const result = await publishDraft(Number(id))
      alert(`Published successfully! Catalog Entry ID: ${result.catalog_entry_id}`)
      navigate(`/catalog/${result.catalog_entry_id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to publish')
    } finally {
      setPublishing(false)
    }
  }

  const handleDiscard = async () => {
    if (!id || !confirm('Are you sure you want to discard this draft?')) return

    setDiscarding(true)
    setError(null)

    try {
      await discardDraft(Number(id))
      alert('Draft discarded')
      navigate('/admin/drafts')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to discard')
    } finally {
      setDiscarding(false)
    }
  }

  if (loading) {
    return <div className="page"><div className="loading">Loading...</div></div>
  }

  if (!draft) {
    return (
      <div className="page">
        <div className="error-state">
          <p>Draft not found</p>
          <Link to="/admin/drafts" className="btn btn-secondary">Back to Drafts</Link>
        </div>
      </div>
    )
  }

  const isPending = draft.status === 'PENDING'

  return (
    <div className="page draft-detail-page">
      <div className="page-header">
        <Link to="/admin/drafts" className="back-link">Back to Drafts</Link>
        {isPending && (
          <div className="header-actions">
            <button
              onClick={handleDiscard}
              disabled={discarding}
              className="btn btn-danger"
            >
              {discarding ? 'Discarding...' : 'Discard'}
            </button>
            <button
              onClick={handlePublish}
              disabled={publishing}
              className="btn btn-primary"
            >
              {publishing ? 'Publishing...' : 'Publish'}
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">{error}</div>
      )}

      <div className="draft-detail">
        <div className="draft-header">
          <h1>{draft.title || '(No title)'}</h1>
          <StatusBadge status={draft.status} />
        </div>

        <div className="draft-content">
          <div className="draft-fields">
            <h2>Mapped Fields</h2>
            <dl className="field-list">
              <dt>Title</dt>
              <dd>{draft.title || '-'}</dd>

              <dt>Description</dt>
              <dd>{draft.description || '-'}</dd>

              <dt>Publisher</dt>
              <dd>{draft.publisher || '-'}</dd>

              <dt>Issued</dt>
              <dd>{draft.issued || '-'}</dd>

              <dt>Modified</dt>
              <dd>{draft.modified || '-'}</dd>

              <dt>Keywords</dt>
              <dd>
                {draft.keyword?.length ? (
                  <div className="tag-list">
                    {draft.keyword.map((kw: string, i: number) => (
                      <span key={i} className="keyword-tag">{kw}</span>
                    ))}
                  </div>
                ) : '-'}
              </dd>

              <dt>Themes</dt>
              <dd>
                {draft.theme?.length ? (
                  <div className="tag-list">
                    {draft.theme.map((t: string, i: number) => (
                      <span key={i} className="theme-tag">{t}</span>
                    ))}
                  </div>
                ) : '-'}
              </dd>

              <dt>Landing Page</dt>
              <dd>{draft.landing_page || '-'}</dd>

              <dt>Access URL</dt>
              <dd>{draft.access_url || '-'}</dd>
            </dl>
          </div>

          <div className="mapping-evidence">
            <h2>Mapping Evidence</h2>
            {draft.mapping_evidence && Object.keys(draft.mapping_evidence).length > 0 ? (
              <div className="evidence-list">
                {Object.entries(draft.mapping_evidence).map(([field, evidence]: [string, { selected: MappingCandidate; alternatives: MappingCandidate[] }]) => (
                  <div key={field} className="evidence-item">
                    <h3>{field}</h3>
                    <div className="selected-mapping">
                      <span className="label">Selected:</span>
                      <span className="value">{evidence.selected?.value || '-'}</span>
                      <span className="source">
                        {evidence.selected?.metadata_column}
                        ({(evidence.selected?.correlation * 100).toFixed(0)}%)
                      </span>
                    </div>
                    {evidence.alternatives?.length > 0 && (
                      <div className="alternatives">
                        <span className="label">Alternatives:</span>
                        <ul>
                          {evidence.alternatives.map((alt: MappingCandidate, i: number) => (
                            <li key={i}>
                              <span className="value">{alt.value || '(empty)'}</span>
                              <span className="source">
                                {alt.metadata_column} ({(alt.correlation * 100).toFixed(0)}%)
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-evidence">No mapping evidence available</p>
            )}
          </div>
        </div>

        <div className="draft-meta">
          <dl>
            <dt>Snapshot ID</dt>
            <dd>
              <Link to={`/admin/lineage?snapshot=${draft.snapshot_id}`}>
                <code>{draft.snapshot_id}</code>
              </Link>
            </dd>

            <dt>Mapping Version</dt>
            <dd>{draft.mapping_version}</dd>

            <dt>Created At</dt>
            <dd>{new Date(draft.created_at).toLocaleString()}</dd>

            <dt>Updated At</dt>
            <dd>{new Date(draft.updated_at).toLocaleString()}</dd>
          </dl>
        </div>
      </div>
    </div>
  )
}
