"""
Unit tests for services/mrs_service.py — MRS creation and issuance.
"""
import pytest
from services.mrs_service import MRSService
from database.models import Material, MRS, MRSItem, Transaction


class TestCreateMRS:
    def test_create_mrs(self, supervisor_user, sample_material):
        items = [{'material_id': sample_material.id, 'quantity_requested': 10}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'BATCH-001', items)
        assert mrs.batch_id == 'BATCH-001'
        assert mrs.status == 'PENDING'
        assert MRSItem.select().where(MRSItem.mrs == mrs).count() == 1

    def test_create_mrs_empty_items(self, supervisor_user):
        with pytest.raises(ValueError, match="No items"):
            MRSService.create_mrs(supervisor_user.id, 'BATCH-002', [])

    def test_create_mrs_insufficient_stock(self, supervisor_user, sample_material):
        items = [{'material_id': sample_material.id, 'quantity_requested': 9999}]
        with pytest.raises(ValueError, match="Insufficient stock"):
            MRSService.create_mrs(supervisor_user.id, 'BATCH-003', items)


class TestIssueMRS:
    def test_issue_mrs_updates_stock(self, supervisor_user, admin_user, sample_material):
        items = [{'material_id': sample_material.id, 'quantity_requested': 20}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'BATCH-004', items)

        issue_items = [{'material_id': sample_material.id, 'quantity_issued': 20}]
        result = MRSService.issue_mrs(mrs.id, admin_user.id, issue_items)

        # Stock should decrease
        updated_material = Material.get_by_id(sample_material.id)
        assert updated_material.quantity == 80.0  # 100 - 20

        # Status should be ISSUED
        assert result.status == 'ISSUED'

        # Transaction should be created
        txns = Transaction.select().where(Transaction.material == sample_material.id)
        assert txns.count() == 1

    def test_issue_mrs_partial(self, supervisor_user, admin_user, sample_material):
        items = [{'material_id': sample_material.id, 'quantity_requested': 30}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'BATCH-005', items)

        # Issue only part
        issue_items = [{'material_id': sample_material.id, 'quantity_issued': 15}]
        result = MRSService.issue_mrs(mrs.id, admin_user.id, issue_items)
        assert result.status == 'PARTIALLY_ISSUED'

    def test_issue_already_issued_raises(self, supervisor_user, admin_user, sample_material):
        items = [{'material_id': sample_material.id, 'quantity_requested': 5}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'BATCH-006', items)

        issue_items = [{'material_id': sample_material.id, 'quantity_issued': 5}]
        MRSService.issue_mrs(mrs.id, admin_user.id, issue_items)

        # Try to issue again
        with pytest.raises(ValueError, match="already issued"):
            MRSService.issue_mrs(mrs.id, admin_user.id, issue_items)

    def test_issue_insufficient_stock_raises(self, supervisor_user, admin_user, sample_material):
        items = [{'material_id': sample_material.id, 'quantity_requested': 50}]
        mrs = MRSService.create_mrs(supervisor_user.id, 'BATCH-007', items)

        # Try to issue more than available
        issue_items = [{'material_id': sample_material.id, 'quantity_issued': 150}]
        with pytest.raises(ValueError, match="Insufficient stock"):
            MRSService.issue_mrs(mrs.id, admin_user.id, issue_items)
