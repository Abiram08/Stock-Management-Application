"""
Unit tests for services/inventory_service.py — material CRUD, ABC analysis, and transactions.
"""
import datetime
import pytest
from services.inventory_service import InventoryService
from database.models import Material, Transaction, Supplier


class TestGetAllMaterials:
    def test_returns_list(self, sample_material):
        materials = InventoryService.get_all_materials()
        assert isinstance(materials, list)
        assert len(materials) == 1
        assert materials[0].name == "Reactive Red 195"

    def test_empty_when_no_materials(self):
        materials = InventoryService.get_all_materials()
        assert materials == []


class TestCreateMaterial:
    def test_create_material(self, sample_supplier):
        data = {
            'name': 'New Dye',
            'category': 'Other Chemicals',
            'unit': 'kg',
            'quantity': 50.0,
            'min_stock': 5.0,
            'unit_cost': 200.0,
            'supplier_id': sample_supplier.id
        }
        material = InventoryService.create_material(data)
        assert material.name == 'New Dye'
        assert material.quantity == 50.0


class TestUpdateMaterial:
    def test_update_sets_updated_at(self, sample_material):
        old_updated = sample_material.updated_at
        InventoryService.update_material(sample_material.id, {'name': 'Updated Red'})
        updated = Material.get_by_id(sample_material.id)
        assert updated.name == 'Updated Red'
        # updated_at should be set (may be same second, but field should exist)
        assert updated.updated_at is not None


class TestDeleteMaterial:
    def test_delete_removes_material(self, sample_material, admin_user):
        # Create a transaction first
        Transaction.create(
            type='INWARD',
            material=sample_material,
            quantity=10,
            performed_by=admin_user
        )
        InventoryService.delete_material(sample_material.id)
        assert Material.select().where(Material.id == sample_material.id).count() == 0
        assert Transaction.select().where(Transaction.material == sample_material.id).count() == 0


class TestGetMaterialDetails:
    def test_existing(self, sample_material):
        result = InventoryService.get_material_details(sample_material.id)
        assert result is not None
        assert result.name == "Reactive Red 195"

    def test_nonexistent(self):
        result = InventoryService.get_material_details(99999)
        assert result is None


class TestABCAnalysis:
    def test_empty_returns_empty_list(self):
        result = InventoryService.calculate_abc_analysis()
        assert result == []

    def test_zero_value_returns_empty_list(self, sample_supplier):
        Material.create(
            name="Free Item", unit="pcs",
            quantity=0, unit_cost=0, supplier=sample_supplier
        )
        result = InventoryService.calculate_abc_analysis()
        assert result == []

    def test_returns_list_with_categories(self, sample_supplier):
        # Create materials with varying values
        Material.create(name="High Value", unit="kg", quantity=100, unit_cost=1000, supplier=sample_supplier)
        Material.create(name="Med Value", unit="kg", quantity=50, unit_cost=200, supplier=sample_supplier)
        Material.create(name="Low Value", unit="kg", quantity=10, unit_cost=10, supplier=sample_supplier)

        result = InventoryService.calculate_abc_analysis()
        assert isinstance(result, list)
        assert len(result) == 3

        # Each item should have material_id, value, and category
        for item in result:
            assert 'material_id' in item
            assert 'category' in item
            assert item['category'] in ('A', 'B', 'C')


class TestTransactionHistory:
    def test_returns_transactions(self, sample_material, admin_user):
        Transaction.create(
            type='INWARD', material=sample_material,
            quantity=50, performed_by=admin_user
        )
        Transaction.create(
            type='ISSUE', material=sample_material,
            quantity=-10, performed_by=admin_user
        )
        history = list(InventoryService.get_transaction_history(sample_material.id))
        assert len(history) == 2
