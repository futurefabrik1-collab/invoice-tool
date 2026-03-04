import React, { useState, useEffect } from 'react'
import axios from 'axios'
import PDFViewer from './components/PDFViewer'
import './styles/NewApp.css'

// Configure axios to use backend URL
// Use relative URLs for production, works on any domain/IP
const api = axios.create({
  baseURL: window.location.origin
})

const DRAFT_STORAGE_KEY = 'invoice_tool_saved_draft_v1'

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
    invoice_number: '5526',
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
    signature_file: '',  // Signature filename
    signature_name: 'Florian Manhardt'
  })
  
  // State for signatures
  const [signatures, setSignatures] = useState([])
  const [selectedSignature, setSelectedSignature] = useState(null)
  
  // State for customers
  const [customers, setCustomers] = useState([])
  
  // State for search filters
  const [invoiceSearchTerm, setInvoiceSearchTerm] = useState('')
  const [customerSearchTerm, setCustomerSearchTerm] = useState('')
  const [itemCatalog, setItemCatalog] = useState([])
  
  // UI State
  const [loading, setLoading] = useState(false)
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState(null)

  // Load examples and customers on mount
  useEffect(() => {
    loadExampleInvoices()
    loadCustomers()
    loadItemsCatalog()
    loadNextInvoiceNumber()
    loadSignatures()
  }, [])
  
  const loadSignatures = async () => {
    try {
      const response = await api.get(`/api/signatures/list?t=${Date.now()}`)
      if (response.data.success) {
        setSignatures(response.data.signatures)
      }
    } catch (error) {
      console.error('Error loading signatures:', error)
    }
  }
  
  const promptSignatureName = (originalName) => {
    const ext = (originalName.match(/\.[^.]+$/)?.[0] || '')
    const base = originalName.replace(/\.[^.]+$/, '')
    const entered = window.prompt('Name this signature (used in selector):', base)
    if (entered === null) return null
    const cleaned = entered.trim().replace(/[^a-zA-Z0-9 _-]/g, '').replace(/\s+/g, '-')
    const safeBase = cleaned || base
    return `${safeBase}${ext}`
  }

  const handleSignatureUpload = async (e) => {
    const files = Array.from(e.target.files)
    
    for (const file of files) {
      const namedFile = promptSignatureName(file.name)
      if (!namedFile) continue

      const formData = new FormData()
      formData.append('file', file)
      formData.append('desired_name', namedFile)
      
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
          alert(`Signature "${namedFile}" uploaded successfully!`)
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
    const namedFile = promptSignatureName(file.name)
    if (!namedFile) return

    const formData = new FormData()
    formData.append('file', file)
    formData.append('desired_name', namedFile)
    
    try {
      const response = await api.post('/api/signatures/upload', formData)
      if (response.data.success) {
        await loadSignatures()
        setSelectedSignature(response.data.filename)
        setDraftInvoice(prev => ({
          ...prev,
          signature_file: response.data.filename
        }))
        alert(`Signature "${namedFile}" uploaded successfully!`)
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

  const handleDeleteSignature = async () => {
    const current = draftInvoice.signature_file || selectedSignature
    if (!current) {
      alert('Select a signature first')
      return
    }

    if (!window.confirm(`Delete signature "${current}"?`)) return

    try {
      // Prefer body-based delete endpoint (more robust with special chars)
      let response
      try {
        response = await api.post('/api/signatures/delete', { filename: current })
      } catch (_e) {
        response = await api.delete(`/api/signatures/delete/${encodeURIComponent(current)}`)
      }

      if (response.data.success) {
        await loadSignatures()
        setSelectedSignature(null)
        setDraftInvoice(prev => ({ ...prev, signature_file: '' }))
        alert('✅ Signature deleted')
      }
    } catch (error) {
      console.error('Error deleting signature:', error)
      alert('Error deleting signature: ' + (error.response?.data?.error || error.message))
    }
  }

  const loadNextInvoiceNumber = async (_docType = 'Rechnung') => {
    // Manual completion mode: always prefill required prefix only
    setDraftInvoice(prev => ({
      ...prev,
      invoice_number: prev.invoice_number && prev.invoice_number.startsWith('5526') ? prev.invoice_number : '5526'
    }))
  }
  
  // Keep current entered suffix when type changes
  const handleTypeChange = (newType) => {
    setDraftInvoice(prev => ({
      ...prev,
      type: newType,
      invoice_number: prev.invoice_number && prev.invoice_number.startsWith('5526') ? prev.invoice_number : '5526'
    }))
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

  const loadItemsCatalog = async (q = '') => {
    try {
      const response = await api.get(`/api/catalog/items${q ? `?q=${encodeURIComponent(q)}` : ''}`)
      if (response.data.success) {
        setItemCatalog(response.data.items || [])
      }
    } catch (error) {
      console.error('Error loading item catalog:', error)
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
        // Reload curated lists after indexing
        await loadExampleInvoices()
        await loadCustomers()
        await loadItemsCatalog()
        const idx = response.data.index_result
        if (idx?.indexed) {
          alert(`Example invoice "${file.name}" imported. Indexed customer: ${idx.customer || 'n/a'}, items: ${idx.items_indexed || 0}`)
        } else {
          alert(`Example invoice "${file.name}" uploaded, but indexing failed: ${idx?.reason || 'unknown reason'}`)
        }
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
    if (!prompt.trim()) {
      alert('Please enter prompt/notes first')
      return
    }
    
    setLoading(true)
    try {
      // Call AI to generate/update invoice
      const response = await api.post('/api/ai/generate-invoice', {
        prompt,
        example_invoice: draftInvoice,
        reference_files: referenceFiles.map(f => f.content)
      })
      
      if (response.data.success) {
        const aiData = response.data.invoice_data || {}
        const mergedInvoice = {
          ...draftInvoice,
          ...aiData,
          // Preserve signature selection/name unless AI explicitly provides them
          signature_file: aiData.signature_file ?? draftInvoice.signature_file,
          signature_name: aiData.signature_name ?? draftInvoice.signature_name
        }
        setDraftInvoice(mergedInvoice)
        // Trigger preview update
        generatePreview(mergedInvoice)
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

      // If description matches item library, prefill curated/default rate
      if (field === 'description') {
        const match = itemCatalog.find(it => (it.description || '').toLowerCase() === String(value || '').toLowerCase())
        if (match) {
          const libRate = Number(match.curated_rate || match.default_rate || 0)
          const qty = parseFloat(newItems[index].quantity || 1)
          newItems[index].rate = libRate
          newItems[index].amount = qty * libRate
        }
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

  const addItemFromCatalog = (catalogItem) => {
    setDraftInvoice(prev => ({
      ...prev,
      items: [...prev.items, {
        description: catalogItem.description || '',
        quantity: 1,
        rate: Number(catalogItem.default_rate || 0),
        amount: Number(catalogItem.default_rate || 0)
      }]
    }))
  }

  const removeItem = (index) => {
    setDraftInvoice(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }))
  }


  const handleSaveDraft = () => {
    try {
      const payload = {
        draftInvoice,
        prompt,
        referenceFiles,
        selectedSignature,
        selectedExampleId: selectedExample?.id || null,
        savedAt: new Date().toISOString()
      }
      localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(payload))
      alert('✅ Draft saved')
    } catch (error) {
      console.error('Error saving draft:', error)
      alert('Error saving draft: ' + error.message)
    }
  }

  const handleLoadDraft = () => {
    try {
      const raw = localStorage.getItem(DRAFT_STORAGE_KEY)
      if (!raw) {
        alert('No saved draft found')
        return
      }

      const payload = JSON.parse(raw)
      const loadedDraft = payload?.draftInvoice
      if (!loadedDraft) {
        alert('Saved draft is invalid')
        return
      }

      setDraftInvoice(loadedDraft)
      setPrompt(payload?.prompt || '')
      setReferenceFiles(Array.isArray(payload?.referenceFiles) ? payload.referenceFiles : [])
      setSelectedSignature(payload?.selectedSignature || loadedDraft?.signature_file || null)

      if (payload?.selectedExampleId) {
        const match = exampleInvoices.find(ex => ex.id === payload.selectedExampleId)
        setSelectedExample(match || null)
      } else {
        setSelectedExample(null)
      }

      generatePreview(loadedDraft)
      alert('✅ Draft loaded')
    } catch (error) {
      console.error('Error loading draft:', error)
      alert('Error loading draft: ' + error.message)
    }
  }

  const handleGeneratePDF = async () => {
    setLoading(true)
    try {
      const response = await api.post('/api/invoice/create', draftInvoice)
      if (response.data.success) {
        // Extract just the filename from the path
        const filename = response.data.path.split('/').pop()
        
        // Create a descriptive filename: Rechnung_number_client_date.pdf
        // Clean client name: remove special chars, replace spaces with hyphens
        const clientName = draftInvoice.client.name
          .replace(/[^a-zA-Z0-9\s]/g, '')  // Remove special characters
          .replace(/\s+/g, '-')             // Replace spaces with hyphens
          .substring(0, 30)                 // Limit length
        
        // Clean invoice number (remove type prefix like "Rechnung_")
        const invoiceNum = draftInvoice.invoice_number
        
        // Format date as DD-MM-YYYY
        const dateStr = draftInvoice.date.replace(/\./g, '-')
        
        // Format: Rechnung_number_client_date (e.g., Rechnung_552421_Deutsche-Bahn_02-03-2026)
        const downloadName = `Rechnung_${invoiceNum}_${clientName}_${dateStr}`
        
        // Open the generated PDF in the viewer instead of downloading
        setViewingPDF({
          url: `${window.location.origin}/output/${filename}`,
          name: downloadName
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

  const calculateSubtotal = () => {
    return draftInvoice.items.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
  }

  const calculateTax = () => {
    return calculateSubtotal() * 0.19
  }

  const calculateTotal = () => {
    return calculateSubtotal() + calculateTax()
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
            onClick={() => document.getElementById('reference-file-input')?.click()}
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
            onClick={() => document.getElementById('signature-file-input')?.click()}
          >
            <div className="dropzone-content">
              <span className="dropzone-icon">✍️</span>
              <p className="dropzone-text">Signature Image</p>
              <input
                type="file"
                onChange={handleSignatureUpload}
                accept=".png,.jpg,.jpeg,.gif,.webp"
                style={{ display: 'none' }}
                id="signature-file-input"
              />
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', justifyContent: 'center', flexWrap: 'nowrap', margin: '10px 20px 0 20px' }}>
        <button
          className="btn-generate"
          onClick={handleSaveDraft}
          disabled={loading}
          style={{ padding: '8px 12px', fontSize: '12px', backgroundColor: '#2563eb' }}
        >
          💾 Save Draft
        </button>
        <button
          className="btn-generate"
          onClick={handleLoadDraft}
          disabled={loading}
          style={{ padding: '8px 12px', fontSize: '12px', backgroundColor: '#7c3aed' }}
        >
          📂 Load Draft
        </button>
        <button
          className="btn-generate"
          onClick={handleGeneratePDF}
          disabled={loading}
          style={{ padding: '8px 12px', fontSize: '12px', backgroundColor: '#059669' }}
        >
          {loading ? 'Generating…' : '📥 Generate PDF'}
        </button>
      </div>

      <div className="main-container">
        {/* Left Panel - Controls */}
        <div className="controls-panel">
          <div className="control-group">
            <label>Dokumenttyp</label>
            <select
              value={draftInvoice.type}
              onChange={(e) => handleTypeChange(e.target.value)}
              style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
            >
              <option value="Rechnung">Rechnung</option>
              <option value="Angebot">Angebot</option>
            </select>
          </div>

          <div className="control-group">
            <label>Example Invoice Import ({exampleInvoices.length} files in pool)</label>
            <p style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Drop a PDF in the top “Example Invoice PDF” dropzone to auto-scrape customer + billed items into the curated database.
            </p>
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
            {loading ? '⏳ Updating...' : '🔄 Update Draft (AI sets initial items)'}
          </button>
          
          {/* Signature Upload Section */}
          <div className="control-group">
            <label>Signature</label>

            {/* Compact selector instead of large gallery */}
            <div className="form-field" style={{ marginTop: '8px' }}>
              <label>Select uploaded signature</label>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                <select
                  value={draftInvoice.signature_file || selectedSignature || ''}
                  onChange={(e) => selectSignature(e.target.value)}
                  style={{ flex: 1 }}
                >
                  <option value="">— No signature selected —</option>
                  {signatures.map(sig => (
                    <option key={sig.filename} value={sig.filename}>
                      {sig.filename}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="btn-remove-small"
                  onClick={handleDeleteSignature}
                  title="Delete selected signature"
                >
                  🗑️
                </button>
              </div>
            </div>

            {(draftInvoice.signature_file || selectedSignature) && (
              <div style={{ marginTop: '10px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                <img
                  src={`${window.location.origin}/api/signatures/view/${draftInvoice.signature_file || selectedSignature}`}
                  alt="Selected signature"
                  style={{
                    width: '140px',
                    maxHeight: '56px',
                    objectFit: 'contain',
                    border: '1px solid #ddd',
                    borderRadius: '6px',
                    background: '#fff',
                    padding: '4px'
                  }}
                />
                <span style={{ fontSize: '12px', color: '#666' }}>
                  {draftInvoice.signature_file || selectedSignature}
                </span>
              </div>
            )}

            <div className="form-field" style={{ marginTop: '10px' }}>
              <label>Signature Name (footer)</label>
              <input
                type="text"
                value={draftInvoice.signature_name || ''}
                onChange={(e) => handleDraftFieldChange('signature_name', e.target.value)}
                placeholder="e.g., Florian Manhardt"
              />
            </div>

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
          </div>

          <div className="draft-form">
            <div className="form-row">
              <div className="form-field">
                <label>{draftInvoice.type} Number</label>
                <input
                  type="text"
                  value={draftInvoice.invoice_number}
                  onChange={(e) => handleDraftFieldChange('invoice_number', e.target.value)}
                  placeholder="5526…"
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

              <datalist id="item-library-options">
                {itemCatalog.slice(0, 300).map((it, idx) => (
                  <option key={`${it.description}-${idx}`} value={it.description}>
                    {it.job_type} • €{Number(it.curated_rate || it.default_rate || 0).toFixed(2)}
                  </option>
                ))}
              </datalist>
              
              {draftInvoice.items.map((item, index) => (
                <div key={index} className="item-row">
                  <div className="item-field item-description">
                    <label>Description</label>
                    <input
                      type="text"
                      value={item.description}
                      list="item-library-options"
                      onChange={(e) => handleItemChange(index, 'description', e.target.value)}
                      placeholder="Type or search from item library"
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
              <div style={{ fontSize: '13px' }}>Subtotal (Netto): €{calculateSubtotal().toFixed(2)}</div>
              <div style={{ fontSize: '13px' }}>MwSt (19%): €{calculateTax().toFixed(2)}</div>
              <strong>Total (Brutto): €{calculateTotal().toFixed(2)}</strong>
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
