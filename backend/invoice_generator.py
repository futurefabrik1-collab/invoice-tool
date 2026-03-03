from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime

class InvoiceGenerator:
    """Generate invoices matching Future Fabrik format"""
    
    def __init__(self, templates_dir, output_dir):
        self.templates_dir = templates_dir
        self.output_dir = output_dir
        
        # Future Fabrik branding colors
        self.primary_color = HexColor('#000000')
        self.accent_color = HexColor('#FF0000')  # Adjust based on actual brand
        
    def calculate_totals(self, items):
        """Calculate subtotal, tax, and total from line items"""
        subtotal = 0
        for item in items:
            quantity = float(item.get('quantity', 0))
            rate = float(item.get('rate', 0))
            subtotal += quantity * rate
        
        tax_rate = 0.19  # 19% MwSt
        tax = subtotal * tax_rate
        total = subtotal + tax
        
        return {
            'subtotal': subtotal,
            'tax': tax,
            'total': total
        }
    
    def format_currency(self, amount):
        """Format amount as EUR currency"""
        return f"€ {amount:,.2f}".replace(',', ' ').replace('.', ',').replace(' ', '.')
    
    def generate_preview(self, data):
        """Generate a preview representation of the invoice"""
        totals = self.calculate_totals(data.get('items', []))
        
        return {
            'invoice_number': data.get('invoice_number', ''),
            'date': data.get('date', ''),
            'client': data.get('client', {}),
            'items': data.get('items', []),
            'subtotal': self.format_currency(totals['subtotal']),
            'tax': self.format_currency(totals['tax']),
            'total': self.format_currency(totals['total'])
        }
    
    def generate(self, data):
        """Generate invoice PDF matching Future Fabrik format exactly"""
        # Create filename
        invoice_type = data.get('type', 'Rechnung')
        invoice_number = data.get('invoice_number', datetime.now().strftime('%Y%m%d%H%M%S'))
        filename = f"{invoice_type}_{invoice_number}.pdf"
        output_path = os.path.join(self.output_dir, filename)
        
        # Create PDF
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # Define margins - LEFT COLUMN for company info, MAIN CONTENT starts after
        left_margin = 20*mm  # Left edge
        left_column_width = 40*mm  # Narrower column for company info
        main_content_start = left_margin + left_column_width + 10*mm  # More space before main content
        right_margin = width - 20*mm
        
        # Colors for elegant design
        grey_color = HexColor('#666666')
        light_grey = HexColor('#F0F0F0')
        
        # LOGO AND TITLE - Top of page, aligned with left page edge
        logo_path = os.path.join(self.templates_dir, 'logo.png')
        
        if os.path.exists(logo_path):
            # Extra huge logo at very top, aligned with left page edge (0mm from left)
            c.drawImage(logo_path, 0, height - 56*mm, width=140*mm, height=56*mm, preserveAspectRatio=True, mask='auto')
        
        # Future Fabrik text below logo
        c.setFont("Helvetica-Bold", 20)
        c.drawString(left_margin, height - 62*mm, "Future Fabrik")
        
        # LEFT COLUMN - Company info (starts below logo and text)
        y_pos = height - 70*mm  # Start below logo (56mm) + text + small gap
        
        # Document type (Rechnung/Angebot) - in left column
        c.setFont("Helvetica-Bold", 14)
        c.drawString(left_margin, y_pos, invoice_type)
        y_pos -= 8*mm
        
        # Company info in left column
        c.setFont("Helvetica", 7)
        company_info = [
            "Burnett & Manhardt GbR",
            "",
            "Mediendienstleistungen",
            "Foto / Video / Livestreams /",
            "Social Media",
            "",
            "Steuernummer: 232/151/37805",
            "",
            "BÜRO",
            "Klingenstraße 22",
            "04229 Leipzig",
            "",
            "TELEFON",
            "0178/1345105",
            "",
            "MAIL",
            "flo@futurefabrik.com",
            "",
            "INTERNET",
            "www.futurefabrik.com"
        ]
        
        for line in company_info:
            if line:
                c.drawString(left_margin, y_pos, line)
            y_pos -= 3*mm
        
        # MAIN CONTENT - starts after left column, aligned with company info
        y_main = height - 70*mm  # Aligned with left column company info start
        
        # DATUM - with grey background
        c.setFillColor(light_grey)
        c.rect(main_content_start - 2*mm, y_main - 1*mm, right_margin - main_content_start + 2*mm, 4*mm, fill=1, stroke=0)
        c.setFillColor(grey_color)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(main_content_start, y_main, "DATUM")
        y_main -= 5*mm
        c.setFillColor(HexColor('#000000'))
        c.setFont("Helvetica", 9)
        c.drawString(main_content_start, y_main, data.get('date', ''))
        y_main -= 8*mm
        
        # AN (Client) - with grey background
        c.setFillColor(light_grey)
        c.rect(main_content_start - 2*mm, y_main - 1*mm, right_margin - main_content_start + 2*mm, 4*mm, fill=1, stroke=0)
        c.setFillColor(grey_color)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(main_content_start, y_main, "AN")
        y_main -= 5*mm
        c.setFillColor(HexColor('#000000'))
        c.setFont("Helvetica", 9)
        client = data.get('client', {})
        client_lines = [
            client.get('name', ''),
            client.get('address', ''),
            client.get('city', '')
        ]
        for line in client_lines:
            if line:
                c.drawString(main_content_start, y_main, line)
                y_main -= 4*mm
        y_main -= 5*mm
        
        # Invoice/Angebot Number - with grey background
        invoice_number_label = "ANGEBOTSNUMMER:" if invoice_type == "Angebot" else "RECHNUNGSNUMMER:"
        c.setFillColor(light_grey)
        c.rect(main_content_start - 2*mm, y_main - 1*mm, right_margin - main_content_start + 2*mm, 4*mm, fill=1, stroke=0)
        c.setFillColor(grey_color)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(main_content_start, y_main, invoice_number_label)
        y_main -= 5*mm
        c.setFillColor(HexColor('#000000'))
        c.setFont("Helvetica", 9)
        c.drawString(main_content_start, y_main, data.get('invoice_number', ''))
        y_main -= 8*mm
        
        # ZEITRAUM - with grey background
        zeitraum = data.get('zeitraum', '')
        if zeitraum:
            c.setFillColor(light_grey)
            c.rect(main_content_start - 2*mm, y_main - 1*mm, right_margin - main_content_start + 2*mm, 4*mm, fill=1, stroke=0)
            c.setFillColor(grey_color)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(main_content_start, y_main, "ZEITRAUM:")
            y_main -= 5*mm
            c.setFillColor(HexColor('#000000'))
            c.setFont("Helvetica", 9)
            c.drawString(main_content_start, y_main, zeitraum)
            y_main -= 8*mm
        
        # EXPIRY (for Angebot) or DUE DATE (for Rechnung) - with grey background
        if invoice_type == "Angebot":
            # Angebot expiry date
            expiry = data.get('expiry_date', '')
            if expiry:
                c.setFillColor(light_grey)
                c.rect(main_content_start - 2*mm, y_main - 1*mm, right_margin - main_content_start + 2*mm, 4*mm, fill=1, stroke=0)
                c.setFillColor(grey_color)
                c.setFont("Helvetica-Bold", 7)
                c.drawString(main_content_start, y_main, "GÜLTIG BIS:")
                y_main -= 5*mm
                c.setFillColor(HexColor('#000000'))
                c.setFont("Helvetica", 9)
                c.drawString(main_content_start, y_main, expiry)
                y_main -= 8*mm
        else:
            # Rechnung due date
            due_date = data.get('due_date', '')
            if due_date:
                c.setFillColor(light_grey)
                c.rect(main_content_start - 2*mm, y_main - 1*mm, right_margin - main_content_start + 2*mm, 4*mm, fill=1, stroke=0)
                c.setFillColor(grey_color)
                c.setFont("Helvetica-Bold", 7)
                c.drawString(main_content_start, y_main, "ZAHLUNGSZIEL:")
                y_main -= 5*mm
                c.setFillColor(HexColor('#000000'))
                c.setFont("Helvetica", 9)
                c.drawString(main_content_start, y_main, due_date)
                y_main -= 8*mm
        
        # PROJEKTNAME (if provided) - with grey background
        project_name = data.get('project_name', '')
        if project_name:
            c.setFillColor(light_grey)
            c.rect(main_content_start - 2*mm, y_main - 1*mm, right_margin - main_content_start + 2*mm, 4*mm, fill=1, stroke=0)
            c.setFillColor(grey_color)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(main_content_start, y_main, "PROJEKTNAME:")
            y_main -= 5*mm
            c.setFillColor(HexColor('#000000'))
            c.setFont("Helvetica", 9)
            c.drawString(main_content_start, y_main, project_name)
            y_main -= 8*mm
        
        # PROJEKTBESCHREIBUNG (if provided) - concise bullet list for clean alignment
        project_desc = data.get('project_description', '')

        # Be resilient to AI output type mismatches (string/list/dict)
        if isinstance(project_desc, list):
            project_desc = "\n".join(str(x) for x in project_desc if x is not None)
        elif isinstance(project_desc, dict):
            project_desc = "\n".join(f"{k}: {v}" for k, v in project_desc.items())
        elif project_desc is None:
            project_desc = ''
        else:
            project_desc = str(project_desc)

        if project_desc and project_desc.strip():
            c.setFillColor(light_grey)
            c.rect(main_content_start - 2*mm, y_main - 1*mm, right_margin - main_content_start + 2*mm, 4*mm, fill=1, stroke=0)
            c.setFillColor(grey_color)
            c.setFont("Helvetica-Bold", 7)
            c.drawString(main_content_start, y_main, "PROJEKTBESCHREIBUNG:")
            y_main -= 5*mm

            c.setFillColor(HexColor('#000000'))
            c.setFont("Helvetica", 9)

            from textwrap import wrap
            # Keep bullets compact and visually aligned with other sections
            bullet_width_chars = 70

            # Build bullets from lines/semicolon-splits; fallback to sentence chunks
            raw_parts = []
            for line in project_desc.replace('•', '').split('\n'):
                raw_parts.extend([p.strip() for p in line.split(';') if p.strip()])

            bullets = raw_parts if raw_parts else [project_desc.strip()]
            bullets = bullets[:4]  # keep block compact

            for bullet in bullets:
                wrapped = wrap(bullet, width=bullet_width_chars)
                if not wrapped:
                    continue
                c.drawString(main_content_start, y_main, f"• {wrapped[0]}")
                y_main -= 4*mm
                # Optional continuation line for readability (max 2 lines per bullet)
                if len(wrapped) > 1:
                    c.drawString(main_content_start + 4*mm, y_main, wrapped[1])
                    y_main -= 4*mm

            y_main -= 3*mm
        
        # TABLE - Line items with grey header background
        y_main -= 8*mm  # More space before table
        
        # Table header with grey background
        c.setFillColor(light_grey)
        c.rect(main_content_start - 2*mm, y_main - 1*mm, right_margin - main_content_start + 2*mm, 5*mm, fill=1, stroke=0)
        c.setFillColor(grey_color)
        c.setFont("Helvetica-Bold", 7)
        c.drawString(main_content_start, y_main, "BESCHREIBUNG")
        c.drawRightString(main_content_start + 80*mm, y_main, "MENGE")
        c.drawRightString(main_content_start + 105*mm, y_main, "€/STÜCK")
        c.drawRightString(right_margin, y_main, "PREIS")
        
        y_main -= 6*mm
        c.setFillColor(HexColor('#000000'))
        
        # Draw horizontal line under headers
        c.setLineWidth(0.5)
        c.line(main_content_start, y_main, right_margin, y_main)
        y_main -= 5*mm
        
        # Line items with concise descriptions (1-2 lines per position)
        c.setFont("Helvetica", 8)
        items = data.get('items', [])
        from textwrap import wrap
        
        for idx, item in enumerate(items):
            quantity = float(item.get('quantity', 0))
            rate = float(item.get('rate', 0))
            total = quantity * rate
            
            # Description limited to 1-2 lines for stable alignment
            description = (item.get('description', '') or '').strip()
            desc_width = 48  # tuned to description column width
            wrapped_desc = wrap(description, width=desc_width) if description else ['']
            
            # Track starting position for this item
            item_start_y = y_main
            
            # Draw description (max 2 lines)
            for line in wrapped_desc[:2]:
                c.drawString(main_content_start, y_main, line)
                y_main -= 4*mm
            
            # Draw numbers at the top line of the item
            c.drawRightString(main_content_start + 80*mm, item_start_y, str(int(quantity)))
            c.drawRightString(main_content_start + 105*mm, item_start_y, f"€{rate:,.2f}".replace(',', '.').replace('.', ',', 1))
            c.drawRightString(right_margin, item_start_y, f"€{total:,.2f}".replace(',', '.').replace('.', ',', 1))
            
            # Add spacing between items
            y_main -= 3*mm
            
            # Light separator line between items (except last)
            if idx < len(items) - 1:
                c.setStrokeColor(HexColor('#E0E0E0'))
                c.setLineWidth(0.3)
                c.line(main_content_start, y_main, right_margin, y_main)
                c.setStrokeColor(HexColor('#000000'))
                y_main -= 3*mm
        
        # Totals section with grey background
        totals = self.calculate_totals(items)
        y_main -= 5*mm
        
        # Strong separator line before totals
        c.setLineWidth(1)
        c.line(main_content_start, y_main, right_margin, y_main)
        y_main -= 6*mm
        
        c.setFont("Helvetica", 8)
        # Zwischensumme Netto
        c.drawString(main_content_start, y_main, "Zwischensumme Netto")
        c.drawRightString(right_margin, y_main, f"€{totals['subtotal']:,.2f}".replace(',', '.').replace('.', ',', 1))
        y_main -= 5*mm
        
        # MwSt 19%
        c.drawString(main_content_start, y_main, "MwSt 19%")
        c.drawRightString(right_margin, y_main, f"€{totals['tax']:,.2f}".replace(',', '.').replace('.', ',', 1))
        y_main -= 6*mm
        
        # Summe (Total) - bold with grey background
        c.setFillColor(light_grey)
        c.rect(main_content_start - 2*mm, y_main - 2*mm, right_margin - main_content_start + 2*mm, 6*mm, fill=1, stroke=0)
        c.setFillColor(HexColor('#000000'))
        c.setFont("Helvetica-Bold", 10)
        c.drawString(main_content_start, y_main, "Summe")
        c.drawRightString(right_margin, y_main, f"€{totals['total']:,.2f}".replace(',', '.').replace('.', ',', 1))
        
        # Footer - aligned to main content
        y_footer = 50*mm
        c.setFont("Helvetica", 6)
        footer_text = "Alle kommerziellen Nutzungsrechte und Vervielfältigungsrechte werden mit Begleichen der Rechnung an Sie übertragen."
        c.drawString(main_content_start, y_footer, footer_text)
        
        # Signature area - lower right
        signature_filename = data.get('signature_file')
        if signature_filename:
            # Add uploaded signature image
            signatures_dir = os.path.join(os.path.dirname(self.templates_dir), 'signatures')
            signature_path = os.path.join(signatures_dir, signature_filename)
            if os.path.exists(signature_path):
                # Position signature in lower right
                sig_width = 50*mm
                sig_height = 20*mm
                sig_x = right_margin - sig_width
                sig_y = 20*mm
                c.drawImage(signature_path, sig_x, sig_y, width=sig_width, height=sig_height, preserveAspectRatio=True, mask='auto')
        else:
            # Default text signature if no image
            y_footer -= 5*mm
            c.setFont("Helvetica", 7)
            c.drawString(main_content_start, y_footer, "Mit freundlichen Grüßen,")
            y_footer -= 4*mm
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(main_content_start, y_footer, "Florian Manhardt")
        
        c.save()
        
        return output_path
