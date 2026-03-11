import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { storeMetadata, createDraft } from '../../api'
import type { StoreResult } from '../../types'

export default function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [storeResult, setStoreResult] = useState<StoreResult | null>(null)
  const [creatingDraft, setCreatingDraft] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
      setStoreResult(null)
      setError(null)
    }
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setStoreResult(null)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)

    try {
      const result = await storeMetadata(file)
      setStoreResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload file')
    } finally {
      setUploading(false)
    }
  }

  const handleCreateDraft = async () => {
    if (!storeResult) return

    setCreatingDraft(true)
    setError(null)

    try {
      const result = await createDraft(storeResult.run_id)
      navigate(`/admin/drafts/${result.draft.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create draft')
    } finally {
      setCreatingDraft(false)
    }
  }

  const handleReset = () => {
    setFile(null)
    setStoreResult(null)
    setError(null)
  }

  return (
    <div className="page upload-page">
      <div className="page-header">
        <h1>Upload Metadata</h1>
      </div>

      {!storeResult ? (
        <>
          <div
            className={`upload-zone ${dragActive ? 'drag-active' : ''} ${file ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              id="file-input"
              onChange={handleFileChange}
              accept=".json,.jsonld,.xml,.rdf"
              className="file-input"
            />
            <label htmlFor="file-input" className="upload-label">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
              </svg>
              {file ? (
                <span className="file-name">{file.name}</span>
              ) : (
                <span>Drag and drop or click to select file</span>
              )}
            </label>
          </div>

          <div className="upload-info">
            <p>Supported formats: JSON-LD (.json, .jsonld), RDF/XML (.xml, .rdf)</p>
          </div>

          {error && (
            <div className="error-message">{error}</div>
          )}

          <div className="upload-actions">
            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="btn btn-primary"
            >
              {uploading ? 'Uploading...' : 'Upload & Store'}
            </button>
          </div>
        </>
      ) : (
        <div className="store-result">
          <div className="result-card success">
            <h2>Metadata Stored Successfully</h2>
            <dl>
              <dt>Snapshot ID</dt>
              <dd><code>{storeResult.snapshot_id}</code></dd>

              <dt>Run ID</dt>
              <dd>{storeResult.run_id}</dd>

              <dt>Metadata Count</dt>
              <dd>{storeResult.metadata_count} fields</dd>

              <dt>State</dt>
              <dd><span className="status-badge stored">{storeResult.state}</span></dd>
            </dl>
          </div>

          {error && (
            <div className="error-message">{error}</div>
          )}

          <div className="result-actions">
            <button onClick={handleReset} className="btn btn-secondary">
              Upload Another
            </button>
            <button
              onClick={handleCreateDraft}
              disabled={creatingDraft}
              className="btn btn-primary"
            >
              {creatingDraft ? 'Creating Draft...' : 'Create Draft'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
