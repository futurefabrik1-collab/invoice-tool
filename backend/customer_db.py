"""
Customer Database Manager
Stores and retrieves customer information from previous invoices
"""
import json
import os
from datetime import datetime

class CustomerDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.customers = self._load_db()
    
    def _load_db(self):
        """Load customer database from JSON file"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading customer DB: {e}")
                return {}
        return {}
    
    def _save_db(self):
        """Save customer database to JSON file"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.customers, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving customer DB: {e}")
    
    def add_or_update_customer(self, customer_data, invoice_number=None):
        """
        Add or update customer information
        customer_data should contain: name, address, city, etc.
        """
        if not customer_data or not customer_data.get('name'):
            return None
        
        customer_name = customer_data['name'].strip()
        
        # Create or update customer entry
        if customer_name not in self.customers:
            self.customers[customer_name] = {
                'name': customer_name,
                'address': customer_data.get('address', ''),
                'city': customer_data.get('city', ''),
                'email': customer_data.get('email', ''),
                'first_seen': datetime.now().isoformat(),
                'last_used': datetime.now().isoformat(),
                'invoice_count': 1,
                'invoices': [invoice_number] if invoice_number else []
            }
        else:
            # Update existing customer
            self.customers[customer_name]['address'] = customer_data.get('address', self.customers[customer_name].get('address', ''))
            self.customers[customer_name]['city'] = customer_data.get('city', self.customers[customer_name].get('city', ''))
            self.customers[customer_name]['email'] = customer_data.get('email', self.customers[customer_name].get('email', ''))
            self.customers[customer_name]['last_used'] = datetime.now().isoformat()
            self.customers[customer_name]['invoice_count'] = self.customers[customer_name].get('invoice_count', 0) + 1
            
            if invoice_number:
                invoices = self.customers[customer_name].get('invoices', [])
                if invoice_number not in invoices:
                    invoices.append(invoice_number)
                self.customers[customer_name]['invoices'] = invoices
        
        self._save_db()
        return self.customers[customer_name]
    
    def get_customer(self, customer_name):
        """Get customer by name"""
        return self.customers.get(customer_name)
    
    def search_customers(self, query):
        """Search customers by name (partial match)"""
        query = query.lower()
        results = []
        for name, data in self.customers.items():
            if query in name.lower():
                results.append(data)
        return results
    
    def get_all_customers(self):
        """Get all customers sorted by last used"""
        customers_list = list(self.customers.values())
        customers_list.sort(key=lambda x: x.get('last_used', ''), reverse=True)
        return customers_list
    
    def get_recent_customers(self, limit=10):
        """Get most recently used customers"""
        return self.get_all_customers()[:limit]
