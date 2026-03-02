import React, { useState } from 'react'
import PDFViewer from './PDFViewer'

function ExampleInvoices({ examples, onLoadExample }) {
  const [selectedPDF, setSelectedPDF] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  // Filter examples based on search
  const filteredExamples = examples.filter(example => 
    example.filename.toLowerCase().includes(searchTerm.toLowerCase())
  )

  // Only show PDF examples
  const pdfExamples = filteredExamples.filter(example => 
    example.filename.toLowerCase().endsWith('.pdf')
  )

  const handleViewPDF = (example) => {
    setSelectedPDF({
      url: `/api/examples/${example.filename}`,
      name: example.filename
    })
  }

  const handleClosePDF = () => {
    setSelectedPDF(null)
  }

  return (
    <div className="example-invoices">
      <div className="examples-header">
        <div>
          <h2>📄 Example Invoice Library</h2>
          <p>Training data pool - {pdfExamples.length} PDF invoices available</p>
        </div>
        <div className="examples-search">
          <input 
            type="text"
            placeholder="🔍 Search invoices..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
      </div>
      
      <div className="examples-scroll-container">
        {pdfExamples.length === 0 ? (
          <div className="no-examples">
            <p>No PDF invoices found.</p>
            {searchTerm && <p>Try a different search term.</p>}
          </div>
        ) : (
          <div className="examples-list">
            {pdfExamples.map((example, index) => (
              <div key={index} className="example-item">
                <div className="example-preview">
                  <div className="pdf-icon">📄</div>
                </div>
                
                <div className="example-info">
                  <h4 className="example-filename">{example.filename}</h4>
                  <div className="example-meta">
                    {example.invoice_number && (
                      <span className="meta-tag">#{example.invoice_number}</span>
                    )}
                    {example.date && (
                      <span className="meta-tag">📅 {example.date}</span>
                    )}
                    {example.total > 0 && (
                      <span className="meta-tag">💶 €{example.total.toFixed(2)}</span>
                    )}
                  </div>
                  {example.client?.name && (
                    <p className="example-client">
                      <strong>Client:</strong> {example.client.name}
                    </p>
                  )}
                </div>
                
                <div className="example-actions">
                  <button 
                    className="btn-view-pdf"
                    onClick={() => handleViewPDF(example)}
                    title="View PDF"
                  >
                    👁️ View
                  </button>
                  <button 
                    className="btn-load-example"
                    onClick={() => onLoadExample(example)}
                    title="Load as template"
                  >
                    📋 Load
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectedPDF && (
        <PDFViewer 
          fileUrl={selectedPDF.url}
          fileName={selectedPDF.name}
          onClose={handleClosePDF}
        />
      )}
    </div>
  )
}

export default ExampleInvoices
