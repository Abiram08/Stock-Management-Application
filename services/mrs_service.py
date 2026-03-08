from database.models import MRS, MRSItem, Material, Transaction, db
from services.audit_service import AuditService
import datetime

class MRSService:
    @staticmethod
    def create_mrs(supervisor_id, batch_id, items):
        """
        items: list of dicts {'material_id': id, 'quantity_requested': qty}
        """
        if not items:
            raise ValueError("No items requested")

        with db.atomic():
            # Validate stock
            for item in items:
                material = Material.get_by_id(item['material_id'])
                if item['quantity_requested'] > material.quantity:
                    raise ValueError(f"Insufficient stock for {material.name}. Required: {item['quantity_requested']}, Available: {material.quantity}")

            # Create MRS
            mrs = MRS.create(
                batch_id=batch_id,
                supervisor=supervisor_id,
                status='PENDING'
            )

            # Create MRS Items
            for item in items:
                MRSItem.create(
                    mrs=mrs,
                    material=item['material_id'],
                    quantity_requested=item['quantity_requested']
                )
            
            AuditService.log('MRS_CREATED', details={'mrs_id': mrs.id, 'batch_id': batch_id, 'item_count': len(items)})
            return mrs

    @staticmethod
    def get_pending_mrs():
        return (MRS
                .select(MRS, MRSItem, Material)
                .join(MRSItem)
                .join(Material)
                .where(MRS.status << ['PENDING', 'PARTIALLY_ISSUED'])
                .order_by(MRS.created_at.asc()))

    @staticmethod
    def get_my_mrs(supervisor_id):
        return (MRS
                .select(MRS, MRSItem, Material)
                .join(MRSItem)
                .join(Material)
                .where(MRS.supervisor == supervisor_id)
                .order_by(MRS.created_at.desc()))

    @staticmethod
    def issue_mrs(mrs_id, performed_by_id, items_issue):
        """
        items_issue: list of dicts {'material_id': id, 'quantity_issued': qty}
        """
        with db.atomic():
            mrs = MRS.get_by_id(mrs_id)
            if mrs.status == 'ISSUED':
                raise ValueError("MRS already issued")

            # Validate all stock first
            for issue_item in items_issue:
                material = Material.get_by_id(issue_item['material_id'])
                if material.quantity < issue_item['quantity_issued']:
                    raise ValueError(f"Insufficient stock for {material.name}")

            # Process issues
            for issue_item in items_issue:
                # Update stock
                Material.update(quantity=Material.quantity - issue_item['quantity_issued']).where(Material.id == issue_item['material_id']).execute()

                # Create transaction
                Transaction.create(
                    type='ISSUE',
                    material=issue_item['material_id'],
                    quantity=-issue_item['quantity_issued'],
                    related_id=mrs.id,
                    performed_by=performed_by_id
                )

                # Update MRS Item
                mrs_item = MRSItem.get((MRSItem.mrs == mrs) & (MRSItem.material == issue_item['material_id']))
                mrs_item.quantity_issued += issue_item['quantity_issued']
                mrs_item.save()

            # Update MRS status
            all_items = list(MRSItem.select().where(MRSItem.mrs == mrs))
            all_issued = all(i.quantity_issued >= i.quantity_requested for i in all_items)
            mrs.status = 'ISSUED' if all_issued else 'PARTIALLY_ISSUED'
            mrs.save()
            
            AuditService.log('MRS_ISSUED', details={'mrs_id': mrs.id, 'status': mrs.status})
            return mrs
