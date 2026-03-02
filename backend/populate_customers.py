"""
Populate customer database from all example invoices
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

from customer_db import CustomerDatabase
from extract_invoice_text import extract_text_from_pdf
from ai_invoice_assistant import AIInvoiceAssistant

def populate_customers_from_examples(example_dir, customer_db_path):
    """Extract customer info from all example PDFs and populate database"""
    
    customer_db = CustomerDatabase(customer_db_path)
    ai_assistant = AIInvoiceAssistant()
    
    if not ai_assistant.client:
        print("Warning: No OpenAI API key. Cannot extract customers.")
        return 0
    
    print(f"Scanning directory: {example_dir}")
    
    if not os.path.exists(example_dir):
        print(f"Error: Directory not found: {example_dir}")
        return 0
    
    pdf_files = [f for f in os.listdir(example_dir) if f.endswith('.pdf')]
    print(f"Found {len(pdf_files)} PDF files")
    
    customers_added = 0
    
    for pdf_file in pdf_files:
        print(f"\nProcessing: {pdf_file}")
        pdf_path = os.path.join(example_dir, pdf_file)
        
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        if not text:
            print(f"  ⚠️  Could not extract text")
            continue
        
        # Use AI to extract customer info
        try:
            prompt = "Extract ONLY the client/customer information from this invoice. Return just the client details."
            invoice_data = ai_assistant.generate_invoice_from_prompt(
                prompt,
                example_invoice=None,
                reference_files=[f"Invoice text:\n{text[:2000]}"]  # First 2000 chars
            )
            
            if invoice_data and invoice_data.get('client'):
                client = invoice_data['client']
                if client.get('name'):
                    # Extract invoice number from filename or text
                    invoice_num = pdf_file.replace('.pdf', '')
                    
                    # Add to database
                    customer_db.add_or_update_customer(client, invoice_num)
                    print(f"  ✅ Added: {client['name']}")
                    customers_added += 1
                else:
                    print(f"  ⚠️  No client name found")
            else:
                print(f"  ⚠️  No client info extracted")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            continue
    
    print(f"\n{'='*50}")
    print(f"Total customers added/updated: {customers_added}")
    print(f"Database location: {customer_db_path}")
    
    return customers_added

if __name__ == "__main__":
    # Set up paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    EXAMPLE_DIR = os.path.join(BASE_DIR, 'example-invoices')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    CUSTOMER_DB_PATH = os.path.join(DATA_DIR, 'customers.json')
    
    print("="*50)
    print("  Customer Database Population Tool")
    print("="*50)
    
    count = populate_customers_from_examples(EXAMPLE_DIR, CUSTOMER_DB_PATH)
    
    if count > 0:
        print("\n✅ Customer database populated successfully!")
        print("\nYou can now:")
        print("1. Restart the backend")
        print("2. Refresh your browser")
        print("3. See all customers in the dropdown")
    else:
        print("\n⚠️  No customers were added. Check that:")
        print("1. OPENAI_API_KEY is set")
        print("2. PDF files exist in example-invoices/")
        print("3. PDFs contain readable text")
