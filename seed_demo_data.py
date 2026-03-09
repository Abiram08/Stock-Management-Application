import os
import datetime
import random
from pathlib import Path
from database.models import (
    db, initialize_db, User, Supplier, Material, MRS, MRSItem, 
    ProductInward, PIItem, Transaction, AuditLog, Invoice, Consumer, 
    CompanyProfile, Setting
)

def seed_data():
    # 1. Initialize DB
    initialize_db()

    # Update Materials with Safety Data (Hazard Classes & Expiry)
    print("Injecting safety data into materials...")
    hazards = ['Flammable', 'Corrosive', 'Irritant', 'Toxic', 'Oxidizing', 'None']
    for mat in Material.select():
        mat.hazard_class = random.choice(hazards)
        # Set random expiry dates: some past, some soon, some far
        days_offset = random.randint(-60, 365)
        mat.expiry_date = (datetime.date.today() + datetime.timedelta(days=days_offset))
        mat.manufacture_date = mat.expiry_date - datetime.timedelta(days=730)
        mat.save()

    # 2. Add Users
    admin = User.get_or_none(User.username == 'Texknit')
    if not admin:
        # Check if old admin exists and rename/update or just create new
        old_admin = User.get_or_none(User.username == 'admin')
        if old_admin:
            admin = old_admin
            admin.username = 'Texknit'
        else:
            admin = User.create(username='Texknit', role='ADMIN', password='')
        
        admin.role = 'ADMIN'
        admin.set_password('texknit2026')
        admin.save()
    else:
        admin.role = 'ADMIN'
        admin.set_password('texknit2026')
        admin.save()
        
    supervisor = User.get_or_none(User.username == 'supervisor')
    if not supervisor:
        supervisor = User.create(username='supervisor', role='SUPERVISOR', password='')
        supervisor.set_password('super123')
        supervisor.save()
    else:
        supervisor.role = 'SUPERVISOR'
        supervisor.save()

    # 3. Add 5 Consumers
    consumers_data = [
        {"company_name": "Global Textiles Ltd", "contact_person": "John Doe", "phone": "+91 98400 12345", "gst_no": "33AACCG1234F1Z1", "location": "Tirupur, Tamil Nadu"},
        {"company_name": "Apex Fashion Wear", "contact_person": "Sarah Smith", "phone": "+91 98400 54321", "gst_no": "33BBCCG5432F1Z2", "location": "Coimbatore, Tamil Nadu"},
        {"company_name": "Green Dye Works", "contact_person": "Rajesh Kumar", "phone": "+91 98400 67890", "gst_no": "33CCDDG6789F1Z3", "location": "Erode, Tamil Nadu"},
        {"company_name": "Royal Knits & Co", "contact_person": "Anita Rani", "phone": "+91 98400 11223", "gst_no": "33DDEEG1122F1Z4", "location": "Salem, Tamil Nadu"},
        {"company_name": "Modern Fabrics Inc", "contact_person": "Michael Chen", "phone": "+91 98400 33445", "gst_no": "33EEFFG3344F1Z5", "location": "Chennai, Tamil Nadu"}
    ]
    for data in consumers_data:
        Consumer.get_or_create(company_name=data["company_name"], defaults=data)

    # 4. Clear existing demo invoices/MRS to allow fresh seeding
    print("Clearing old demo data...")
    Invoice.delete().execute()
    MRSItem.delete().execute()
    MRS.delete().execute()
    Transaction.delete().where(Transaction.type == 'ISSUE').execute()

    # 5. Seed Timeline Data
    materials = list(Material.select())
    consumers = list(Consumer.select())
    now = datetime.datetime.now()
    
    print("Seeding new timeline data...")
    for month_offset in range(7, -1, -1):
        num_entries = random.randint(2, 4)
        for i in range(num_entries):
            past_date = now - datetime.timedelta(days=month_offset * 30 + random.randint(0, 20))
            consumer = random.choice(consumers)
            
            mrs = MRS.create(
                batch_id=f"B-{past_date.strftime('%y%m')}-{i+1}",
                supervisor=supervisor,
                status='ISSUED',
                created_at=past_date
            )
            
            mrs_mats = random.sample(materials, k=random.randint(1, 3))
            total_base = 0.0
            for mat in mrs_mats:
                qty = random.uniform(5.0, 30.0)
                MRSItem.create(mrs=mrs, material=mat, quantity_requested=qty, quantity_issued=qty)
                total_base += qty * mat.unit_cost
                Transaction.create(type='ISSUE', material=mat, quantity=qty, related_id=mrs.id, performed_by=supervisor, timestamp=past_date)
            
            tax = total_base * 0.18
            invoice_no = f"INV-{past_date.year}-{ (month_offset * 10 + i + 1):04d}"
            
            # Status Logic:
            # - Current month (0): SENT
            # - 1 month ago: Some PAID, some SENT (will be OVERDUE)
            # - > 1 month ago: Mostly PAID
            status = 'PAID'
            if month_offset == 0:
                status = 'SENT'
            elif month_offset == 1 and random.random() > 0.4:
                status = 'SENT' # Will be overdue 
            
            Invoice.create(
                invoice_no=invoice_no,
                mrs=mrs,
                total_amount=total_base,
                tax_amount=tax,
                grand_total=total_base + tax,
                client_name=consumer.company_name,
                client_address=consumer.location,
                client_gstin=consumer.gst_no,
                gst_percentage=18,
                status=status,
                created_at=past_date,
                due_date=(past_date + datetime.timedelta(days=14)).date(),
                company_name="TEXKNIT COLORS",
                company_address="123 Textile Park, Tirupur - 641601",
                company_gstin="33AAAAA0000A1Z5",
                company_email="accounts@texknit.com",
                company_phone="+91 98765 43210"
            )

    # 6. Seed Procurement Data (Purchase Indents)
    print("Seeding procurement data...")
    suppliers = list(Supplier.select())
    reasons = [
        "Monthly replenishment of bleaching agents.",
        "Emergency restock: Dye levels low for Spring batch.",
        "Quarterly safety chemical restock.",
        "Replenishing raw materials for new client order.",
        "Auxiliaries stock-up for holiday production run."
    ]
    
    for i in range(10):
        past_date = now - datetime.timedelta(days=random.randint(1, 45))
        supplier = random.choice(suppliers)
        reason = random.choice(reasons)
        
        # Status distribution: 2 Raised, 2 Approved, 1 Rejected, 5 Completed
        if i < 2: status = 'RAISED'
        elif i < 4: status = 'APPROVED'
        elif i == 4: status = 'REJECTED'
        else: status = 'COMPLETED'
        
        pi = ProductInward.create(
            store_manager=admin,
            supplier=supplier,
            status=status,
            reason=reason,
            created_at=past_date,
            approved_at=past_date + datetime.timedelta(hours=5) if status != 'RAISED' else None,
            completed_at=past_date + datetime.timedelta(days=2) if status == 'COMPLETED' else None,
            approval_remarks="Auto-approved for demo." if status != 'RAISED' else ""
        )
        
        pi_mats = random.sample(materials, k=random.randint(1, 3))
        for mat in pi_mats:
            qty = random.uniform(20.0, 150.0)
            PIItem.create(pi=pi, material=mat, quantity=qty, unit_price=mat.unit_cost)
            
            if status == 'COMPLETED':
                Transaction.create(
                    type='INWARD',
                    material=mat,
                    quantity=qty,
                    related_id=pi.id,
                    performed_by=admin,
                    timestamp=pi.completed_at
                )

    print("Success: Professional Procurement Timeline Seeded.")

if __name__ == "__main__":
    seed_data()
