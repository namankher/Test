import os
from datetime import datetime, timedelta
from typing import List
import uuid
from app.models.database import Quote, Part, CostBreakdown
from app.models.schemas import ClientQuote, ClientQuoteItem

class QuoteGenerator:
    """Generate professional client-facing quotes"""
    
    def __init__(self):
        # Company information from environment variables
        self.company_name = os.getenv("COMPANY_NAME", "Advanced Manufacturing Solutions")
        self.company_address = os.getenv("COMPANY_ADDRESS", "123 Manufacturing Street\nIndustrial Park, State 12345")
        self.company_email = os.getenv("COMPANY_EMAIL", "quotes@advancedmfg.com")
        self.company_phone = os.getenv("COMPANY_PHONE", "+1 (555) 123-4567")
        self.company_website = os.getenv("COMPANY_WEBSITE", "www.advancedmfg.com")
        
        # Quote validity period
        self.quote_validity_days = int(os.getenv("QUOTE_VALIDITY_DAYS", 30))
        
        # Terms and conditions
        self.terms_and_conditions = self._get_terms_and_conditions()
    
    async def generate_client_quote(
        self,
        quote: Quote,
        parts: List[Part],
        cost_breakdown: CostBreakdown,
        include_cost_breakdown: bool = False
    ) -> ClientQuote:
        """Generate a professional client-facing quote"""
        
        # Generate quote number
        quote_number = self._generate_quote_number(quote.id)
        
        # Create quote items
        quote_items = self._create_quote_items(parts, cost_breakdown)
        
        # Calculate totals
        subtotal = cost_breakdown.total_cost
        tax_rate = float(os.getenv("TAX_RATE", 0.0875))  # 8.75% default tax
        tax_amount = subtotal * tax_rate if tax_rate > 0 else None
        
        shipping_cost = self._calculate_shipping_cost(parts, cost_breakdown.quantity)
        
        total = subtotal + (tax_amount or 0) + (shipping_cost or 0)
        
        # Calculate delivery date
        delivery_date = datetime.now() + timedelta(days=cost_breakdown.delivery_days)
        
        # Generate client quote
        client_quote = ClientQuote(
            quote_number=quote_number,
            client_name=quote.client_name,
            client_email=quote.client_email,
            quote_date=datetime.now(),
            valid_until=datetime.now() + timedelta(days=self.quote_validity_days),
            items=quote_items,
            subtotal=round(subtotal, 2),
            tax=round(tax_amount, 2) if tax_amount else None,
            shipping=round(shipping_cost, 2) if shipping_cost else None,
            total=round(total, 2),
            terms_and_conditions=self.terms_and_conditions,
            notes=self._generate_quote_notes(quote, parts, cost_breakdown)
        )
        
        return client_quote
    
    def _generate_quote_number(self, quote_id: str) -> str:
        """Generate a professional quote number"""
        
        # Format: QTE-YYYY-MM-XXXXX
        current_date = datetime.now()
        year = current_date.strftime("%Y")
        month = current_date.strftime("%m")
        
        # Use last 5 characters of quote_id as unique identifier
        unique_id = quote_id[-5:].upper()
        
        return f"QTE-{year}-{month}-{unique_id}"
    
    def _create_quote_items(self, parts: List[Part], cost_breakdown: CostBreakdown) -> List[ClientQuoteItem]:
        """Create client quote items from parts"""
        
        items = []
        quantity = cost_breakdown.quantity
        
        if len(parts) == 1:
            # Single part - show unit pricing
            part = parts[0]
            unit_price = cost_breakdown.total_cost / quantity
            
            items.append(ClientQuoteItem(
                part_name=part.part_name,
                quantity=quantity,
                unit_price=round(unit_price, 2),
                total_price=round(cost_breakdown.total_cost, 2),
                delivery_time=f"{cost_breakdown.delivery_days} business days"
            ))
        else:
            # Multiple parts - show as assembly or individual items
            total_per_part = cost_breakdown.total_cost / len(parts)
            
            for i, part in enumerate(parts):
                items.append(ClientQuoteItem(
                    part_name=part.part_name,
                    quantity=quantity,
                    unit_price=round(total_per_part / quantity, 2),
                    total_price=round(total_per_part, 2),
                    delivery_time=f"{cost_breakdown.delivery_days} business days"
                ))
        
        return items
    
    def _calculate_shipping_cost(self, parts: List[Part], quantity: int) -> float:
        """Calculate shipping cost based on parts size and weight"""
        
        try:
            # Estimate total weight and volume
            total_weight = 0
            total_volume = 0
            
            for part in parts:
                # Get material density (g/cm³)
                material_density = {
                    'aluminum': 2.7,
                    'steel': 7.85,
                    'brass': 8.5,
                    'titanium': 4.5
                }.get(part.material_type, 3.0)
                
                # Calculate weight (kg)
                volume_cm3 = (part.volume or 1000) / 1000  # Convert mm³ to cm³
                weight_kg = (volume_cm3 * material_density) / 1000
                
                total_weight += weight_kg * quantity
                total_volume += volume_cm3 * quantity
            
            # Shipping cost calculation
            if total_weight <= 1:  # Less than 1kg
                return 15.0
            elif total_weight <= 5:  # 1-5kg
                return 25.0
            elif total_weight <= 10:  # 5-10kg
                return 35.0
            elif total_weight <= 25:  # 10-25kg
                return 50.0
            else:  # Over 25kg
                return 75.0 + (total_weight - 25) * 2.0  # $2 per additional kg
            
        except Exception as e:
            print(f"Error calculating shipping cost: {str(e)}")
            return 25.0  # Default shipping cost
    
    def _generate_quote_notes(self, quote: Quote, parts: List[Part], cost_breakdown: CostBreakdown) -> str:
        """Generate professional notes for the quote"""
        
        notes = []
        
        # Lead time note
        if cost_breakdown.delivery_days <= 7:
            notes.append("• Expedited delivery requested - additional charges apply")
        elif cost_breakdown.delivery_days <= 14:
            notes.append("• Standard lead time with priority processing")
        
        # Rush order note
        if cost_breakdown.rush_order:
            notes.append("• Rush order processing - 25% surcharge included")
        
        # Quantity note
        if cost_breakdown.quantity > 100:
            notes.append("• Volume discount applied for large quantity order")
        elif cost_breakdown.quantity == 1:
            notes.append("• Prototype/single unit pricing")
        
        # Material notes
        materials = list(set(part.material_type for part in parts))
        if len(materials) == 1:
            notes.append(f"• Material: {materials[0].title()} grade {parts[0].material_grade}")
        else:
            notes.append(f"• Multiple materials: {', '.join(material.title() for material in materials)}")
        
        # Complexity notes
        avg_complexity = sum(part.complexity_score or 0.5 for part in parts) / len(parts)
        if avg_complexity > 0.8:
            notes.append("• High precision machining required - extended lead time")
        elif avg_complexity < 0.3:
            notes.append("• Standard machining processes - efficient production")
        
        # Quality assurance
        notes.append("• All parts include quality inspection per our standard procedures")
        notes.append("• Material certifications available upon request")
        
        # Payment terms
        notes.append("• Payment terms: Net 30 days from invoice date")
        notes.append("• 50% deposit required for orders over $5,000")
        
        return "\n".join(notes)
    
    def _get_terms_and_conditions(self) -> str:
        """Get standard terms and conditions"""
        
        return """
TERMS AND CONDITIONS

1. PRICING: Prices are valid for 30 days from quote date and are subject to change without notice.

2. PAYMENT: Payment terms are Net 30 days from invoice date. Orders over $5,000 require 50% deposit.

3. DELIVERY: Delivery dates are estimates and are subject to material availability and production schedule.

4. QUALITY: All parts are manufactured to specified tolerances and undergo quality inspection.

5. MATERIALS: Material certifications available upon request. Customer is responsible for specifying required certifications.

6. CHANGES: Any changes to specifications after order confirmation may result in additional charges and delivery delays.

7. LIABILITY: Our liability is limited to the cost of replacement parts. We are not liable for consequential damages.

8. RETURNS: Custom manufactured parts are non-returnable unless defective.

9. FORCE MAJEURE: We are not liable for delays due to circumstances beyond our control.

10. GOVERNING LAW: This quote is governed by the laws of [State/Province].

For questions about this quote, please contact us at {email} or {phone}.
        """.format(
            email=self.company_email,
            phone=self.company_phone
        ).strip()
    
    def generate_quote_pdf(self, client_quote: ClientQuote) -> bytes:
        """Generate PDF version of the quote (placeholder for future implementation)"""
        
        # This would use a library like ReportLab or WeasyPrint to generate PDF
        # For now, return a placeholder
        
        pdf_content = f"""
PDF QUOTE: {client_quote.quote_number}

{self.company_name}
{self.company_address}
{self.company_phone}
{self.company_email}

Quote Date: {client_quote.quote_date.strftime('%B %d, %Y')}
Valid Until: {client_quote.valid_until.strftime('%B %d, %Y')}

Bill To:
{client_quote.client_name}
{client_quote.client_email}

ITEMS:
"""
        
        for item in client_quote.items:
            pdf_content += f"""
{item.part_name}
Quantity: {item.quantity} @ ${item.unit_price:.2f} each
Total: ${item.total_price:.2f}
Delivery: {item.delivery_time}
"""
        
        pdf_content += f"""

Subtotal: ${client_quote.subtotal:.2f}
"""
        
        if client_quote.tax:
            pdf_content += f"Tax: ${client_quote.tax:.2f}\n"
        
        if client_quote.shipping:
            pdf_content += f"Shipping: ${client_quote.shipping:.2f}\n"
        
        pdf_content += f"""
TOTAL: ${client_quote.total:.2f}

NOTES:
{client_quote.notes}

{client_quote.terms_and_conditions}
"""
        
        return pdf_content.encode('utf-8')
    
    def format_quote_email(self, client_quote: ClientQuote) -> dict:
        """Format quote for email delivery"""
        
        email_subject = f"Quote {client_quote.quote_number} - {self.company_name}"
        
        email_body = f"""
Dear {client_quote.client_name},

Thank you for your interest in our manufacturing services. Please find your requested quote below:

Quote Number: {client_quote.quote_number}
Quote Date: {client_quote.quote_date.strftime('%B %d, %Y')}
Valid Until: {client_quote.valid_until.strftime('%B %d, %Y')}

QUOTED ITEMS:
"""
        
        for item in client_quote.items:
            email_body += f"""
• {item.part_name}
  Quantity: {item.quantity}
  Unit Price: ${item.unit_price:.2f}
  Total: ${item.total_price:.2f}
  Delivery Time: {item.delivery_time}
"""
        
        email_body += f"""

QUOTE SUMMARY:
Subtotal: ${client_quote.subtotal:.2f}
"""
        
        if client_quote.tax:
            email_body += f"Tax: ${client_quote.tax:.2f}\n"
        
        if client_quote.shipping:
            email_body += f"Shipping: ${client_quote.shipping:.2f}\n"
        
        email_body += f"""
TOTAL: ${client_quote.total:.2f}

IMPORTANT NOTES:
{client_quote.notes}

To proceed with this order, please reply to this email with your approval. We will then send a formal purchase order for your signature.

If you have any questions about this quote, please don't hesitate to contact us.

Best regards,

{self.company_name}
{self.company_phone}
{self.company_email}
{self.company_website}

---
This quote is valid until {client_quote.valid_until.strftime('%B %d, %Y')}
"""
        
        return {
            "subject": email_subject,
            "body": email_body,
            "to": client_quote.client_email,
            "from": self.company_email
        }