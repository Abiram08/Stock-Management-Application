from database.models import ProductInward, PIItem, Material, Transaction, db, Supplier
from services.audit_service import AuditService
import datetime

class ProcurementService:
    @staticmethod
    def create_pi(store_manager_id, items, reason, supplier_id):
        """
        items: list of dicts {'material_id': id, 'quantity': qty}
        """
        with db.atomic():
            pi = ProductInward.create(
                store_manager=store_manager_id,
                supplier=supplier_id,
                reason=reason,
                status='RAISED'
            )
            for item in items:
                PIItem.create(
                    pi=pi,
                    material=item['material_id'],
                    quantity=item['quantity']
                )
            AuditService.log('PI_CREATED', details={'pi_id': pi.id, 'supplier_id': supplier_id, 'item_count': len(items)})
            return pi

    @staticmethod
    def get_all_pis():
        return (ProductInward
                .select(ProductInward, Supplier)
                .join(Supplier)
                .order_by(ProductInward.created_at.desc()))

    @staticmethod
    def update_pi_status(pi_id, admin_id, status, remarks):
        pi = ProductInward.get_by_id(pi_id)
        pi.admin = admin_id
        pi.status = status
        pi.approval_remarks = remarks or "No remarks"
        if status in ['APPROVED', 'REJECTED']:
            pi.approved_at = datetime.datetime.now()
        pi.save()
        AuditService.log('PI_STATUS_UPDATED', details={'pi_id': pi.id, 'status': status, 'admin_id': admin_id})
        return pi

    @staticmethod
    def process_inward(pi_id, performed_by_id):
        with db.atomic():
            pi = ProductInward.get_by_id(pi_id)
            if pi.status != 'APPROVED':
                raise ValueError("Only approved PIs can be processed for inward")

            # Update stock and create transactions
            for item in pi.items:
                Material.update(quantity=Material.quantity + item.quantity, 
                              updated_at=datetime.datetime.now()).where(Material.id == item.material.id).execute()
                
                Transaction.create(
                    type='INWARD',
                    material=item.material.id,
                    quantity=item.quantity,
                    related_id=pi.id,
                    performed_by=performed_by_id
                )

            # Mark PI as completed
            pi.status = 'COMPLETED'
            pi.completed_at = datetime.datetime.now()
            pi.save()
            AuditService.log('PI_INWARD_PROCESSED', details={'pi_id': pi.id})
            return pi

    @staticmethod
    def reverse_inward(pi_id, performed_by_id):
        """
        Reverses a completed inward entry: 
        1. Deducts stock
        2. Status goes back to APPROVED
        3. Deletes the INWARD transactions associated with this PI
        """
        with db.atomic():
            pi = ProductInward.get_by_id(pi_id)
            if pi.status != 'COMPLETED':
                raise ValueError("Only completed PIs can be reversed")

            # 1. Revert stock
            for item in pi.items:
                Material.update(quantity=Material.quantity - item.quantity,
                              updated_at=datetime.datetime.now()).where(Material.id == item.material.id).execute()
            
            # 2. Status back to APPROVED
            pi.status = 'APPROVED'
            pi.completed_at = None
            pi.save()

            # 3. Delete INWARD transactions for this PI
            Transaction.delete().where(Transaction.type == 'INWARD', Transaction.related_id == pi.id).execute()

            AuditService.log('PI_INWARD_REVERSED', details={'pi_id': pi.id, 'reversed_by': performed_by_id})
            return pi

    @staticmethod
    def get_recommendations():
        low_stock = Material.select().where(Material.quantity <= Material.min_stock)
        recommendations = []
        for m in low_stock:
            recommendations.append({
                'material_id': m.id,
                'name': m.name,
                'quantity': m.min_stock * 2,
                'current_stock': m.quantity,
                'unit': m.unit
            })
        return recommendations
