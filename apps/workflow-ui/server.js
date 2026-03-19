import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3000;

// API Proxy configuration
const CATALOG_SERVICE_URL = process.env.CATALOG_SERVICE_URL || 'http://catalog-service:8084';
const INGESTION_SERVICE_URL = process.env.INGESTION_SERVICE_URL || 'http://metadata-ingestion:8085';

// Proxy to catalog-service
app.use('/api/v1/catalog-service', createProxyMiddleware({
  target: CATALOG_SERVICE_URL,
  changeOrigin: true,
  pathRewrite: { '^/api/v1/catalog-service': '' },
  onError: (err, req, res) => {
    console.error('Catalog service proxy error:', err.message);
    res.status(502).json({ error: 'Catalog service unavailable' });
  }
}));

// Proxy to metadata-ingestion
app.use('/api/v1/metadata-ingestion', createProxyMiddleware({
  target: INGESTION_SERVICE_URL,
  changeOrigin: true,
  pathRewrite: { '^/api/v1/metadata-ingestion': '' },
  onError: (err, req, res) => {
    console.error('Ingestion service proxy error:', err.message);
    res.status(502).json({ error: 'Ingestion service unavailable' });
  }
}));

// Static files
app.use(express.static(join(__dirname, 'dist')));

// SPA fallback
app.use((req, res) => {
  res.sendFile(join(__dirname, 'dist', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Catalog service: ${CATALOG_SERVICE_URL}`);
  console.log(`Ingestion service: ${INGESTION_SERVICE_URL}`);
});
