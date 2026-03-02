"""
Google Sheets Integration for Invoice Numbering
Tracks existing invoices and generates next invoice number
"""
import os
import pickle
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.pickle
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

class GoogleSheetsInvoiceTracker:
    def __init__(self, spreadsheet_id=None, range_name='Sheet1!A:C'):
        """
        Initialize Google Sheets integration
        
        Args:
            spreadsheet_id: The ID of the Google Sheet (from the URL)
            range_name: The range to read (e.g., 'Sheet1!A:C' for columns A, B, C)
        """
        self.spreadsheet_id = spreadsheet_id or os.getenv('GOOGLE_SHEETS_ID')
        self.range_name = range_name
        self.service = None
        self.credentials_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'credentials.json'
        )
        self.token_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'token.pickle'
        )
        
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        creds = None
        
        # Token file stores user's access and refresh tokens
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"credentials.json not found at {self.credentials_path}\n"
                        "Please download it from Google Cloud Console"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('sheets', 'v4', credentials=creds)
        return True
    
    def get_all_invoice_numbers(self):
        """
        Get all invoice numbers from the spreadsheet
        
        Returns:
            list: All invoice numbers found in the sheet
        """
        if not self.service:
            self.authenticate()
        
        if not self.spreadsheet_id:
            print("Warning: No spreadsheet ID configured")
            return []
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                print('No data found in spreadsheet')
                return []
            
            # Extract invoice numbers (assuming they're in the first column)
            invoice_numbers = []
            for row in values:
                if row:  # Skip empty rows
                    invoice_num = str(row[0]).strip()
                    # Skip header row
                    if not invoice_num.lower().startswith('invoice'):
                        invoice_numbers.append(invoice_num)
            
            return invoice_numbers
            
        except HttpError as err:
            print(f'Error accessing Google Sheets: {err}')
            return []
    
    def get_next_invoice_number(self, prefix=''):
        """
        Generate the next invoice number based on existing invoices
        
        Args:
            prefix: Optional prefix for invoice numbers (e.g., '2025-')
        
        Returns:
            str: The next invoice number
        """
        existing_numbers = self.get_all_invoice_numbers()
        
        if not existing_numbers:
            # No existing invoices, start with prefix + 001
            return f"{prefix}001"
        
        # Extract numeric part from invoice numbers
        numeric_values = []
        for num in existing_numbers:
            # Remove prefix if present
            if prefix and num.startswith(prefix):
                num = num[len(prefix):]
            
            # Extract numeric part
            try:
                # Try to parse as integer
                numeric_values.append(int(num))
            except ValueError:
                # If it contains non-numeric characters, try to extract numbers
                import re
                numbers = re.findall(r'\d+', num)
                if numbers:
                    numeric_values.append(int(numbers[-1]))  # Take last number found
        
        if not numeric_values:
            return f"{prefix}001"
        
        # Get max and increment
        next_num = max(numeric_values) + 1
        
        # Format with leading zeros (same width as existing numbers)
        # Find the maximum width used
        max_width = max(len(str(v)) for v in numeric_values)
        max_width = max(max_width, 3)  # At least 3 digits
        
        return f"{prefix}{str(next_num).zfill(max_width)}"
    
    def search_invoice(self, invoice_number):
        """
        Search for a specific invoice number in the spreadsheet
        
        Args:
            invoice_number: The invoice number to search for
        
        Returns:
            dict: Invoice data if found, None otherwise
        """
        if not self.service:
            self.authenticate()
        
        if not self.spreadsheet_id:
            return None
        
        try:
            sheet = self.service.spreadsheets()
            result = sheet.values().get(
                spreadsheetId=self.spreadsheet_id,
                range=self.range_name
            ).execute()
            
            values = result.get('values', [])
            
            for i, row in enumerate(values):
                if row and str(row[0]).strip() == str(invoice_number):
                    # Assuming format: Invoice# | Date | Client | Amount
                    return {
                        'invoice_number': row[0] if len(row) > 0 else '',
                        'date': row[1] if len(row) > 1 else '',
                        'client': row[2] if len(row) > 2 else '',
                        'amount': row[3] if len(row) > 3 else '',
                        'row': i + 1
                    }
            
            return None
            
        except HttpError as err:
            print(f'Error searching invoice: {err}')
            return None
