from peewee import *
import datetime
import bcrypt
import json
from pathlib import Path

# Initialize a Database Proxy for dynamic configuration
db = DatabaseProxy()

class BaseModel(Model):
    class Meta:
        database = db

class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()  # Stores bcrypt-hashed password
    role = CharField()  # ADMIN, SUPERVISOR, STORE_MANAGER
    created_at = DateTimeField(default=datetime.datetime.now)

    def set_password(self, raw_password):
        """Hash and store a password."""
        self.password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, raw_password):
        """Verify a password against the stored hash."""
        try:
            return bcrypt.checkpw(raw_password.encode('utf-8'), self.password.encode('utf-8'))
        except (ValueError, AttributeError):
            # Fallback for legacy plain-text passwords
            return self.password == raw_password

class Supplier(BaseModel):
    name = CharField()
    contact_person = CharField()
    phone = CharField()
    material_categories = TextField()
    gst_no = CharField(null=True)
    rating = FloatField(default=0.0)
    rating_count = IntegerField(default=0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class Material(BaseModel):
    name = CharField()
    code = CharField(null=True)
    category = CharField(default='CHEMICAL')  # DYE, CHEMICAL, AUXILIARIES, OTHER
    unit = CharField()  # kg, ltr, pcs
    quantity = FloatField(default=0.0)
    min_stock = FloatField(default=10.0)
    unit_cost = FloatField(default=0.0)
    abc_category = CharField(default='None')  # A, B, C, None
    supplier = ForeignKeyField(Supplier, backref='materials', null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    updated_at = DateTimeField(default=datetime.datetime.now)

    # Chemical safety fields
    shelf_life_days = IntegerField(null=True)  # Shelf life in days
    manufacture_date = DateField(null=True)
    expiry_date = DateField(null=True)
    hazard_class = CharField(default='None')  # None, Flammable, Corrosive, Irritant, Toxic, Oxidizing
    storage_temp_min = FloatField(null=True)  # Min storage temp in °C
    storage_temp_max = FloatField(null=True)  # Max storage temp in °C

    @property
    def is_expired(self):
        if self.expiry_date:
            return datetime.date.today() > self.expiry_date
        return False

    @property
    def days_until_expiry(self):
        if self.expiry_date:
            delta = self.expiry_date - datetime.date.today()
            return delta.days
        return None

    @property
    def is_hazardous(self):
        return self.hazard_class and self.hazard_class != 'None'

class MRS(BaseModel):
    batch_id = CharField()
    supervisor = ForeignKeyField(User, backref='material_requests')
    status = CharField(default='PENDING')  # PENDING, ISSUED, REJECTED, PARTIALLY_ISSUED
    created_at = DateTimeField(default=datetime.datetime.now)

class MRSItem(BaseModel):
    mrs = ForeignKeyField(MRS, backref='items')
    material = ForeignKeyField(Material, backref='mrs_items')
    quantity_requested = FloatField()
    quantity_issued = FloatField(default=0.0)

class ProductInward(BaseModel):
    store_manager = ForeignKeyField(User, backref='indents_raised')
    supplier = ForeignKeyField(Supplier, backref='indents')
    admin = ForeignKeyField(User, backref='indents_approved', null=True)
    status = CharField(default='RAISED')  # RAISED, APPROVED, REJECTED, COMPLETED
    reason = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    approved_at = DateTimeField(null=True)
    approval_remarks = TextField(null=True)
    completed_at = DateTimeField(null=True)

class PIItem(BaseModel):
    pi = ForeignKeyField(ProductInward, backref='items')
    material = ForeignKeyField(Material, backref='pi_items')
    quantity = FloatField()
    unit_price = FloatField(default=0.0)

class Transaction(BaseModel):
    type = CharField()  # ISSUE, INWARD, ADJUSTMENT, RETURN
    material = ForeignKeyField(Material, backref='transactions')
    quantity = FloatField()
    related_id = IntegerField(null=True)
    performed_by = ForeignKeyField(User, backref='transactions')
    timestamp = DateTimeField(default=datetime.datetime.now)

class AuditLog(BaseModel):
    action = CharField()
    user = ForeignKeyField(User, backref='audit_logs', null=True)
    details = TextField(null=True)  # JSON string
    timestamp = DateTimeField(default=datetime.datetime.now)

class Invoice(BaseModel):
    invoice_no = CharField(unique=True)
    mrs = ForeignKeyField(MRS, backref='invoices')
    total_amount = FloatField(default=0.0)
    tax_amount = FloatField(default=0.0)
    grand_total = FloatField(default=0.0)
    client_name = CharField(null=True)
    client_address = TextField(null=True)
    client_gstin = CharField(null=True)
    gst_percentage = FloatField(default=18)
    status = CharField(default='SENT')  # SENT, PAID, OVERDUE
    created_at = DateTimeField(default=datetime.datetime.now)

    # Snapshots for immutability
    company_name = CharField(null=True)
    company_address = TextField(null=True)
    company_gstin = CharField(null=True)
    company_email = CharField(null=True)
    company_phone = CharField(null=True)
    company_logo_data = TextField(null=True)
    due_date = DateField(null=True)

class Consumer(BaseModel):
    company_name = CharField()
    contact_person = CharField()
    phone = CharField()
    gst_no = CharField(null=True)
    location = CharField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)

class CompanyProfile(BaseModel):
    name = CharField(default="TEXKNIT COLORS")
    address = TextField(default="123 Textile Park, Tirupur - 641601")
    gstin = CharField(default="33AAAAA0000A1Z5")
    email = CharField(default="accounts@texknit.com")
    phone = CharField(default="+91 98765 43210")
    logo_path = CharField(null=True)
    default_tax_rate = FloatField(default=18.0)
    daily_late_fee = FloatField(default=0.0)

class Setting(BaseModel):
    """Key-value store for system settings."""
    key = CharField(unique=True)
    value = TextField(default='')
    category = CharField(default='general')  # general, notifications, defaults

    @classmethod
    def get_value(cls, key, default=None):
        try:
            setting = cls.get(cls.key == key)
            return setting.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key, value, category='general'):
        setting, created = cls.get_or_create(key=key, defaults={'value': value, 'category': category})
        if not created:
            setting.value = value
            setting.save()
        return setting


def _migrate_passwords():
    """Hash any plain-text passwords in the database."""
    for user in User.select():
        # Check if password is already a bcrypt hash (starts with $2b$ or $2a$)
        if not user.password.startswith('$2b$') and not user.password.startswith('$2a$'):
            user.set_password(user.password)
            user.save()


def _add_column_if_missing(table_class, column_name, column_field):
    """Safely add a column to an existing table if it doesn't exist."""
    try:
        db.execute_sql(f'SELECT "{column_name}" FROM "{table_class._meta.table_name}" LIMIT 1')
    except Exception:
        from playhouse.migrate import SqliteMigrator, migrate as pw_migrate
        migrator = SqliteMigrator(db)
        pw_migrate(migrator.add_column(table_class._meta.table_name, column_name, column_field))


def initialize_db():
    config_file = Path(__file__).parent.parent / "config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    else:
        config = {"db_type": "sqlite", "db_name": "stock_management.db"}
        
    if config.get("db_type") == "postgresql":
        # Note: psycopg2 module must be installed to use PostgresqlDatabase
        database = PostgresqlDatabase(
            config.get("db_name"),
            user=config.get("db_user", "postgres"),
            password=config.get("db_password", "root"),
            host=config.get("db_host", "localhost"),
            port=config.get("db_port", 5432)
        )
    else:
        root_dir = Path(__file__).parent.parent
        db_path = root_dir / config.get("db_name", "stock_management.db")
        database = SqliteDatabase(str(db_path))
        
    db.initialize(database)
    db.connect()

    # Create core tables
    db.create_tables([
        User, Supplier, Material, MRS, MRSItem,
        ProductInward, PIItem, Transaction, AuditLog, Invoice, CompanyProfile, Consumer,
        Setting
    ])

    # Migrate: add new Material safety columns if missing
    _add_column_if_missing(Material, 'shelf_life_days', IntegerField(null=True))
    _add_column_if_missing(Material, 'manufacture_date', DateField(null=True))
    _add_column_if_missing(Material, 'expiry_date', DateField(null=True))
    _add_column_if_missing(Material, 'hazard_class', CharField(default='None'))
    _add_column_if_missing(Material, 'storage_temp_min', FloatField(null=True))
    _add_column_if_missing(Material, 'storage_temp_max', FloatField(null=True))

    # Create default admin if not exists
    if User.select().where(User.username == 'admin').count() == 0:
        admin = User(username='admin', role='ADMIN')
        admin.set_password('admin123')
        admin.save()

    # Migrate existing plain-text passwords
    _migrate_passwords()

    # Ensure at least one company profile exists
    if CompanyProfile.select().count() == 0:
        CompanyProfile.create()

    # Seed default settings
    Setting.set_value('expiry_warning_days', '30', 'notifications')
    Setting.set_value('low_stock_multiplier', '1.0', 'defaults')

    # Seed supplier and product data (FY 2026)
    if Supplier.select().count() == 0:
        _seed_suppliers_and_products()

    db.close()


def _seed_suppliers_and_products():
    """Seed built-in supplier and product catalog data."""
    seed_data = [
        {
            "company_name": "ZSCHIMMER AND SCHWARZ INDIA PVT LTD",
            "contact_person": "Sales Dept",
            "phone": "9000000001",
            "gst_no": None,
            "material_categories": "Auxiliaries, Chemicals",
            "products": [
                {"name": "Cefatex ENN", "category": "Auxiliaries", "unit": "kg", "cost": 320.0, "stock": 50},
                {"name": "Lubatex ECS Conc", "category": "Auxiliaries", "unit": "kg", "cost": 280.0, "stock": 30},
                {"name": "Lubatex LV-91", "category": "Auxiliaries", "unit": "kg", "cost": 310.0, "stock": 25},
                {"name": "Optavon MEX-91", "category": "Auxiliaries", "unit": "kg", "cost": 450.0, "stock": 40},
                {"name": "Optavon SV", "category": "Auxiliaries", "unit": "kg", "cost": 390.0, "stock": 15},
                {"name": "Setavin PQD", "category": "Other Chemicals", "unit": "kg", "cost": 210.0, "stock": 60},
                {"name": "Setavin RCO", "category": "Other Chemicals", "unit": "ltr", "cost": 185.0, "stock": 45},
                {"name": "Setavin RCO Liq", "category": "Other Chemicals", "unit": "ltr", "cost": 195.0, "stock": 35},
                {"name": "Tissocyl COD", "category": "Auxiliaries", "unit": "kg", "cost": 520.0, "stock": 20},
                {"name": "Tissocyl RC 9", "category": "Auxiliaries", "unit": "kg", "cost": 480.0, "stock": 18},
                {"name": "Tissocyl WLF", "category": "Auxiliaries", "unit": "kg", "cost": 540.0, "stock": 12},
                {"name": "Zetesal 2000", "category": "Other Chemicals", "unit": "kg", "cost": 260.0, "stock": 55},
                {"name": "Zetesal CPW", "category": "Other Chemicals", "unit": "kg", "cost": 230.0, "stock": 70},
                {"name": "Zetesal FIX", "category": "Other Chemicals", "unit": "kg", "cost": 245.0, "stock": 0},
                {"name": "Zetesal NPC", "category": "Other Chemicals", "unit": "kg", "cost": 275.0, "stock": 8},
                {"name": "Zetesan LTS", "category": "Other Chemicals", "unit": "kg", "cost": 290.0, "stock": 42},
                {"name": "ZS Dyeset RFT", "category": "Reactive Dye (Cotton)", "unit": "kg", "cost": 680.0, "stock": 10},
            ]
        },
        {
            "company_name": "CHROMOLIN CAPITAL PVT LTD",
            "contact_person": "Sales Dept",
            "phone": "9000000002",
            "gst_no": None,
            "material_categories": "Chemicals",
            "products": [
                {"name": "HEMITTOL SRW", "category": "Other Chemicals", "unit": "kg", "cost": 350.0, "stock": 28},
                {"name": "FABIN EG", "category": "Other Chemicals", "unit": "ltr", "cost": 420.0, "stock": 15},
                {"name": "CATAMINE OC", "category": "Other Chemicals", "unit": "kg", "cost": 380.0, "stock": 5},
                {"name": "CATAMINE HCS", "category": "Other Chemicals", "unit": "kg", "cost": 395.0, "stock": 22},
            ]
        },
        {
            "company_name": "Advanced Enzytech Pvt Ltd",
            "contact_person": "Sales Dept",
            "phone": "9000000003",
            "gst_no": None,
            "material_categories": "Chemicals, Auxiliaries",
            "products": [
                {"name": "Addox 12L", "category": "Other Chemicals", "unit": "ltr", "cost": 290.0, "stock": 35},
                {"name": "Addox 25L", "category": "Other Chemicals", "unit": "ltr", "cost": 310.0, "stock": 0},
                {"name": "Sebsoft HCL", "category": "Auxiliaries", "unit": "kg", "cost": 450.0, "stock": 20},
                {"name": "Seebrite 4ML", "category": "Auxiliaries", "unit": "ltr", "cost": 520.0, "stock": 18},
            ]
        }
    ]

    for company in seed_data:
        supplier = Supplier.create(
            name=company["company_name"],
            contact_person=company["contact_person"],
            phone=company["phone"],
            gst_no=company["gst_no"],
            material_categories=company["material_categories"],
            rating=5.0
        )

        for product in company["products"]:
            Material.create(
                name=product["name"],
                category=product["category"],
                unit=product["unit"],
                quantity=product["stock"],
                min_stock=10.0,
                unit_cost=product["cost"],
                supplier=supplier
            )


if __name__ == '__main__':
    initialize_db()
