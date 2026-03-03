from database.models import Invoice, MRS, MRSItem, CompanyProfile
from datetime import datetime, timedelta
import random
import string
import os
import base64

class InvoiceService:
    @staticmethod
    def generate_invoice_no():
        """Generate a continuous unique invoice number: INV-YYYY-XXXX"""
        now = datetime.now()
        year = now.strftime("%Y")
        
        # Count existing invoices for this year to get next sequence
        prefix = f"INV-{year}-"
        count = Invoice.select().where(Invoice.invoice_no.startswith(prefix)).count()
        next_seq = count + 1
        
        return f"{prefix}{next_seq:04d}"

    @staticmethod
    def create_invoice_from_mrs(mrs_id, client_name=None, client_address=None, client_gstin=None, due_date=None):
        mrs = MRS.get_by_id(mrs_id)
        
        # Calculate totals
        total_amount = 0.0
        for item in mrs.items:
            qty = item.quantity_issued if item.quantity_issued > 0 else item.quantity_requested
            total_amount += qty * item.material.unit_cost
            
        # Use tax rate from Company Profile
        from database.models import CompanyProfile
        profile = CompanyProfile.get_or_none()
        gst_rate = (profile.default_tax_rate / 100.0) if profile else 0.18
            
        tax_amount = total_amount * gst_rate
        grand_total = total_amount + tax_amount
        
        # Capture Company Profile Snapshot
        profile = CompanyProfile.get_or_none()
        company_logo_data = None
        if profile and profile.logo_path and os.path.exists(profile.logo_path):
            try:
                with open(profile.logo_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode()
                    ext = os.path.splitext(profile.logo_path)[1].lower().replace('.', '')
                    if ext == 'jpg': ext = 'jpeg'
                    company_logo_data = f"data:image/{ext};base64,{encoded_string}"
            except Exception as e:
                print(f"Error encoding logo for snapshot: {e}")

        invoice = Invoice.create(
            invoice_no=InvoiceService.generate_invoice_no(),
            mrs=mrs,
            client_name=client_name,
            client_address=client_address,
            client_gstin=client_gstin,
            gst_percentage=gst_rate * 100,
            total_amount=total_amount,
            tax_amount=tax_amount,
            grand_total=grand_total,
            status='DRAFT',
            due_date=due_date or (datetime.now() + timedelta(days=14)).date(),
            
            # Snapshots
            company_name=profile.name if profile else "TEXKNIT COLORS",
            company_address=profile.address if profile else "",
            company_gstin=profile.gstin if profile else "",
            company_email=profile.email if profile else "",
            company_phone=profile.phone if profile else "",
            company_logo_data=company_logo_data
        )
        return invoice

    @staticmethod
    def get_invoice_by_mrs(mrs_id):
        return Invoice.select().where(Invoice.mrs == mrs_id).first()

    @staticmethod
    def get_all_invoices():
        return Invoice.select().order_by(Invoice.created_at.desc())

    @staticmethod
    def update_invoice_status(invoice_id, new_status):
        invoice = Invoice.get_by_id(invoice_id)
        invoice.status = new_status
        invoice.save()
        return invoice
