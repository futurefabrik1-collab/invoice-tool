"""
Extract text from invoice PDFs for AI context
"""
import os
import PyPDF2

def extract_text_from_pdf(pdf_path):
    """Extract text content from a PDF file"""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None

def get_example_invoice_text(example_name, example_dir):
    """Get text content from an example invoice by name"""
    pdf_path = os.path.join(example_dir, example_name)
    if not os.path.exists(pdf_path):
        # Try with .pdf extension
        pdf_path = os.path.join(example_dir, f"{example_name}.pdf")
    
    if os.path.exists(pdf_path):
        return extract_text_from_pdf(pdf_path)
    return None
