import React from 'react'
import '../styles/PDFViewer.css'

function PDFViewer({ fileUrl, fileName, onClose }) {
  const handleDownload = () => {
    // Replace /output/ with /download/ and add custom filename as query parameter
    const downloadUrl = fileUrl.replace('/output/', '/download/')
    const customFilename = fileName && !fileName.endsWith('.pdf') ? `${fileName}.pdf` : (fileName || 'invoice.pdf')
    
    // Add custom filename as query parameter
    const urlWithName = `${downloadUrl}?name=${encodeURIComponent(customFilename)}`
    
    // Use window.location to trigger download - server will handle the filename
    window.location.href = urlWithName
  }

  return (
    <div className="pdf-viewer-overlay" onClick={onClose}>
      <div className="pdf-viewer-container" onClick={(e) => e.stopPropagation()}>
        <div className="pdf-viewer-header">
          <div className="pdf-viewer-title">
            <span className="pdf-icon">📄</span>
            <span>{fileName || 'PDF Viewer'}</span>
          </div>
          <div className="pdf-viewer-actions">
            <button className="pdf-download-btn" onClick={handleDownload}>
              ⬇️ Download
            </button>
            <button className="pdf-viewer-close" onClick={onClose}>✕</button>
          </div>
        </div>

        <div className="pdf-viewer-content">
          <iframe 
            src={fileUrl}
            className="pdf-iframe"
            title={fileName || 'PDF Preview'}
            frameBorder="0"
          />
        </div>
      </div>
    </div>
  )
}

export default PDFViewer
