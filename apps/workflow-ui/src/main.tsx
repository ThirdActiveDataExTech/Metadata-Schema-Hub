import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from './components'
import HomePage from './pages/HomePage'
import CatalogListPage from './pages/consumer/CatalogListPage'
import CatalogDetailPage from './pages/consumer/CatalogDetailPage'
import UploadPage from './pages/publisher/UploadPage'
import IngestionRunsPage from './pages/publisher/IngestionRunsPage'
import DraftListPage from './pages/publisher/DraftListPage'
import DraftDetailPage from './pages/publisher/DraftDetailPage'
import LineagePage from './pages/publisher/LineagePage'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="catalog" element={<CatalogListPage />} />
          <Route path="catalog/:id" element={<CatalogDetailPage />} />
          <Route path="admin/upload" element={<UploadPage />} />
          <Route path="admin/runs" element={<IngestionRunsPage />} />
          <Route path="admin/drafts" element={<DraftListPage />} />
          <Route path="admin/drafts/:id" element={<DraftDetailPage />} />
          <Route path="admin/lineage" element={<LineagePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)
