import React, { useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'
import '../styles/PDFViewer.css'

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

function PDFViewer({ fileUrl, fileName, onClose }) {
  const [numPages, setNumPages] = useState(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [scale, setScale] = useState(1.0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  function onDocumentLoadSuccess({ numPages }) {
    setNumPages(numPages)
    setLoading(false)
  }

  function onDocumentLoadError(error) {
    console.error('Error loading PDF:', error)
    setError('Failed to load PDF')
    setLoading(false)
  }

  function changePage(offset) {
    setPageNumber(prevPageNumber => prevPageNumber + offset)
  }

  function previousPage() {
    changePage(-1)
  }

  function nextPage() {
    changePage(1)
  }

  function zoomIn() {
    setScale(prev => Math.min(prev + 0.2, 3.0))
  }

  function zoomOut() {
    setScale(prev => Math.max(prev - 0.2, 0.5))
  }

  function resetZoom() {
    setScale(1.0)
  }

  return (
    <div className="pdf-viewer-overlay" onClick={onClose}>
      <div className="pdf-viewer-container" onClick={(e) => e.stopPropagation()}>
        <div className="pdf-viewer-header">
          <div className="pdf-viewer-title">
            <span className="pdf-icon">📄</span>
            <span>{fileName || 'PDF Viewer'}</span>
          </div>
          <button className="pdf-viewer-close" onClick={onClose}>✕</button>
        </div>

        <div className="pdf-viewer-controls">
          <div className="pdf-viewer-nav">
            <button 
              onClick={previousPage} 
              disabled={pageNumber <= 1}
              className="pdf-nav-btn"
            >
              ← Previous
            </button>
            <span className="pdf-page-info">
              Page {pageNumber} of {numPages || '?'}
            </span>
            <button 
              onClick={nextPage} 
              disabled={pageNumber >= numPages}
              className="pdf-nav-btn"
            >
              Next →
            </button>
          </div>

          <div className="pdf-viewer-zoom">
            <button onClick={zoomOut} className="pdf-zoom-btn">-</button>
            <button onClick={resetZoom} className="pdf-zoom-btn">{Math.round(scale * 100)}%</button>
            <button onClick={zoomIn} className="pdf-zoom-btn">+</button>
          </div>
        </div>

        <div className="pdf-viewer-content">
          {loading && (
            <div className="pdf-viewer-loading">
              <div className="spinner">⏳</div>
              <p>Loading PDF...</p>
            </div>
          )}

          {error && (
            <div className="pdf-viewer-error">
              <p>❌ {error}</p>
              <button onClick={onClose}>Close</button>
            </div>
          )}

          {!error && (
            <Document
              file={fileUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={null}
            >
              <Page 
                pageNumber={pageNumber} 
                scale={scale}
                renderTextLayer={true}
                renderAnnotationLayer={true}
              />
            </Document>
          )}
        </div>
      </div>
    </div>
  )
}

export default PDFViewer
