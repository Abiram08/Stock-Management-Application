from peewee import JOIN
from database.models import Material, Transaction, ProductInward, Supplier, db
from services.audit_service import AuditService
import datetime

class InventoryService:
    @staticmethod
    def get_all_materials():
        return list(Material.select(Material, Supplier).join(Supplier, join_type=JOIN.LEFT_OUTER).order_by(Material.name))

    @staticmethod
    def get_procurement_context(material_id):
        try:
            material = Material.get_by_id(material_id)
            
            last_inward = (Transaction
                          .select()
                          .where((Transaction.material == material) & (Transaction.type == 'INWARD'))
                          .order_by(Transaction.timestamp.desc())
                          .first())
            
            context = {
                'material': {
                    'name': material.name,
                    'code': material.code,
                    'category': material.category,
                    'quantity': material.quantity,
                    'min_stock': material.min_stock,
                    'unit': material.unit
                },
                'status': 'NEVER_ORDERED',
                'last_inward': None,
                'context_note': ''
            }

            if material.quantity == 0:
                context['context_note'] = 'Stock is critically low (0). Immediate action required.'
            elif material.quantity <= material.min_stock:
                context['context_note'] = 'Stock is approaching minimum level. Review procurement.'
            elif material.quantity > material.min_stock * 5:
                context['context_note'] = 'Material not used recently. Verify future requirement.'

            if last_inward and last_inward.related_id:
                context['status'] = 'ORDERED_BEFORE'
                pi = ProductInward.get_or_none(ProductInward.id == last_inward.related_id)
                if pi:
                    context['last_inward'] = {
                        'date': last_inward.timestamp.isoformat(),
                        'quantity': last_inward.quantity,
                        'supplier_name': pi.supplier.name if pi.supplier else 'Unknown',
                        'pi_ref': f"PI-{str(pi.id)[-4:].upper()}"
                    }
            
            return context
        except Material.DoesNotExist:
            return None

    @staticmethod
    def calculate_abc_analysis():
        with db.atomic():
            materials = list(Material.select())
            if not materials:
                return []

            material_values = []
            for m in materials:
                val = (m.quantity or 0) * (m.unit_cost or 0)
                material_values.append({'material_id': m.id, 'value': val})

            material_values.sort(key=lambda x: x['value'], reverse=True)
            total_value = sum(item['value'] for item in material_values)

            if total_value == 0:
                return []

            cumulative_value = 0
            result = []
            for item in material_values:
                cumulative_value += item['value']
                percentage = (cumulative_value / total_value) * 100

                category = 'C'
                if percentage <= 70:
                    category = 'A'
                elif percentage <= 90:
                    category = 'B'

                item['category'] = category
                result.append(item)
                Material.update(abc_category=category).where(Material.id == item['material_id']).execute()

            return result

    @staticmethod
    def get_material_details(material_id):
        try:
            return Material.get_by_id(material_id)
        except Material.DoesNotExist:
            return None

    @staticmethod
    def get_transaction_history(material_id):
        from database.models import User
        return (Transaction
                .select(Transaction, User)
                .join(User, on=(Transaction.performed_by == User.id))
                .where(Transaction.material == material_id)
                .order_by(Transaction.timestamp.desc()))

    @staticmethod
    def create_material(data):
        with db.atomic():
            material = Material.create(**data)
            AuditService.log('MATERIAL_CREATED', details={'material_id': material.id, 'name': data.get('name', '')})
            return material

    @staticmethod
    def update_material(material_id, data):
        with db.atomic():
            data['updated_at'] = datetime.datetime.now()
            query = Material.update(**data).where(Material.id == material_id)
            result = query.execute()
            AuditService.log('MATERIAL_UPDATED', details={'material_id': material_id})
            return result

    @staticmethod
    def delete_material(material_id):
        with db.atomic():
            from database.models import MRSItem, PIItem
            material = Material.get_by_id(material_id)
            name = material.name
            # Delete related records first to avoid FK errors
            Transaction.delete().where(Transaction.material == material_id).execute()
            MRSItem.delete().where(MRSItem.material == material_id).execute()
            PIItem.delete().where(PIItem.material == material_id).execute()
            material.delete_instance()
            AuditService.log('MATERIAL_DELETED', details={'material_id': material_id, 'name': name})
            return True
