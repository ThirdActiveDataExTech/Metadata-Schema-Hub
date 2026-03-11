import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { searchCatalogEntries, getCatalogExportCsvUrl } from '../../api'
import { Pagination } from '../../components'
import type { CatalogEntrySummary, SearchParams } from '../../types'

export default function CatalogListPage() {
  const [entries, setEntries] = useState<CatalogEntrySummary[]>([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [params, setParams] = useState<SearchParams>({
    limit: 20,
    offset: 0,
    sort_field: 'updated_at',
    sort_order: 'desc',
  })
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadEntries()
  }, [params])

  const loadEntries = async () => {
    setLoading(true)
    try {
      const results = await searchCatalogEntries(params)
      setEntries(results)
      setTotal(results.length >= params.limit! ? (params.offset || 0) + results.length + 1 : (params.offset || 0) + results.length)
    } catch (err) {
      console.error('Failed to load catalog entries:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setParams((prev: SearchParams) => ({ ...prev, query: searchQuery || undefined, offset: 0 }))
  }

  const handlePageChange = (offset: number) => {
    setParams((prev: SearchParams) => ({ ...prev, offset }))
  }

  const handleSort = (field: string) => {
    setParams((prev: SearchParams) => ({
      ...prev,
      sort_field: field,
      sort_order: prev.sort_field === field && prev.sort_order === 'asc' ? 'desc' : 'asc',
    }))
  }

  return (
    <div className="page catalog-list-page">
      <div className="page-header">
        <h1>Catalog Search</h1>
        <a href={getCatalogExportCsvUrl(1000)} className="btn btn-secondary" download>
          Export CSV
        </a>
      </div>

      <form className="search-form" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search by title or description..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
        <button type="submit" className="btn btn-primary">Search</button>
      </form>

      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <>
          <table className="data-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('id')} className="sortable">
                  ID {params.sort_field === 'id' && (params.sort_order === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('title')} className="sortable">
                  Title {params.sort_field === 'title' && (params.sort_order === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('publisher')} className="sortable">
                  Publisher {params.sort_field === 'publisher' && (params.sort_order === 'asc' ? '↑' : '↓')}
                </th>
                <th>Keywords</th>
                <th onClick={() => handleSort('updated_at')} className="sortable">
                  Updated {params.sort_field === 'updated_at' && (params.sort_order === 'asc' ? '↑' : '↓')}
                </th>
              </tr>
            </thead>
            <tbody>
              {entries.length === 0 ? (
                <tr>
                  <td colSpan={5} className="empty-row">No catalog entries found</td>
                </tr>
              ) : (
                entries.map(entry => (
                  <tr key={entry.id}>
                    <td>{entry.id}</td>
                    <td>
                      <Link to={`/catalog/${entry.id}`} className="entry-link">
                        {entry.title || '(No title)'}
                      </Link>
                    </td>
                    <td>{entry.publisher || '-'}</td>
                    <td>
                      {entry.keyword?.slice(0, 3).map((kw: string, i: number) => (
                        <span key={i} className="keyword-tag">{kw}</span>
                      ))}
                      {entry.keyword && entry.keyword.length > 3 && (
                        <span className="keyword-more">+{entry.keyword.length - 3}</span>
                      )}
                    </td>
                    <td>{entry.updated_at ? new Date(entry.updated_at).toLocaleDateString() : '-'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          <Pagination
            total={total}
            limit={params.limit || 20}
            offset={params.offset || 0}
            onPageChange={handlePageChange}
          />
        </>
      )}
    </div>
  )
}
