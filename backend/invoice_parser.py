import os
import subprocess
import re
import zipfile
from PIL import Image
import pytesseract
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

class InvoiceParser:
    """Parse existing invoices to extract data"""
    
    def __init__(self, example_dir):
        self.example_dir = example_dir
    
    def extract_preview_from_pages(self, pages_file):
        """Extract preview image from .pages file"""
        try:
            with zipfile.ZipFile(pages_file, 'r') as zip_ref:
                # Extract preview.jpg
                preview_data = zip_ref.read('preview.jpg')
                return preview_data
        except Exception as e:
            print(f"Error extracting preview from {pages_file}: {e}")
            return None
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from PDF file"""
        try:
            if PdfReader is None:
                print("PyPDF2 not available, skipping PDF parsing")
                return ""
            
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF {pdf_file}: {e}")
            return ""
    
    def ocr_image(self, image_data):
        """Perform OCR on image data"""
        try:
            import io
            image = Image.open(io.BytesIO(image_data))
            text = pytesseract.image_to_string(image, lang='deu')
            return text
        except Exception as e:
            print(f"Error performing OCR: {e}")
            return ""
    
    def parse_invoice_text(self, text):
        """Parse invoice text to extract structured data"""
        data = {
            'invoice_number': '',
            'date': '',
            'client': {
                'name': '',
                'address': '',
                'city': ''
            },
            'items': [],
            'tax_rate': 19,
            'subtotal': 0,
            'tax': 0,
            'total': 0
        }
        
        # Extract invoice number
        invoice_match = re.search(r'Rechnungsnummer:\s*(\d+)', text)
        if invoice_match:
            data['invoice_number'] = invoice_match.group(1)
        
        # Extract date
        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', text)
        if date_match:
            data['date'] = date_match.group(1)
        
        # Extract tax rate
        tax_match = re.search(r'MwSt?\s*(\d+)%', text)
        if tax_match:
            data['tax_rate'] = int(tax_match.group(1))
        
        # Extract amounts (simple approach)
        amounts = re.findall(r'€\s*([\d,\.]+)', text)
        if amounts:
            try:
                # Last amount is usually total
                data['total'] = float(amounts[-1].replace(',', '.').replace(' ', ''))
            except:
                pass
        
        return data
    
    def parse_single_invoice(self, filepath):
        """Parse a single invoice file"""
        text = ""
        
        if filepath.endswith('.pages'):
            preview_data = self.extract_preview_from_pages(filepath)
            if preview_data:
                text = self.ocr_image(preview_data)
        elif filepath.endswith('.pdf'):
            text = self.extract_text_from_pdf(filepath)
        
        if text:
            return self.parse_invoice_text(text)
        return None
    
    def parse_all_examples(self):
        """Parse all example invoices in the directory"""
        examples = []
        
        if not os.path.exists(self.example_dir):
            return examples
        
        for filename in os.listdir(self.example_dir):
            if filename.endswith(('.pages', '.pdf')):
                filepath = os.path.join(self.example_dir, filename)
                data = self.parse_single_invoice(filepath)
                if data:
                    data['filename'] = filename
                    examples.append(data)
        
        return examples
