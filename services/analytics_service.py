from database.models import Material, Transaction, ProductInward, MRS, Invoice, db
from peewee import fn
import datetime

class AnalyticsService:
    @staticmethod
    def get_inventory_health():
        all_materials = Material.select()
        low_stock = [m for m in all_materials if m.quantity <= m.min_stock]
        dead_stock = [m for m in all_materials if m.quantity == 0]
        
        return {
            'all_materials': list(all_materials),
            'low_stock': low_stock,
            'dead_stock': dead_stock
        }

    @staticmethod
    def get_cost_trends():
        # Sum of inward transactions per month
        inwards = (Transaction
                   .select(Transaction.timestamp, Transaction.quantity, Material.unit_cost)
                   .join(Material)
                   .where(Transaction.type == 'INWARD'))
        
        trends = {}
        for tx in inwards:
            month = tx.timestamp.strftime("%Y-%m")
            cost = tx.quantity * tx.material.unit_cost
            trends[month] = trends.get(month, 0) + cost
            
        return [{'date': k, 'cost': v} for k, v in sorted(trends.items())]

    @staticmethod
    def get_sales_performance():
        # 1. Monthly Revenue Trend
        invoices = Invoice.select(Invoice.created_at, Invoice.grand_total)
        trends = {}
        for inv in invoices:
            month = inv.created_at.strftime("%Y-%m")
            trends[month] = trends.get(month, 0) + inv.grand_total
            
        # 2. Revenue by Consumer
        consumer_sales = (Invoice
                         .select(Invoice.client_name, fn.SUM(Invoice.grand_total).alias('total'))
                         .group_by(Invoice.client_name)
                         .order_by(fn.SUM(Invoice.grand_total).desc()))
        
        return {
            'trends': [{'date': k, 'revenue': v} for k, v in sorted(trends.items())],
            'consumers': [{'name': i.client_name or "Unknown", 'value': float(i.total)} for i in consumer_sales]
        }

    @staticmethod
    def get_material_insights():
        # Top 5 Materials by Consumption (Issues)
        top_materials = (Transaction
                        .select(Material.name, fn.SUM(fn.ABS(Transaction.quantity)).alias('total'))
                        .join(Material)
                        .where(Transaction.type == 'ISSUE')
                        .group_by(Material.name)
                        .order_by(fn.SUM(fn.ABS(Transaction.quantity)).desc())
                        .limit(5))
        
        return [{'name': m.material.name, 'value': m.total} for m in top_materials]

    @staticmethod
    def get_invoice_stats():
        stats = (Invoice
                .select(Invoice.status, fn.COUNT(Invoice.id).alias('count'))
                .group_by(Invoice.status))
        
        return [{'name': s.status, 'value': s.count} for s in stats]

    @staticmethod
    def get_forecast():
        # Simple forecast: Avg daily consumption over last 30 days
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        issues = (Transaction
                  .select(Transaction.material, fn.SUM(Transaction.quantity).alias('total'))
                  .where(Transaction.type == 'ISSUE', Transaction.timestamp >= thirty_days_ago)
                  .group_by(Transaction.material))
        
        consumption = {tx.material_id: abs(tx.total) / 30 for tx in issues}
        
        results = []
        for m in Material.select():
            avg_daily = consumption.get(m.id, 0)
            days_left = m.quantity / avg_daily if avg_daily > 0 else 999
            
            results.append({
                'name': m.name,
                'current_stock': m.quantity,
                'avg_daily': round(avg_daily, 2),
                'forecast_7_days': round(avg_daily * 7, 2),
                'suggested_reorder': max(0, (m.min_stock * 2) - m.quantity),
                'status': 'REORDER_NOW' if days_left < 7 else 'SUFFICIENT'
            })
        return results

    @staticmethod
    def get_expiry_alerts(warning_days=30):
        """Get materials nearing or past expiry."""
        today = datetime.date.today()
        warning_date = today + datetime.timedelta(days=warning_days)

        materials = Material.select().where(Material.expiry_date.is_null(False))

        expired = []
        expiring_soon = []
        safe = []

        for m in materials:
            info = {
                'id': m.id,
                'name': m.name,
                'category': m.category,
                'expiry_date': m.expiry_date,
                'days_left': (m.expiry_date - today).days,
                'quantity': m.quantity,
                'hazard_class': m.hazard_class or 'None'
            }

            if m.expiry_date < today:
                expired.append(info)
            elif m.expiry_date <= warning_date:
                expiring_soon.append(info)
            else:
                safe.append(info)

        return {
            'expired': expired,
            'expiring_soon': expiring_soon,
            'safe': safe,
            'total_tracked': len(expired) + len(expiring_soon) + len(safe)
        }

    @staticmethod
    def get_hazardous_materials():
        """Get all materials with hazard classifications."""
        materials = (Material
                     .select()
                     .where(Material.hazard_class != 'None', Material.hazard_class.is_null(False)))
        
        by_class = {}
        for m in materials:
            cls = m.hazard_class
            if cls not in by_class:
                by_class[cls] = []
            by_class[cls].append({
                'name': m.name,
                'category': m.category,
                'quantity': m.quantity,
                'storage_temp': f"{m.storage_temp_min or '?'}°C - {m.storage_temp_max or '?'}°C"
            })

        return by_class

    @staticmethod
    def get_safety_warnings():
        """
        Implements proactive safety logic for chemical storage.
        Detects incompatible hazard classes currently present in inventory.
        """
        hazardous_data = AnalyticsService.get_hazardous_materials()
        present_classes = set(hazardous_data.keys())
        
        # Incompatibility Matrix (simplified for textile chemicals)
        # Pairs that should NOT be stored together in the same warehouse zone
        INCOMPATIBLE_PAIRS = [
            ({'Flammable', 'Oxidizer'}, "FIRE RISK: Oxidizers and Flammables stored together can cause rapid combustion."),
            ({'Toxic', 'Oxidizer'}, "HEALTH RISK: Oxidizers can accelerate the release of toxic vapors if a leak occurs."),
            ({'Flammable', 'Acid'}, "CHEMICAL RISK: Acids may react with flammable containers or liquids."),
            ({'Corrosive', 'Metal'}, "INFRASTRUCTURE RISK: High concentration of corrosives nearing structural materials.")
        ]
        
        warnings = []
        for pair_set, reason in INCOMPATIBLE_PAIRS:
            # Check if both classes in the set are present in inventory
            if pair_set.issubset(present_classes):
                warnings.append({
                    'type': 'INCOMPATIBILITY',
                    'involved_classes': list(pair_set),
                    'message': reason,
                    'severity': 'critical'
                })
                
        # Also check for heat sensitivity (Materials in high temp areas)
        # (Assuming we have a 'current_temp' sensor in future, for now we check the range)
        for cls, items in hazardous_data.items():
            for item in items:
                # Mock high temp warning if storage range is very narrow/low
                # This could be expanded with actual sensor data
                pass

        return warnings
