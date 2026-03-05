import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <div className="home-page">
      <div className="welcome-section">
        <h1>Active Metadata Management</h1>
        <p>Metadata Catalog and Publishing System</p>
      </div>

      <div className="role-cards">
        <Link to="/catalog" className="role-card consumer">
          <div className="role-icon">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
            </svg>
          </div>
          <h2>Catalog Consumer</h2>
          <p>Search and browse published metadata catalog entries</p>
          <ul>
            <li>Search by keywords, themes</li>
            <li>Filter by date ranges</li>
            <li>Export to CSV / RDF</li>
          </ul>
        </Link>

        <Link to="/admin/upload" className="role-card publisher">
          <div className="role-icon">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
            </svg>
          </div>
          <h2>Catalog Publisher</h2>
          <p>Ingest, review, and publish metadata to catalog</p>
          <ul>
            <li>Upload metadata files</li>
            <li>Review draft mappings</li>
            <li>Publish or discard drafts</li>
          </ul>
        </Link>
      </div>
    </div>
  )
}
