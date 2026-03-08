"""
Unit tests for services/invoice_service.py — invoice creation, numbering, and status updates.
"""
import pytest
from services.invoice_service import InvoiceService
from services.mrs_service import MRSService
from database.models import Invoice


class TestInvoiceNumbering:
    def test_first_invoice_is_0001(self, supervisor_user, sample_material, company_profile):
        items = [{'material_id': sample_material.id, 'quantity_requested': 5}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-1', items)
        invoice = InvoiceService.create_invoice_from_mrs(mrs.id)
        assert invoice.invoice_no.endswith('-0001')

    def test_sequential_numbering(self, supervisor_user, sample_material, company_profile):
        # Create first invoice
        items1 = [{'material_id': sample_material.id, 'quantity_requested': 5}]
        mrs1 = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-2', items1)
        inv1 = InvoiceService.create_invoice_from_mrs(mrs1.id)

        # Create second invoice
        items2 = [{'material_id': sample_material.id, 'quantity_requested': 3}]
        mrs2 = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-3', items2)
        inv2 = InvoiceService.create_invoice_from_mrs(mrs2.id)

        assert inv1.invoice_no.endswith('-0001')
        assert inv2.invoice_no.endswith('-0002')


class TestInvoiceCreation:
    def test_totals_calculated_correctly(self, supervisor_user, sample_material, company_profile):
        items = [{'material_id': sample_material.id, 'quantity_requested': 10}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-4', items)

        invoice = InvoiceService.create_invoice_from_mrs(mrs.id, client_name="Test Client")

        # unit_cost=680, qty=10, total=6800
        assert invoice.total_amount == 6800.0
        # Tax at 18% = 1224
        assert invoice.tax_amount == pytest.approx(1224.0, abs=0.01)
        # Grand total = 6800 + 1224 = 8024
        assert invoice.grand_total == pytest.approx(8024.0, abs=0.01)

    def test_status_is_draft(self, supervisor_user, sample_material, company_profile):
        items = [{'material_id': sample_material.id, 'quantity_requested': 5}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-5', items)
        invoice = InvoiceService.create_invoice_from_mrs(mrs.id)
        assert invoice.status == 'DRAFT'

    def test_client_details_stored(self, supervisor_user, sample_material, company_profile):
        items = [{'material_id': sample_material.id, 'quantity_requested': 5}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-6', items)
        invoice = InvoiceService.create_invoice_from_mrs(
            mrs.id,
            client_name="Acme Corp",
            client_address="123 Test St",
            client_gstin="33BBBBB0000B1Z5"
        )
        assert invoice.client_name == "Acme Corp"
        assert invoice.client_address == "123 Test St"
        assert invoice.client_gstin == "33BBBBB0000B1Z5"

    def test_company_snapshot(self, supervisor_user, sample_material, company_profile):
        items = [{'material_id': sample_material.id, 'quantity_requested': 5}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-7', items)
        invoice = InvoiceService.create_invoice_from_mrs(mrs.id)

        assert invoice.company_name == "TEXKNIT COLORS"
        assert invoice.company_gstin == "33AAAAA0000A1Z5"


class TestInvoiceStatusUpdate:
    def test_mark_as_paid(self, supervisor_user, sample_material, company_profile):
        items = [{'material_id': sample_material.id, 'quantity_requested': 5}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-8', items)
        invoice = InvoiceService.create_invoice_from_mrs(mrs.id)

        updated = InvoiceService.update_invoice_status(invoice.id, 'PAID')
        assert updated.status == 'PAID'


class TestGetInvoices:
    def test_get_all_invoices(self, supervisor_user, sample_material, company_profile):
        items = [{'material_id': sample_material.id, 'quantity_requested': 5}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-9', items)
        InvoiceService.create_invoice_from_mrs(mrs.id)

        invoices = list(InvoiceService.get_all_invoices())
        assert len(invoices) == 1

    def test_get_by_mrs(self, supervisor_user, sample_material, company_profile):
        items = [{'material_id': sample_material.id, 'quantity_requested': 5}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'INV-BATCH-10', items)
        InvoiceService.create_invoice_from_mrs(mrs.id)

        result = InvoiceService.get_invoice_by_mrs(mrs.id)
        assert result is not None
        assert result.mrs.id == mrs.id
