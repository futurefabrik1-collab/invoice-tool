"""
AI Invoice Assistant
Uses OpenAI to generate invoice content from prompts and reference documents
"""
import os
import json
from openai import OpenAI

class AIInvoiceAssistant:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not set. AI features will be limited.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def generate_invoice_from_prompt(self, prompt, example_invoice=None, reference_files=None):
        """
        Generate invoice data from a text prompt
        
        Args:
            prompt: User's description of what the invoice should contain
            example_invoice: Optional example invoice data to use as template
            reference_files: Optional list of reference file contents
        
        Returns:
            dict: Invoice data structure
        """
        if not self.client:
            # Fallback: return basic structure if no API key
            return self._generate_basic_invoice(prompt, example_invoice)
        
        # Build the system message
        system_msg = """You are an expert invoice generator for Future Fabrik, a creative production company specializing in video production, 3D visualization, livestreaming, and creative services.

IMPORTANT: Based on analyzing 156 real Future Fabrik invoices, use intelligent service bundling:

COMMON SERVICE BUNDLES:
1. Video Production Package: Filming (3-5 days @ €850/day) + Post-Production (5-10 days @ €750/day) + Mastering (1 day @ €750)
2. 3D Visualization Package: Modeling (10-20 hours @ €650/hour) + Rendering (5-10 hours @ €650/hour) + Integration (3-5 hours @ €650/hour)
3. Livestream Package: Technical Setup (1 day @ €850) + Moderation (per event @ €750) + Post-Production (2-3 days @ €750/day)
4. Workshop/Training: Facilitation (1-2 days @ €850/day) + Materials preparation (half day @ €400) + Livestream documentation (optional, €850)
5. Corporate Video: On-site filming (2-3 days @ €850/day) + Editing (3-5 days @ €750/day) + 3D elements if technical (10 hours @ €650/hour)

PRICING STANDARDS (from 156 examples):
- Video day rate: €850/day (on-site filming, direction, full equipment)
- Post-production: €750/day (editing, color grading, sound design)
- 3D work: €650/hour (visualization, rendering, animation)
- Livestreaming: €850 setup + €750/event for moderation
- Workshop facilitation: €850/day

INTELLIGENT BUNDLING RULES:
- If prompt mentions "video" → suggest filming + post-production + mastering
- If prompt mentions "3D" or "visualization" → suggest modeling + rendering + integration
- If prompt mentions "livestream" or "event" → suggest setup + moderation + optional recording
- If prompt mentions "technical" or "CAD" → add 3D visualization to video packages
- If prompt mentions "training" or "workshop" → suggest facilitation + optional livestream documentation

Generate invoice data in the following JSON format:
{
    "type": "Rechnung" or "Angebot",
    "invoice_number": "string",
    "date": "DD.MM.YYYY",
    "zeitraum": "string (e.g., '01.02.2026 - 28.02.2026')",
    "expiry_date": "string (DD.MM.YYYY - ONLY for Angebot, typically 30 days from date)",
    "due_date": "string (e.g., '14 Tage netto' - ONLY for Rechnung)",
    "client": {
        "name": "string",
        "address": "string",
        "city": "string"
    },
    "project_name": "string (optional)",
    "project_description": "string (3-4 concise bullet points using '\u2022 ', each bullet practical and clear)",
    "items": [
        {
            "description": "string (brief item description, target 1 line, max 2 lines in PDF)",
            "quantity": number,
            "rate": number,
            "amount": number
        }
    ],
    "notes": "string (optional payment terms, thank you note, etc.)"
}

IMPORTANT:
- If type is "Angebot": include expiry_date (30 days from date), do NOT include due_date
- If type is "Rechnung": include due_date (e.g., "14 Tage netto"), do NOT include expiry_date

IMPORTANT for project_description:
- Write 3-4 concise bullet points (prefix each with "• ")
- Keep each bullet short (ideally one line, max two lines in PDF)
- Focus on scope, key deliverables, and timeline/quality notes
- Avoid long paragraphs
- Use context from reference documents if provided

IMPORTANT for service bundling:
- Analyze the prompt and reference documents to understand project needs
- If reference files include CURATED_DATABASE_CONTEXT, treat it as highest-priority guidance for job types/descriptions/rates
- Prefer catalog-matching line items over generic defaults whenever possible
- For baustelle/timelapse/construction prompts, prioritize timelapse/construction monitoring item patterns when present in context
- Suggest complete, realistic service packages (not just one item)
- Use standard Future Fabrik pricing from the examples above unless curated context provides a better match
- Bundle related services intelligently (e.g., video needs editing, 3D needs rendering)
- Provide detailed descriptions for each line item
- Quantities should be realistic for the project scope

Extract all relevant information from the user's prompt. If information is missing, make reasonable assumptions based on context.
For line items, calculate amount = quantity × rate.
"""
        
        # Build the user message
        user_msg = f"Create an invoice based on this prompt:\n\n{prompt}"
        
        if example_invoice:
            user_msg += f"\n\nUse this example invoice as a template for structure and formatting:\n{json.dumps(example_invoice, indent=2, ensure_ascii=False)}"
        
        if reference_files:
            user_msg += f"\n\nReference files provided:\n"
            for i, ref in enumerate(reference_files, 1):
                user_msg += f"\n--- File {i} ---\n{ref}\n"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini which supports JSON mode
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return self._generate_basic_invoice(prompt, example_invoice)
    
    def _generate_basic_invoice(self, prompt, example_invoice=None):
        """Fallback method when API is not available"""
        base_structure = {
            "type": "Rechnung",
            "invoice_number": "",
            "date": "",
            "client": {
                "name": "",
                "address": "",
                "city": ""
            },
            "items": [],
            "notes": prompt  # Store the prompt in notes for manual editing
        }
        
        # If example provided, copy its structure
        if example_invoice:
            base_structure['client'] = example_invoice.get('client', base_structure['client'])
            if example_invoice.get('items'):
                base_structure['items'] = [example_invoice['items'][0].copy()]
        
        return base_structure
    
    def update_invoice_from_prompt(self, current_invoice, update_prompt):
        """
        Update an existing invoice based on a new prompt
        
        Args:
            current_invoice: The current invoice data
            update_prompt: What to change/update
        
        Returns:
            dict: Updated invoice data
        """
        if not self.client:
            return current_invoice
        
        system_msg = """You are helping update an existing invoice. 
The user will provide the current invoice data and describe what changes they want.
Return the complete updated invoice in the same JSON format."""
        
        user_msg = f"""Current invoice:
{json.dumps(current_invoice, indent=2, ensure_ascii=False)}

Update request: {update_prompt}

Return the complete updated invoice."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini which supports JSON mode
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            import traceback
            print(f"Error updating invoice: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
            return current_invoice
