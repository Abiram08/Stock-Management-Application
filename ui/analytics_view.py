from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QFrame)
from PySide6.QtCore import Qt
from services.analytics_service import AnalyticsService
from services.communication_service import relay
from ui.components.card_widget import CardWidget
from ui.components.chart_widget import ChartWidget
from database.models import AuditLog, User

class AnalyticsView(QWidget):
    def __init__(self):
        super().__init__()
        self.analytics_service = AnalyticsService()
        self.setup_ui()
        self.load_data()
        
        # Connect to reactivity system
        relay.data_changed.connect(self.load_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        title = QLabel("COMMAND CENTER")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e293b; letter-spacing: 1px;")
        layout.addWidget(title)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 12px; background: white; top: 0px; margin-top: 10px; }
            QTabBar { background: #f1f5f9; border-radius: 10px; padding: 4px; }
            QTabBar::tab { 
                padding: 10px 24px; 
                background: transparent; 
                border: none;
                border-radius: 8px;
                color: #64748b;
                font-weight: 700;
                font-size: 12px;
                margin-right: 2px;
            }
            QTabBar::tab:hover {
                background: rgba(0,0,0,0.03);
            }
            QTabBar::tab:selected { 
                background: white; 
                color: #8B5E3C; 
            }
        """)
        
        self.tabs.addTab(self.create_inventory_tab(), "Inventory Intelligence")
        self.tabs.addTab(self.create_sales_tab(), "Sales Performance")
        self.tabs.addTab(self.create_cost_tab(), "Financial Insights")
        
        layout.addWidget(self.tabs)

    def create_inventory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(15)
        self.low_stock_card = self.create_metric_card("Low Stock Items", "0", "critical")
        self.dead_stock_card = self.create_metric_card("Dead Stock", "0", "warning")
        self.total_sku_card = self.create_metric_card("Total SKU", "0", "neutral")
        metrics_layout.addWidget(self.low_stock_card)
        metrics_layout.addWidget(self.dead_stock_card)
        metrics_layout.addWidget(self.total_sku_card)
        layout.addLayout(metrics_layout)
        
        charts_row = QHBoxLayout()
        
        # 1. Distribution Chart
        dist_card = CardWidget()
        dist_card.layout.setContentsMargins(10, 10, 10, 10)
        dist_card.layout.setSpacing(2)
        dist_title = QLabel("INVENTORY STATUS DISTRIBUTION")
        dist_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 5px;")
        dist_card.addWidget(dist_title)
        self.inv_chart = ChartWidget()
        dist_card.addWidget(self.inv_chart)
        
        # 2. Top Demanded Chart
        demand_card = CardWidget()
        demand_card.layout.setContentsMargins(10, 10, 10, 10)
        demand_card.layout.setSpacing(2)
        demand_title = QLabel("TOP DEMANDED MATERIALS (CONSUMPTION)")
        demand_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 5px;")
        demand_card.addWidget(demand_title)
        self.demand_chart = ChartWidget()
        demand_card.addWidget(self.demand_chart)
        
        charts_row.addWidget(dist_card, 1)
        charts_row.addWidget(demand_card, 1)
        layout.addLayout(charts_row)
        layout.addStretch()
        return tab

    def create_sales_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Revenue and Consumer Contribution Row
        top_row = QHBoxLayout()
        
        rev_card = CardWidget()
        rev_card.layout.setContentsMargins(10, 10, 10, 10)
        rev_card.layout.setSpacing(2)
        rev_title = QLabel("REVENUE GROWTH (INR) - PAST 6 MONTHS")
        rev_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 5px;")
        rev_card.addWidget(rev_title)
        self.revenue_chart = ChartWidget()
        rev_card.addWidget(self.revenue_chart)
        
        consumer_card = CardWidget()
        consumer_card.setFixedWidth(400)
        consumer_card.layout.setContentsMargins(10, 10, 10, 10)
        consumer_card.layout.setSpacing(2)
        consumer_title = QLabel("REVENUE BY CONSUMER")
        consumer_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 5px;")
        consumer_card.addWidget(consumer_title)
        self.consumer_chart = ChartWidget()
        consumer_card.addWidget(self.consumer_chart)
        
        top_row.addWidget(rev_card, 2)
        top_row.addWidget(consumer_card, 1)
        layout.addLayout(top_row)
        
        # Invoice distribution
        invoice_card = CardWidget()
        invoice_card.layout.setContentsMargins(10, 10, 10, 10)
        invoice_card.layout.setSpacing(2)
        invoice_title = QLabel("INVOICE STATUS DISTRIBUTION")
        invoice_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 5px;")
        invoice_card.addWidget(invoice_title)
        self.status_chart = ChartWidget()
        invoice_card.addWidget(self.status_chart)
        layout.addWidget(invoice_card)
        layout.addStretch()
        
        return tab

    def create_metric_card(self, title, val, status):
        from ui.components.card_widget import CardWidget
        card = CardWidget()
        card.setFixedHeight(95)
        card.layout.setContentsMargins(15, 12, 15, 12)
        card.layout.setSpacing(2)
        
        t = QLabel(title.upper())
        t.setStyleSheet("font-size: 10px; color: #1e293b; font-weight: 800; letter-spacing: 0.8px;")
        
        v = QLabel(val)
        colors = {'critical': '#dc2626', 'warning': '#d97706', 'neutral': '#0f172a'}
        v.setStyleSheet(f"font-size: 28px; font-weight: 900; color: {colors.get(status, '#0f172a')};")
        
        card.addWidget(t)
        card.addWidget(v)
        card.value_label = v 
        return card

    def create_cost_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        chart_card = CardWidget()
        chart_card.layout.setContentsMargins(10, 10, 10, 10)
        chart_card.layout.setSpacing(2)
        chart_title = QLabel("MONTHLY PROCUREMENT EXPENDITURE (INR) - PAST 6 MONTHS")
        chart_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; margin-bottom: 5px;")
        chart_card.addWidget(chart_title)
        
        self.cost_chart = ChartWidget()
        chart_card.addWidget(self.cost_chart)
        layout.addWidget(chart_card)
        layout.addStretch()
        return tab


    def load_data(self):
        # 1. Inventory Intelligence
        inv = AnalyticsService.get_inventory_health()
        self.low_stock_card.value_label.setText(str(len(inv['low_stock'])))
        self.dead_stock_card.value_label.setText(str(len(inv['dead_stock'])))
        self.total_sku_card.value_label.setText(str(len(inv['all_materials'])))
        
        # low_stock includes dead_stock (qty=0 is also <= min_stock), so subtract dead from low for accurate chart
        low_only = len(inv['low_stock']) - len(inv['dead_stock'])
        healthy = len(inv['all_materials']) - len(inv['low_stock'])
        self.inv_chart.draw_pie(
            ['Healthy', 'Low Stock', 'Dead Stock'], 
            [healthy, low_only, len(inv['dead_stock'])],
            "INVENTORY HEALTH RATIO"
        )
        
        demands = AnalyticsService.get_material_insights()
        if demands:
            self.demand_chart.draw_bar(
                [d['name'] for d in demands],
                [d['value'] for d in demands],
                "TOP CONSUMED MATERIALS (QTY)",
                color='#10b981'
            )
            
        # 2. Sales Performance
        sales = AnalyticsService.get_sales_performance()
        if sales['trends']:
            self.revenue_chart.draw_line(
                [t['date'] for t in sales['trends']],
                [t['revenue'] for t in sales['trends']],
                "MONTHLY REVENUE TREND (INR)"
            )
        
        if sales['consumers']:
            self.consumer_chart.draw_pie(
                [c['name'][:15] for c in sales['consumers'][:5]],
                [c['value'] for c in sales['consumers'][:5]],
                "TOP 5 CONSUMERS (REVENUE)"
            )
            
        status_stats = AnalyticsService.get_invoice_stats()
        if status_stats:
            self.status_chart.draw_bar(
                [s['name'] for s in status_stats],
                [s['value'] for s in status_stats],
                "TOTAL INVOICES BY STATUS",
                color='#f59e0b'
            )

        # 3. Financial Costs
        costs = AnalyticsService.get_cost_trends()
        if costs:
            self.cost_chart.draw_line(
                [c['date'] for c in costs], 
                [c['cost'] for c in costs], 
                "MONTHLY PROCUREMENT SPENDING",
                color='#8b5cf6'
            )
