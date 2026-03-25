import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getCatalogEntry, getCatalogEntryRdf, getCatalogEntryRdfDownloadUrl } from '../../api'
import { TagList } from '../../components'
import type { CatalogEntryDetail } from '../../types'

export default function CatalogDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [entry, setEntry] = useState<CatalogEntryDetail | null>(null)
  const [rdf, setRdf] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(true)
  const [showRdf, setShowRdf] = useState(false)

  useEffect(() => {
    if (id) {
      loadEntry(Number(id))
    }
  }, [id])

  const loadEntry = async (entryId: number) => {
    setLoading(true)
    try {
      const data = await getCatalogEntry(entryId)
      setEntry(data)
    } catch (err) {
      console.error('Failed to load catalog entry:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadRdf = async () => {
    if (!id || rdf) return
    try {
      const data = await getCatalogEntryRdf(Number(id))
      setRdf(data)
    } catch (err) {
      console.error('Failed to load RDF:', err)
    }
  }

  const handleToggleRdf = () => {
    if (!showRdf && !rdf) {
      loadRdf()
    }
    setShowRdf(!showRdf)
  }

  if (loading) {
    return <div className="page"><div className="loading">Loading...</div></div>
  }

  if (!entry) {
    return (
      <div className="page">
        <div className="error-state">
          <p>Catalog entry not found</p>
          <Link to="/catalog" className="btn btn-secondary">Back to Catalog</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="page catalog-detail-page">
      <div className="page-header">
        <Link to="/catalog" className="back-link">Back to Catalog</Link>
        <div className="header-actions">
          <button onClick={handleToggleRdf} className="btn btn-secondary">
            {showRdf ? 'Hide RDF' : 'View RDF'}
          </button>
          <a href={getCatalogEntryRdfDownloadUrl(Number(id))} className="btn btn-primary" download>
            Download RDF
          </a>
        </div>
      </div>

      <div className="entry-detail">
        <h1>{entry.title || '(No title)'}</h1>

        <div className="detail-grid">
          <div className="detail-section">
            <h2>Basic Information</h2>
            <dl>
              <dt>Identifier</dt>
              <dd><code>{entry.identifier}</code></dd>

              <dt>Description</dt>
              <dd>{entry.description || '-'}</dd>

              <dt>Publisher</dt>
              <dd>{entry.publisher || '-'}</dd>
            </dl>
          </div>

          <div className="detail-section">
            <h2>Dates</h2>
            <dl>
              <dt>Issued</dt>
              <dd>{entry.issued || '-'}</dd>

              <dt>Modified</dt>
              <dd>{entry.modified || '-'}</dd>

              <dt>Ingested At</dt>
              <dd>{entry.ingested_at ? new Date(entry.ingested_at).toLocaleString() : '-'}</dd>

              <dt>Updated At</dt>
              <dd>{entry.updated_at ? new Date(entry.updated_at).toLocaleString() : '-'}</dd>
            </dl>
          </div>

          <div className="detail-section">
            <h2>Classification</h2>
            <dl>
              <dt>Keywords</dt>
              <dd><TagList items={entry.keyword} variant="keyword" /></dd>

              <dt>Themes</dt>
              <dd><TagList items={entry.theme} variant="theme" /></dd>

              <dt>External IDs</dt>
              <dd><TagList items={entry.external_ids} variant="external-id" /></dd>
            </dl>
          </div>

          <div className="detail-section">
            <h2>Access</h2>
            <dl>
              <dt>Landing Page</dt>
              <dd>
                {entry.landing_page ? (
                  <a href={entry.landing_page} target="_blank" rel="noopener noreferrer">
                    {entry.landing_page}
                  </a>
                ) : '-'}
              </dd>

              <dt>Access URL</dt>
              <dd>
                {entry.access_url ? (
                  <a href={entry.access_url} target="_blank" rel="noopener noreferrer">
                    {entry.access_url}
                  </a>
                ) : '-'}
              </dd>
            </dl>
          </div>

          <div className="detail-section">
            <h2>Lineage</h2>
            <dl>
              <dt>Snapshot ID</dt>
              <dd>
                {entry.latest_snapshot_id ? (
                  <Link to={`/admin/lineage?snapshot=${entry.latest_snapshot_id}`}>
                    <code>{entry.latest_snapshot_id.slice(0, 16)}...</code>
                  </Link>
                ) : '-'}
              </dd>
            </dl>
          </div>
        </div>

        {showRdf && (
          <div className="rdf-section">
            <h2>RDF (JSON-LD)</h2>
            <pre className="rdf-content">
              {rdf ? JSON.stringify(rdf, null, 2) : 'Loading...'}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
