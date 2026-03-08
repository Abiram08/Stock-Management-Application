"""
Shared pytest fixtures for all test modules.
Uses an in-memory SQLite database for complete test isolation.
"""
import sys
import os
import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from peewee import SqliteDatabase
from database.models import (
    db, User, Supplier, Material, MRS, MRSItem,
    ProductInward, PIItem, Transaction, AuditLog,
    Invoice, CompanyProfile, Consumer, Setting, BaseModel
)

# In-memory test database
test_db = SqliteDatabase(':memory:')

ALL_MODELS = [
    User, Supplier, Material, MRS, MRSItem,
    ProductInward, PIItem, Transaction, AuditLog,
    Invoice, CompanyProfile, Consumer, Setting
]


@pytest.fixture(autouse=True)
def setup_test_db():
    """
    Bind all models to an in-memory SQLite DB before each test,
    create tables, and tear them down after.
    """
    # Bind models to the test database
    test_db.bind(ALL_MODELS, bind_refs=False, bind_backrefs=False)
    test_db.connect()
    test_db.create_tables(ALL_MODELS)

    yield test_db

    test_db.drop_tables(ALL_MODELS)
    test_db.close()


@pytest.fixture
def admin_user():
    """Create a default admin user."""
    user = User(username='admin', role='ADMIN')
    user.set_password('admin123')
    user.save()
    return user


@pytest.fixture
def supervisor_user():
    """Create a supervisor user."""
    user = User(username='supervisor', role='SUPERVISOR')
    user.set_password('super123')
    user.save()
    return user


@pytest.fixture
def store_manager_user():
    """Create a store manager user."""
    user = User(username='storekeeper', role='STORE_MANAGER')
    user.set_password('store123')
    user.save()
    return user


@pytest.fixture
def sample_supplier():
    """Create a sample supplier."""
    return Supplier.create(
        name="Test Chemicals Ltd",
        contact_person="John Doe",
        phone="9876543210",
        gst_no="33AAAAA0000A1Z5",
        material_categories="Chemicals, Dyes",
        rating=5.0
    )


@pytest.fixture
def sample_material(sample_supplier):
    """Create a sample material linked to a supplier."""
    return Material.create(
        name="Reactive Red 195",
        code="RR-195",
        category="Reactive Dye (Cotton)",
        unit="kg",
        quantity=100.0,
        min_stock=10.0,
        unit_cost=680.0,
        supplier=sample_supplier
    )


@pytest.fixture
def company_profile():
    """Create a default company profile."""
    return CompanyProfile.create(
        name="TEXKNIT COLORS",
        address="123 Textile Park, Tirupur",
        gstin="33AAAAA0000A1Z5",
        email="accounts@texknit.com",
        phone="+91 98765 43210",
        default_tax_rate=18.0,
        daily_late_fee=100.0
    )
