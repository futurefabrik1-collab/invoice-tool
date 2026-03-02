import React, { useState, useEffect } from 'react'
import axios from 'axios'
import PDFViewer from './components/PDFViewer'
import './styles/NewApp.css'

// Configure axios to use backend URL
// Use relative URLs for production, works on any domain/IP
const api = axios.create({
  baseURL: window.location.origin
})

function NewApp() {
  // State for dropdowns and inputs
  const [exampleInvoices, setExampleInvoices] = useState([])
  const [selectedExample, setSelectedExample] = useState(null)
  const [prompt, setPrompt] = useState('')
  const [referenceFiles, setReferenceFiles] = useState([])
  
  // PDF Viewer state
  const [viewingPDF, setViewingPDF] = useState(null)
  
  // State for the draft invoice
  const [draftInvoice, setDraftInvoice] = useState({
    type: 'Rechnung',
    invoice_number: '',
    date: new Date().toLocaleDateString('de-DE'),
    zeitraum: '',
    expiry_date: '',  // For Angebot
    due_date: '',      // For Rechnung
    client: {
      name: '',
      address: '',
      city: ''
    },
    project_name: '',
    project_description: '',
    items: [],
    notes: '',
    signature_file: ''  // Signature filename
  })
  
  // State for signatures
  const [signatures, setSignatures] = useState([])
  const [selectedSignature, setSelectedSignature] = useState(null)
  
  // State for customers
  const [customers, setCustomers] = useState([])
  
  // State for search filters
  const [invoiceSearchTerm, setInvoiceSearchTerm] = useState('')
  const [customerSearchTerm, setCustomerSearchTerm] = useState('')
  
  // UI State
  const [loading, setLoading] = useState(false)
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState(null)

  // Load examples and customers on mount
  useEffect(() => {
    loadExampleInvoices()
    loadCustomers()
    loadNextInvoiceNumber()
    loadSignatures()
  }, [])
  
  const loadSignatures = async () => {
    try {
      const response = await api.get('/api/signatures/list')
      if (response.data.success) {
        setSignatures(response.data.signatures)
      }
    } catch (error) {
      console.error('Error loading signatures:', error)
    }
  }
  
  const handleSignatureUpload = async (e) => {
    const files = Array.from(e.target.files)
    
    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        const response = await api.post('/api/signatures/upload', formData)
        if (response.data.success) {
          // Reload signatures
          await loadSignatures()
          // Auto-select the newly uploaded signature
          setSelectedSignature(response.data.filename)
          setDraftInvoice(prev => ({
            ...prev,
            signature_file: response.data.filename
          }))
          alert(`Signature "${file.name}" uploaded successfully!`)
        }
      } catch (error) {
        console.error('Error uploading signature:', error)
        alert('Error uploading signature: ' + (error.response?.data?.error || error.message))
      }
    }
  }
  
  const handleSignatureDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) return
    
    const file = files[0]
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await api.post('/api/signatures/upload', formData)
      if (response.data.success) {
        await loadSignatures()
        setSelectedSignature(response.data.filename)
        setDraftInvoice(prev => ({
          ...prev,
          signature_file: response.data.filename
        }))
        alert(`Signature "${file.name}" uploaded successfully!`)
      }
    } catch (error) {
      console.error('Error uploading signature:', error)
      alert('Error: ' + (error.response?.data?.error || error.message))
    }
  }
  
  const selectSignature = (filename) => {
    setSelectedSignature(filename)
    setDraftInvoice(prev => ({
      ...prev,
      signature_file: filename
    }))
  }

  const loadNextInvoiceNumber = async (docType = 'Rechnung') => {
    try {
      const response = await api.get(`/api/invoice/next-number?type=${docType}`)
      if (response.data.success && response.data.next_number) {
        setDraftInvoice(prev => ({
          ...prev,
          invoice_number: response.data.next_number
        }))
        console.log(`Auto-assigned ${docType} number: ${response.data.next_number}`)
      }
    } catch (error) {
      console.log('Invoice numbering not configured - manual numbering')
    }
  }
  
  // Reload number when type changes
  const handleTypeChange = (newType) => {
    setDraftInvoice(prev => ({ ...prev, type: newType }))
    loadNextInvoiceNumber(newType)
  }

  const loadExampleInvoices = async () => {
    try {
      const response = await api.get('/api/examples/list-all')
      if (response.data.success) {
        setExampleInvoices(response.data.examples)
      }
    } catch (error) {
      console.error('Error loading examples:', error)
    }
  }

  const loadCustomers = async () => {
    try {
      const response = await api.get('/api/customers')
      if (response.data.success) {
        setCustomers(response.data.customers)
      }
    } catch (error) {
      console.error('Error loading customers:', error)
    }
  }

  const handleExampleChange = async (e) => {
    const exampleId = e.target.value
    if (!exampleId) {
      setSelectedExample(null)
      return
    }
    
    const example = exampleInvoices.find(ex => ex.id === exampleId)
    setSelectedExample(example)
    
    // Use AI to extract client info from the example invoice PDF
    setLoading(true)
    try {
      const response = await api.post('/api/ai/generate-invoice', {
        prompt: `Extract the client information from this invoice. Keep all other fields empty.`,
        example_name: example.id,
        reference_files: []
      })
      
      if (response.data.success && response.data.invoice_data.client) {
        console.log('Auto-populated from example:', response.data.invoice_data)
        setDraftInvoice(prev => ({
          ...prev,
          client: response.data.invoice_data.client,
          type: response.data.invoice_data.type || prev.type
        }))
      }
    } catch (error) {
      console.error('Error extracting from example:', error)
      // Fallback to old parsing method
      try {
        const response = await api.get('/api/parse-examples')
        if (response.data.success) {
          const parsedExample = response.data.examples.find(ex => 
            ex.filename === example.id || ex.filename.includes(example.name)
          )
          
          if (parsedExample && parsedExample.client) {
            setDraftInvoice(prev => ({
              ...prev,
              client: parsedExample.client,
              items: parsedExample.items || prev.items
            }))
          }
        }
      } catch (fallbackError) {
        console.error('Error with fallback parsing:', fallbackError)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const files = Array.from(e.target.files)
    await processReferenceFiles(files)
  }

  const processReferenceFiles = async (files) => {
    for (const file of files) {
      const formData = new FormData()
      formData.append('file', file)
      
      try {
        const response = await api.post('/api/upload-reference', formData)
        if (response.data.success) {
          setReferenceFiles(prev => [...prev, {
            name: file.name,
            content: response.data.content
          }])
        }
      } catch (error) {
        console.error('Error uploading file:', error)
      }
    }
    
    // Auto-update draft after file upload
    if (prompt) {
      handleUpdateDraft()
    }
  }

  const handleReferenceDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    const files = Array.from(e.dataTransfer.files)
    await processReferenceFiles(files)
  }

  const handleExampleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    
    const files = Array.from(e.dataTransfer.files)
    if (files.length === 0) return
    
    // Upload the example invoice to the examples directory
    const file = files[0] // Take first file only
    if (!file.name.endsWith('.pdf')) {
      alert('Please upload a PDF file')
      return
    }
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await api.post('/api/upload-example', formData)
      if (response.data.success) {
        // Reload examples list
        await loadExampleInvoices()
        alert(`Example invoice "${file.name}" uploaded successfully!`)
      }
    } catch (error) {
      console.error('Error uploading example:', error)
      alert('Error uploading example: ' + (error.response?.data?.error || error.message))
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    e.currentTarget.classList.add('dragging')
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    e.currentTarget.classList.remove('dragging')
  }

  const handleUpdateDraft = async () => {
    if (!prompt.trim() && !selectedExample) {
      alert('Please enter a prompt/notes or select an example invoice first')
      return
    }
    
    setLoading(true)
    try {
      // If example is selected, tell AI to use it as reference
      let enhancedPrompt = prompt
      if (selectedExample && prompt) {
        enhancedPrompt = `${prompt}\n\nUse example invoice "${selectedExample.name}" as a reference for formatting and structure.`
      } else if (selectedExample && !prompt) {
        enhancedPrompt = `Create an invoice similar to the example "${selectedExample.name}". Extract and use the client information from that invoice.`
      }
      
      // Prepare example invoice data if selected
      let exampleData = null
      if (selectedExample) {
        const response = await api.get('/api/parse-examples')
        if (response.data.success) {
          const parsedExample = response.data.examples.find(ex => 
            ex.filename === selectedExample.id || ex.filename === selectedExample.name
          )
          exampleData = parsedExample
        }
      }
      
      // Call AI to generate/update invoice
      const response = await api.post('/api/ai/generate-invoice', {
        prompt: enhancedPrompt,
        example_invoice: exampleData || draftInvoice,
        reference_files: referenceFiles.map(f => f.content),
        example_name: selectedExample?.name
      })
      
      if (response.data.success) {
        setDraftInvoice(response.data.invoice_data)
        // Trigger preview update
        generatePreview(response.data.invoice_data)
      }
    } catch (error) {
      console.error('Error updating draft:', error)
      alert('Error updating draft: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  const generatePreview = async (invoiceData = draftInvoice) => {
    try {
      const response = await api.post('/api/invoice/preview', invoiceData)
      if (response.data.success) {
        // Preview generation successful
        // For now, we'll just show the data
        // TODO: Generate actual PDF preview
      }
    } catch (error) {
      console.error('Error generating preview:', error)
    }
  }

  const handleDraftFieldChange = (field, value) => {
    setDraftInvoice(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleClientFieldChange = (field, value) => {
    setDraftInvoice(prev => ({
      ...prev,
      client: {
        ...prev.client,
        [field]: value
      }
    }))
  }

  const handleItemChange = (index, field, value) => {
    setDraftInvoice(prev => {
      const newItems = [...prev.items]
      newItems[index] = {
        ...newItems[index],
        [field]: value
      }
      
      // Auto-calculate amount if quantity or rate changes
      if (field === 'quantity' || field === 'rate') {
        const qty = field === 'quantity' ? parseFloat(value) : parseFloat(newItems[index].quantity || 0)
        const rate = field === 'rate' ? parseFloat(value) : parseFloat(newItems[index].rate || 0)
        newItems[index].amount = qty * rate
      }
      
      return {
        ...prev,
        items: newItems
      }
    })
  }

  const addItem = () => {
    setDraftInvoice(prev => ({
      ...prev,
      items: [...prev.items, {
        description: '',
        quantity: 1,
        rate: 0,
        amount: 0
      }]
    }))
  }

  const removeItem = (index) => {
    setDraftInvoice(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }))
  }

  const handleGeneratePDF = async () => {
    setLoading(true)
    try {
      const response = await api.post('/api/invoice/create', draftInvoice)
      if (response.data.success) {
        // Open the generated PDF in the viewer instead of downloading
        setViewingPDF({
          url: `${window.location.origin}${response.data.path.replace('/Users/markburnett/DevPro/invoice-tool', '')}`,
          name: response.data.invoice_id
        })
        
        alert(`Invoice ${response.data.invoice_id} generated successfully!`)
        
        // Reload customers (new customer may have been added)
        loadCustomers()
      }
    } catch (error) {
      console.error('Error generating PDF:', error)
      alert('Error generating PDF: ' + (error.response?.data?.error || error.message))
    } finally {
      setLoading(false)
    }
  }

  const loadCustomerData = (customer) => {
    setDraftInvoice(prev => ({
      ...prev,
      client: {
        name: customer.name,
        address: customer.address,
        city: customer.city
      }
    }))
  }

  const calculateTotal = () => {
    return draftInvoice.items.reduce((sum, item) => sum + (item.amount || 0), 0)
  }

  return (
    <div className="new-app">
      {viewingPDF && (
        <PDFViewer
          fileUrl={viewingPDF.url}
          fileName={viewingPDF.name}
          onClose={() => setViewingPDF(null)}
        />
      )}
      
      <header className="header">
        <h1>📄 Future Fabrik - AI Invoice Generator</h1>
        <p>Create invoices with AI assistance</p>
      </header>

      {/* Drag and Drop Zones Header - Full Width */}
      <div className="dropzones-header">
        <div className="dropzone-container">
          <div 
            className="dropzone dropzone-compact"
            onDrop={handleExampleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <div className="dropzone-content">
              <span className="dropzone-icon">📄</span>
              <p className="dropzone-text">Example Invoice PDF</p>
            </div>
          </div>

          <div 
            className="dropzone dropzone-compact"
            onDrop={handleReferenceDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <div className="dropzone-content">
              <span className="dropzone-icon">📎</span>
              <p className="dropzone-text">Reference Files</p>
              <input
                type="file"
                multiple
                onChange={handleFileUpload}
                style={{ display: 'none' }}
                id="reference-file-input"
              />
            </div>
          </div>

          <div 
            className="dropzone dropzone-compact"
            onDrop={handleSignatureDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <div className="dropzone-content">
              <span className="dropzone-icon">✍️</span>
              <p className="dropzone-text">Signature Image</p>
              <input
                type="file"
                onChange={handleSignatureUpload}
                accept=".png,.jpg,.jpeg,.gif,.pdf"
                style={{ display: 'none' }}
                id="signature-file-input"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="main-container">
        {/* Left Panel - Controls */}
        <div className="controls-panel">
          <div className="control-group">
            <label>Previous Rechnung ({exampleInvoices.length} available)</label>
            
            {/* Search input for invoices */}
            <input
              type="text"
              placeholder="🔍 Search invoices..."
              value={invoiceSearchTerm}
              onChange={(e) => setInvoiceSearchTerm(e.target.value)}
              className="search-input"
              style={{ marginBottom: '10px', width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
            />
            
            {/* List-style selector with fixed height and scroll */}
            <div className="examples-list">
              {exampleInvoices
                .filter(ex => ex.name.toLowerCase().includes(invoiceSearchTerm.toLowerCase()))
                .map(ex => (
                <div 
                  key={ex.id}
                  className={`example-list-item ${selectedExample?.id === ex.id ? 'selected' : ''}`}
                  onClick={() => {
                    const event = { target: { value: ex.id } };
                    handleExampleChange(event);
                  }}
                >
                  <div className="example-list-icon">
                    {ex.type === 'Angebot' ? '📋' : '📄'}
                  </div>
                  <div className="example-list-content">
                    <div className="example-list-name">{ex.name}</div>
                    <div className="example-list-meta">
                      <span className="example-list-type">{ex.type}</span>
                    </div>
                  </div>
                  <button 
                    className="example-list-preview"
                    onClick={(e) => {
                      e.stopPropagation();
                      setViewingPDF({
                        url: `${window.location.origin}/api/examples/${ex.filename || ex.name}`,
                        name: ex.name
                      });
                    }}
                    title="Preview this invoice"
                  >
                    👁️
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="control-group">
            <label>Previous Customers ({customers.length} available)</label>
            
            {/* Search input for customers */}
            <input
              type="text"
              placeholder="🔍 Search customers..."
              value={customerSearchTerm}
              onChange={(e) => setCustomerSearchTerm(e.target.value)}
              className="search-input"
              style={{ marginBottom: '10px', width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
            />
            
            {/* List-style selector for customers with live search results */}
            <div className="customers-list" style={{ 
              maxHeight: '200px', 
              overflowY: 'auto', 
              border: '1px solid #ccc', 
              borderRadius: '4px',
              backgroundColor: '#fff'
            }}>
              {customers
                .filter(c => c.name.toLowerCase().includes(customerSearchTerm.toLowerCase()))
                .map(customer => (
                  <div
                    key={customer.name}
                    className="customer-item"
                    onClick={() => loadCustomerData(customer)}
                    style={{
                      padding: '10px',
                      cursor: 'pointer',
                      borderBottom: '1px solid #eee',
                      transition: 'background-color 0.2s'
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = '#f0f0f0'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = '#fff'}
                  >
                    <div style={{ fontWeight: '500', marginBottom: '2px' }}>{customer.name}</div>
                    <div style={{ fontSize: '12px', color: '#666' }}>
                      {customer.invoice_count} invoices
                      {customer.address && ` • ${customer.address}`}
                      {customer.city && ` • ${customer.city}`}
                    </div>
                  </div>
                ))}
              {customers.filter(c => c.name.toLowerCase().includes(customerSearchTerm.toLowerCase())).length === 0 && (
                <div style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
                  No customers found
                </div>
              )}
            </div>
          </div>

          <div className="control-group">
            <label>Notes / Prompt</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe what you want in the invoice... e.g., '3D visualization for Leipzig project, 10 hours at 650€/hour'"
              className="prompt-textarea"
              rows={6}
            />
          </div>

          <div className="control-group">
            <label>Reference Files ({referenceFiles.length})</label>
            {referenceFiles.length > 0 && (
              <div className="reference-files-list">
                {referenceFiles.map((file, idx) => (
                  <div key={idx} className="reference-file">
                    <span>📎 {file.name}</span>
                    <div className="reference-file-actions">
                      {file.name.endsWith('.pdf') && (
                        <button 
                          className="btn-view-small"
                          onClick={() => setViewingPDF({
                            url: `${window.location.origin}/api/pdf/view/${file.name}`,
                            name: file.name
                          })}
                        >
                          👁️
                        </button>
                      )}
                      <button 
                        className="btn-remove-small"
                        onClick={() => setReferenceFiles(prev => prev.filter((_, i) => i !== idx))}
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <button 
            className="btn-update"
            onClick={handleUpdateDraft}
            disabled={loading}
          >
            {loading ? '⏳ Updating...' : '🔄 Update Draft'}
          </button>
          
          {/* Signature Upload Section */}
          <div className="control-group">
            <label>Signature</label>
            
            {/* Previously uploaded signatures */}
            {signatures.length > 0 && (
              <div className="signatures-list">
                {signatures.map(sig => (
                  <div 
                    key={sig.filename}
                    className={`signature-item ${selectedSignature === sig.filename ? 'selected' : ''}`}
                    onClick={() => selectSignature(sig.filename)}
                  >
                    <img 
                      src={`${window.location.origin}/api/signatures/view/${sig.filename}`}
                      alt={sig.filename}
                      className="signature-preview"
                    />
                    <div className="signature-name">{sig.filename}</div>
                  </div>
                ))}
              </div>
            )}
            {referenceFiles.length === 0 && (
              <p style={{ fontSize: '12px', color: '#999', fontStyle: 'italic', marginTop: '10px' }}>
                No reference files. Use dropzone above.
              </p>
            )}
          </div>
        </div>

        {/* Right Panel - Live Draft */}
        <div className="draft-panel">
          <div className="draft-header">
            <h2>Live Draft</h2>
            <button 
              className="btn-generate"
              onClick={handleGeneratePDF}
              disabled={loading}
            >
              {loading ? 'Generating...' : '📥 Generate PDF'}
            </button>
          </div>

          <div className="draft-form">
            <div className="form-row">
              <div className="form-field">
                <label>Type</label>
                <select 
                  value={draftInvoice.type}
                  onChange={(e) => handleTypeChange(e.target.value)}
                >
                  <option value="Rechnung">Rechnung</option>
                  <option value="Angebot">Angebot</option>
                </select>
              </div>
              <div className="form-field">
                <label>{draftInvoice.type} Number</label>
                <input
                  type="text"
                  value={draftInvoice.invoice_number}
                  onChange={(e) => handleDraftFieldChange('invoice_number', e.target.value)}
                  placeholder="Auto-generated"
                />
              </div>
              <div className="form-field">
                <label>Date</label>
                <input
                  type="text"
                  value={draftInvoice.date}
                  onChange={(e) => handleDraftFieldChange('date', e.target.value)}
                />
              </div>
            </div>
            
            <div className="form-row">
              <div className="form-field">
                <label>Zeitraum (Optional)</label>
                <input
                  type="text"
                  value={draftInvoice.zeitraum}
                  onChange={(e) => handleDraftFieldChange('zeitraum', e.target.value)}
                  placeholder="e.g., 01.02.2026 - 28.02.2026"
                />
              </div>
              {draftInvoice.type === 'Angebot' ? (
                <div className="form-field">
                  <label>Gültig bis (Optional)</label>
                  <input
                    type="text"
                    value={draftInvoice.expiry_date}
                    onChange={(e) => handleDraftFieldChange('expiry_date', e.target.value)}
                    placeholder="e.g., 31.03.2026"
                  />
                </div>
              ) : (
                <div className="form-field">
                  <label>Zahlungsziel (Optional)</label>
                  <input
                    type="text"
                    value={draftInvoice.due_date}
                    onChange={(e) => handleDraftFieldChange('due_date', e.target.value)}
                    placeholder="e.g., 14 Tage netto"
                  />
                </div>
              )}
            </div>

            <div className="client-section">
              <h3>Client Information</h3>
              <div className="form-field">
                <label>Client Name</label>
                <input
                  type="text"
                  value={draftInvoice.client.name}
                  onChange={(e) => handleClientFieldChange('name', e.target.value)}
                />
              </div>
              <div className="form-field">
                <label>Address</label>
                <input
                  type="text"
                  value={draftInvoice.client.address}
                  onChange={(e) => handleClientFieldChange('address', e.target.value)}
                />
              </div>
              <div className="form-field">
                <label>City</label>
                <input
                  type="text"
                  value={draftInvoice.client.city}
                  onChange={(e) => handleClientFieldChange('city', e.target.value)}
                />
              </div>
            </div>

            <div className="project-section">
              <h3>Project Details (Optional)</h3>
              <div className="form-field">
                <label>Project Name</label>
                <input
                  type="text"
                  value={draftInvoice.project_name}
                  onChange={(e) => handleDraftFieldChange('project_name', e.target.value)}
                  placeholder="e.g., Akustikinstallation"
                />
              </div>
              <div className="form-field" style={{gridColumn: '1 / -1'}}>
                <label>Project Description (up to 200 words)</label>
                <textarea
                  value={draftInvoice.project_description}
                  onChange={(e) => handleDraftFieldChange('project_description', e.target.value)}
                  placeholder="Detailed description of project scope, deliverables, and services. AI will generate this automatically when you click 'Update Draft'."
                  rows={6}
                  style={{width: '100%', resize: 'vertical'}}
                />
                <div className="char-count">
                  {draftInvoice.project_description.length} characters
                </div>
              </div>
            </div>

            <div className="items-section">
              <div className="items-header">
                <h3>Line Items</h3>
                <button className="btn-add-item" onClick={addItem}>+ Add Item</button>
              </div>
              
              {draftInvoice.items.map((item, index) => (
                <div key={index} className="item-row">
                  <div className="item-field item-description">
                    <label>Description</label>
                    <input
                      type="text"
                      value={item.description}
                      onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                    />
                  </div>
                  <div className="item-field item-quantity">
                    <label>Qty</label>
                    <input
                      type="number"
                      value={item.quantity}
                      onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                    />
                  </div>
                  <div className="item-field item-rate">
                    <label>Rate (€)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={item.rate}
                      onChange={(e) => handleItemChange(index, 'rate', e.target.value)}
                    />
                  </div>
                  <div className="item-field item-amount">
                    <label>Amount (€)</label>
                    <input
                      type="number"
                      value={item.amount}
                      readOnly
                    />
                  </div>
                  <button 
                    className="btn-remove-item"
                    onClick={() => removeItem(index)}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>

            <div className="total-section">
              <strong>Total: €{calculateTotal().toFixed(2)}</strong>
            </div>

            <div className="notes-section">
              <h3>Notes</h3>
              <textarea
                value={draftInvoice.notes}
                onChange={(e) => handleDraftFieldChange('notes', e.target.value)}
                placeholder="Payment terms, thank you note, etc."
                rows={4}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NewApp
