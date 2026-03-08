"""
Unit tests for services/procurement_service.py — PI lifecycle: create, approve, inward.
"""
import pytest
from services.procurement_service import ProcurementService
from database.models import Material, ProductInward, Supplier


class TestCreatePI:
    def test_create_pi(self, store_manager_user, sample_material, sample_supplier):
        items = [{'material_id': sample_material.id, 'quantity': 50}]
        pi = ProcurementService.create_pi(store_manager_user.id, items, "Monthly restock", sample_supplier.id)
        assert pi.status == 'RAISED'
        assert pi.reason == "Monthly restock"

    def test_pi_items_stored(self, store_manager_user, sample_material, sample_supplier):
        items = [{'material_id': sample_material.id, 'quantity': 25}]
        pi = ProcurementService.create_pi(store_manager_user.id, items, "Test", sample_supplier.id)
        assert len(list(pi.items)) == 1
        assert list(pi.items)[0].quantity == 25


class TestApprovePi:
    def test_approve_pi(self, store_manager_user, admin_user, sample_material, sample_supplier):
        items = [{'material_id': sample_material.id, 'quantity': 30}]
        pi = ProcurementService.create_pi(store_manager_user.id, items, "Restock", sample_supplier.id)

        updated = ProcurementService.update_pi_status(pi.id, admin_user.id, 'APPROVED', 'Looks good')
        assert updated.status == 'APPROVED'
        assert updated.approval_remarks == 'Looks good'
        assert updated.admin.id == admin_user.id

    def test_reject_pi(self, store_manager_user, admin_user, sample_material, sample_supplier):
        items = [{'material_id': sample_material.id, 'quantity': 30}]
        pi = ProcurementService.create_pi(store_manager_user.id, items, "Restock", sample_supplier.id)

        updated = ProcurementService.update_pi_status(pi.id, admin_user.id, 'REJECTED', 'Not needed')
        assert updated.status == 'REJECTED'


class TestProcessInward:
    def test_inward_updates_stock(self, store_manager_user, admin_user, sample_material, sample_supplier):
        initial_qty = sample_material.quantity  # 100

        items = [{'material_id': sample_material.id, 'quantity': 50}]
        pi = ProcurementService.create_pi(store_manager_user.id, items, "Restock", sample_supplier.id)
        ProcurementService.update_pi_status(pi.id, admin_user.id, 'APPROVED', 'OK')

        ProcurementService.process_inward(pi.id, store_manager_user.id, 4)

        # Stock should increase
        updated = Material.get_by_id(sample_material.id)
        assert updated.quantity == initial_qty + 50  # 100 + 50 = 150

    def test_inward_updates_supplier_rating(self, store_manager_user, admin_user, sample_material, sample_supplier):
        items = [{'material_id': sample_material.id, 'quantity': 20}]
        pi = ProcurementService.create_pi(store_manager_user.id, items, "Rate test", sample_supplier.id)
        ProcurementService.update_pi_status(pi.id, admin_user.id, 'APPROVED', 'OK')

        ProcurementService.process_inward(pi.id, store_manager_user.id, 3)

        supplier = Supplier.get_by_id(sample_supplier.id)
        # Supplier starts with rating_count=0, so new rating = (0*5 + 3) / 1 = 3.0
        assert supplier.rating == pytest.approx(3.0, abs=0.01)
        assert supplier.rating_count == 1

    def test_inward_on_non_approved_raises(self, store_manager_user, sample_material, sample_supplier):
        items = [{'material_id': sample_material.id, 'quantity': 20}]
        pi = ProcurementService.create_pi(store_manager_user.id, items, "Test", sample_supplier.id)

        with pytest.raises(ValueError, match="approved"):
            ProcurementService.process_inward(pi.id, store_manager_user.id, 5)

    def test_pi_status_completed(self, store_manager_user, admin_user, sample_material, sample_supplier):
        items = [{'material_id': sample_material.id, 'quantity': 10}]
        pi = ProcurementService.create_pi(store_manager_user.id, items, "Complete test", sample_supplier.id)
        ProcurementService.update_pi_status(pi.id, admin_user.id, 'APPROVED', 'OK')

        ProcurementService.process_inward(pi.id, store_manager_user.id, 5)

        updated_pi = ProductInward.get_by_id(pi.id)
        assert updated_pi.status == 'COMPLETED'


class TestGetRecommendations:
    def test_recommends_low_stock(self, sample_supplier):
        Material.create(
            name="Low Stock Item", unit="kg",
            quantity=5.0, min_stock=10.0,
            unit_cost=100, supplier=sample_supplier
        )
        recs = ProcurementService.get_recommendations()
        assert len(recs) == 1
        assert recs[0]['name'] == "Low Stock Item"
        assert recs[0]['quantity'] == 20.0  # min_stock * 2

    def test_no_recommendations_when_healthy(self, sample_material):
        # sample_material has qty=100, min_stock=10 → healthy
        recs = ProcurementService.get_recommendations()
        assert len(recs) == 0
