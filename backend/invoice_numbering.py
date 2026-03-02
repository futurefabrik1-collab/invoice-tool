"""
Invoice and Angebot numbering system
Maintains separate sequences for Rechnung and Angebot
"""
import os
import json
from datetime import datetime

class InvoiceNumbering:
    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.numbering_file = os.path.join(data_dir, 'invoice_numbering.json')
        self.numbering = self._load_numbering()
    
    def _load_numbering(self):
        """Load numbering data from file"""
        if os.path.exists(self.numbering_file):
            try:
                with open(self.numbering_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading numbering: {e}")
                return self._get_default_numbering()
        return self._get_default_numbering()
    
    def _get_default_numbering(self):
        """Get default numbering structure"""
        return {
            'rechnung': {
                'last_number': 0,
                'prefix': '',
                'last_date': None
            },
            'angebot': {
                'last_number': 0,
                'prefix': '',
                'last_date': None
            }
        }
    
    def _save_numbering(self):
        """Save numbering data to file"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            with open(self.numbering_file, 'w') as f:
                json.dump(self.numbering, f, indent=2)
        except Exception as e:
            print(f"Error saving numbering: {e}")
    
    def get_next_number(self, doc_type='Rechnung', prefix=''):
        """
        Get next invoice/angebot number
        
        Args:
            doc_type: 'Rechnung' or 'Angebot'
            prefix: Optional prefix (e.g., 'AFF')
        
        Returns:
            str: Next document number
        """
        key = doc_type.lower()
        
        if key not in self.numbering:
            self.numbering[key] = self._get_default_numbering()[key]
        
        # Increment number
        current = self.numbering[key]['last_number']
        next_num = current + 1
        
        # Update
        self.numbering[key]['last_number'] = next_num
        self.numbering[key]['prefix'] = prefix
        self.numbering[key]['last_date'] = datetime.now().isoformat()
        
        self._save_numbering()
        
        # Format number
        if prefix:
            return f"{prefix}{next_num:06d}"
        else:
            return f"{next_num:06d}"
    
    def get_current_number(self, doc_type='Rechnung'):
        """Get the current (last used) number without incrementing"""
        key = doc_type.lower()
        if key not in self.numbering:
            return 0
        return self.numbering[key]['last_number']
    
    def set_number(self, doc_type, number):
        """Manually set the current number (for initialization from Google Sheets)"""
        key = doc_type.lower()
        if key not in self.numbering:
            self.numbering[key] = self._get_default_numbering()[key]
        
        # Extract numeric part if prefix exists
        numeric_part = number
        if isinstance(number, str):
            # Try to extract number from end of string
            import re
            match = re.search(r'(\d+)$', number)
            if match:
                numeric_part = int(match.group(1))
            else:
                try:
                    numeric_part = int(number)
                except:
                    numeric_part = 0
        
        self.numbering[key]['last_number'] = int(numeric_part)
        self._save_numbering()
