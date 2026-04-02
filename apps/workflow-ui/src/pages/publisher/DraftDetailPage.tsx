import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getDraft, discardDraft, getMetadataOptions, updateDraftFields, getMergeByDraft, executeMergePhase } from '../../api'
import { StatusBadge, TagList } from '../../components'
import type { DraftDetail, MetadataEntryOption, MappingCandidate } from '../../types'

const EDITABLE_FIELDS = [
  'title', 'description', 'publisher', 'issued', 'modified',
  'keyword', 'theme', 'landing_page', 'access_url', 'external_ids'
] as const

type EditableField = typeof EDITABLE_FIELDS[number]

export default function DraftDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [draft, setDraft] = useState<DraftDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [discarding, setDiscarding] = useState(false)
  const [creatingMerge, setCreatingMerge] = useState(false)
  const [mergeId, setMergeId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Edit mode state
  const [isEditing, setIsEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [metadataOptions, setMetadataOptions] = useState<MetadataEntryOption[]>([])
  const [fieldSelections, setFieldSelections] = useState<Record<string, string>>({})
  const [activeField, setActiveField] = useState<string | null>(null)

  useEffect(() => {
    if (id) {
      loadDraftAndMetadata(Number(id))
    }
  }, [id])

  const loadDraftAndMetadata = async (draftId: number) => {
    setLoading(true)
    try {
      // Load draft and metadata options in parallel
      const [draftData, options] = await Promise.all([
        getDraft(draftId),
        getMetadataOptions(draftId)
      ])
      setDraft(draftData)
      setMetadataOptions(options)
      // Load linked merge
      try {
        const mergeData = await getMergeByDraft(draftId)
        setMergeId(mergeData.id)
      } catch {
        // Merge may not exist yet
      }
    } catch (err) {
      console.error('Failed to load draft:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleEditStart = () => {
    setFieldSelections({})
    setActiveField(null)
    setIsEditing(true)
  }

  const handleEditCancel = () => {
    setIsEditing(false)
    setFieldSelections({})
    setActiveField(null)
    setError(null)
  }

  const handleFieldClick = (field: string) => {
    // All fields are clickable in both view and edit mode
    setActiveField(activeField === field ? null : field)
  }

  const handleMetadataSelect = (metadataSchema: string) => {
    if (!activeField) return
    setFieldSelections(prev => ({ ...prev, [activeField]: metadataSchema }))
  }

  const handleClearSelection = (field: string) => {
    setFieldSelections(prev => {
      const updated = { ...prev }
      delete updated[field]
      return updated
    })
  }

  const handleSave = async () => {
    if (!id || Object.keys(fieldSelections).length === 0) return

    setSaving(true)
    setError(null)

    try {
      const updates = Object.entries(fieldSelections).map(([catalog_field, metadata_schema]) => ({
        catalog_field,
        metadata_schema,
      }))

      const updatedDraft = await updateDraftFields(Number(id), { updates })
      setDraft(updatedDraft)
      setIsEditing(false)
      setFieldSelections({})
      setActiveField(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save')
    } finally {
      setSaving(false)
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

  const handleSendToMerge = async () => {
    if (!id) return

    setCreatingMerge(true)
    setError(null)
    try {
      const result = await executeMergePhase(Number(id))
      setMergeId(result.merge.id)
      navigate(`/admin/merges/${result.merge.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create merge')
    } finally {
      setCreatingMerge(false)
    }
  }

  const getFieldValue = (field: EditableField): string => {
    if (!draft) return '-'
    const value = draft[field]
    if (Array.isArray(value)) return value.join(', ') || '-'
    return value || '-'
  }

  const isFieldModified = (field: string): boolean => {
    if (!draft?.mapping_evidence?.[field]) return false
    const evidence = draft.mapping_evidence[field]
    return evidence.decided?.metadata_column !== evidence.recommended?.metadata_column
  }

  const getCorrelationForSchema = (field: string | null, schema: string): number | null => {
    if (!field || !draft?.mapping_evidence?.[field]) return null
    const candidates = draft.mapping_evidence[field].candidates || []
    const candidate = candidates.find(c => c.metadata_column === schema)
    return candidate?.correlation ?? null
  }

  const isCandidate = (field: string, schema: string): boolean => {
    if (!draft?.mapping_evidence?.[field]) return false
    const candidates = draft.mapping_evidence[field].candidates || []
    return candidates.some(c => c.metadata_column === schema)
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
            {isEditing ? (
              <>
                <button onClick={handleEditCancel} className="btn btn-secondary">
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || Object.keys(fieldSelections).length === 0}
                  className="btn btn-primary"
                >
                  {saving ? 'Saving...' : `Save (${Object.keys(fieldSelections).length} changes)`}
                </button>
              </>
            ) : (
              <>
                <button onClick={handleEditStart} className="btn btn-secondary">
                  Edit
                </button>
                <button
                  onClick={handleDiscard}
                  disabled={discarding}
                  className="btn btn-danger"
                >
                  {discarding ? 'Discarding...' : 'Discard'}
                </button>
                {mergeId ? (
                  <Link to={`/admin/merges/${mergeId}`} className="btn btn-primary">
                    Merge Review
                  </Link>
                ) : (
                  <button
                    onClick={handleSendToMerge}
                    disabled={creatingMerge}
                    className="btn btn-primary"
                  >
                    {creatingMerge ? 'Creating Merge...' : 'Send to Merge'}
                  </button>
                )}
              </>
            )}
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

        {/* 3-Column Layout */}
        <div className="draft-three-column">
          {/* Column 1: Mapped Fields */}
          <div className="draft-column">
            <h2>Mapped Fields</h2>
            <div className="field-cards">
              {EDITABLE_FIELDS.map(field => {
                const evidence = draft.mapping_evidence?.[field]
                const pendingSelection = fieldSelections[field]
                const pendingValue = pendingSelection
                  ? metadataOptions.find(o => o.schema === pendingSelection)?.value
                  : null

                return (
                  <div
                    key={field}
                    className={`field-card clickable ${isEditing ? 'editable' : ''} ${activeField === field ? 'active' : ''} ${pendingSelection ? 'pending-change' : ''}`}
                    onClick={() => handleFieldClick(field)}
                  >
                    <div className="field-card-header">
                      <span className="field-name">
                        {field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                      </span>
                      {isFieldModified(field) && <span className="modified-badge">Modified</span>}
                      {pendingSelection && <span className="pending-badge">Pending</span>}
                    </div>
                    <div className="field-card-value">
                      {pendingSelection ? (
                        <>
                          <div className="pending-value">
                            <span className="label">New:</span>
                            <span className="value">{pendingValue || '-'}</span>
                            <button
                              className="clear-btn"
                              onClick={(e) => { e.stopPropagation(); handleClearSelection(field); }}
                            >
                              ×
                            </button>
                          </div>
                          <div className="current-value-small">
                            Current: {getFieldValue(field)}
                          </div>
                        </>
                      ) : (
                        field === 'keyword' || field === 'theme' || field === 'external_ids' ? (
                          <TagList
                            items={draft[field]}
                            variant={field === 'keyword' ? 'keyword' : field === 'theme' ? 'theme' : 'external-id'}
                          />
                        ) : (
                          <span className={getFieldValue(field) === '-' ? 'empty' : ''}>{getFieldValue(field)}</span>
                        )
                      )}
                    </div>
                    {evidence?.decided && (
                      <div className="field-card-source">
                        <span className="schema">{evidence.decided.metadata_column}</span>
                        {evidence.decided.correlation !== null && (
                          <span className="correlation"><span className="score">{(evidence.decided.correlation * 100).toFixed(0)}%</span></span>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Column 2: Mapping Evidence */}
          <div className="draft-column">
            <h2>Mapping Evidence {activeField && <span className="active-field-label">({activeField})</span>}</h2>
            {activeField && draft.mapping_evidence?.[activeField] ? (
              <div className="evidence-detail">
                {(() => {
                  const evidence = draft.mapping_evidence[activeField]
                  return (
                    <>
                      <div className="evidence-section">
                        <h3>Decided</h3>
                        <div className={`evidence-item-card ${evidence.decided?.out_of_candidates ? 'out-of-candidates' : ''}`}>
                          <div className="evidence-schema">{evidence.decided?.metadata_column}</div>
                          <div className="evidence-value">{evidence.decided?.value || '-'}</div>
                          <div className="evidence-meta">
                            {evidence.decided?.correlation !== null && (
                              <span className="correlation">Correlation <span className="score">{(evidence.decided.correlation * 100).toFixed(0)}%</span></span>
                            )}
                            {evidence.decided?.out_of_candidates && (
                              <span className="out-badge">Out of candidates</span>
                            )}
                          </div>
                        </div>
                      </div>

                      {evidence.recommended && (
                        <div className="evidence-section">
                          <h3>Recommended</h3>
                          <div className="evidence-item-card recommended">
                            <div className="evidence-schema">{evidence.recommended.metadata_column}</div>
                            <div className="evidence-value">{evidence.recommended.value || '-'}</div>
                            {evidence.recommended.correlation !== null && evidence.recommended.correlation !== undefined && (
                              <div className="evidence-meta">
                                <span className="correlation">Correlation <span className="score">{(evidence.recommended.correlation * 100).toFixed(0)}%</span></span>
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      <div className="evidence-section">
                        <h3>Candidates ({evidence.candidates?.length || 0})</h3>
                        <div className="candidates-list">
                          {evidence.candidates?.map((candidate: MappingCandidate, i: number) => (
                            <div
                              key={i}
                              className={`candidate-item ${candidate.metadata_column === evidence.decided?.metadata_column ? 'is-decided' : ''} ${candidate.metadata_column === evidence.recommended?.metadata_column ? 'is-recommended' : ''}`}
                            >
                              <div className="candidate-schema">{candidate.metadata_column}</div>
                              <div className="candidate-value">{candidate.value || '(empty)'}</div>
                              <div className="candidate-meta">
                                <span className="correlation">Correlation <span className="score">{(candidate.correlation * 100).toFixed(0)}%</span></span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </>
                  )
                })()}
              </div>
            ) : (
              <div className="evidence-placeholder">
                {activeField
                  ? `No mapping evidence for "${activeField.replace(/_/g, ' ')}"`
                  : draft.mapping_evidence && Object.keys(draft.mapping_evidence).length > 0
                    ? 'Click a field on the left to view its mapping evidence'
                    : 'No mapping evidence available'
                }
              </div>
            )}
          </div>

          {/* Column 3: Metadata Entries */}
          <div className="draft-column">
            <h2>Metadata Entries {metadataOptions.length > 0 && <span className="count">({metadataOptions.length})</span>}</h2>
            {metadataOptions.length > 0 ? (
              <div className="metadata-list">
                {metadataOptions.map(opt => {
                  const correlation = getCorrelationForSchema(activeField, opt.schema)
                  const isCandidateForField = activeField ? isCandidate(activeField, opt.schema) : false
                  const isSelected = activeField && isEditing && fieldSelections[activeField] === opt.schema
                  const isCurrentDecided = activeField && draft.mapping_evidence?.[activeField]?.decided?.metadata_column === opt.schema

                  return (
                    <div
                      key={opt.schema}
                      className={`metadata-item ${isCandidateForField ? 'is-candidate' : ''} ${isSelected ? 'selected' : ''} ${isCurrentDecided ? 'is-current' : ''} ${!isEditing || !activeField ? 'readonly' : ''}`}
                      onClick={() => isEditing && activeField && handleMetadataSelect(opt.schema)}
                    >
                      <div className="metadata-schema">
                        {opt.schema}
                        {isCandidateForField && <span className="candidate-badge">Candidate</span>}
                        {isCurrentDecided && <span className="current-badge">Current</span>}
                      </div>
                      <div className="metadata-value">{opt.value || '(empty)'}</div>
                      {correlation !== null && (
                        <div className="metadata-correlation">Correlation <span className="score">{(correlation * 100).toFixed(0)}%</span></div>
                      )}
                    </div>
                  )
                })}
              </div>
            ) : (
              <div className="metadata-placeholder">No metadata entries available</div>
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
