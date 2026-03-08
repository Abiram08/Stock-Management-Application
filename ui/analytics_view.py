from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget, QFrame,
                             QScrollArea, QGridLayout)
from PySide6.QtCore import Qt
from services.analytics_service import AnalyticsService
from services.communication_service import relay
from ui.components.card_widget import CardWidget
from ui.components.chart_widget import ChartWidget
from ui.components.status_badge import StatusBadge
import datetime

class AnalyticsView(QWidget):
    def __init__(self):
        super().__init__()
        self.analytics_service = AnalyticsService()
        self.setup_ui()
        self.load_data()
        
        relay.data_changed.connect(self.load_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Premium Header
        header_layout = QHBoxLayout()
        title_vbox = QVBoxLayout()
        title = QLabel("ANALYTICS COMMAND CENTER")
        title.setStyleSheet("font-size: 22px; font-weight: 900; color: #0f172a; letter-spacing: 1px;")
        subtitle = QLabel("Data-driven insights for inventory, finance, and safety")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 500;")
        title_vbox.addWidget(title)
        title_vbox.addWidget(subtitle)
        header_layout.addLayout(title_vbox)
        header_layout.addStretch()
        
        # Last Updated Badge
        self.last_updated = QLabel(f"LAST SYNC: {datetime.datetime.now().strftime('%H:%M:%S')}")
        self.last_updated.setStyleSheet("background: #f1f5f9; color: #475569; padding: 6px 12px; border-radius: 8px; font-size: 10px; font-weight: 800;")
        header_layout.addWidget(self.last_updated, 0, Qt.AlignTop)
        layout.addLayout(header_layout)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e2e8f0; border-radius: 12px; background: white; top: -1px; }
            QTabBar { background: #f8fafc; border-radius: 10px; padding: 2px; }
            QTabBar::tab { 
                padding: 12px 28px; 
                background: transparent; 
                border: none;
                border-radius: 8px;
                color: #64748b;
                font-weight: 800;
                font-size: 11px;
                margin: 2px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            QTabBar::tab:hover { background: #f1f5f9; color: #1e293b; }
            QTabBar::tab:selected { background: white; color: #6366f1; border: 1px solid #e2e8f0; }
        """)
        
        self.tabs.addTab(self.create_inventory_tab(), "Inventory Health")
        self.tabs.addTab(self.create_sales_tab(), "Financial Insights")
        self.tabs.addTab(self.create_safety_tab(), "Safety Intelligence")
        
        layout.addWidget(self.tabs)

    def create_inventory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # High-level Metrics
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(16)
        self.low_stock_card = self.create_metric_card("Low Stock Items", "0", "rose")
        self.dead_stock_card = self.create_metric_card("Zero Inventory", "0", "amber")
        self.total_sku_card = self.create_metric_card("Managed SKUs", "0", "indigo")
        metrics_layout.addWidget(self.low_stock_card)
        metrics_layout.addWidget(self.dead_stock_card)
        metrics_layout.addWidget(self.total_sku_card)
        layout.addLayout(metrics_layout)
        
        charts_row = QHBoxLayout()
        charts_row.setSpacing(16)
        
        # 1. Distribution Chart (Donut)
        dist_card = self._create_card_container("Inventory Status Composition")
        self.inv_chart = ChartWidget()
        dist_card.layout.addWidget(self.inv_chart)
        
        # 2. Top Demanded Chart (Bar)
        demand_card = self._create_card_container("Top Consumption Velociy")
        self.demand_chart = ChartWidget()
        demand_card.layout.addWidget(self.demand_chart)
        
        charts_row.addWidget(dist_card, 1)
        charts_row.addWidget(demand_card, 1)
        layout.addLayout(charts_row)
        layout.addStretch()
        return tab

    def create_sales_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)
        
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        
        # Growth Line Chart
        rev_card = self._create_card_container("Revenue Trajectory (Past 6 Months)")
        self.revenue_chart = ChartWidget()
        rev_card.layout.addWidget(self.revenue_chart)
        
        # Consumer Distribution Donut
        consumer_card = self._create_card_container("Top 5 Consumer Contributions")
        consumer_card.setFixedWidth(380)
        self.consumer_chart = ChartWidget()
        consumer_card.layout.addWidget(self.consumer_chart)
        
        top_row.addWidget(rev_card, 2)
        top_row.addWidget(consumer_card, 1)
        layout.addLayout(top_row)
        
        # Invoice Status Tracking
        invoice_card = self._create_card_container("Transactional Ecosystem Status")
        self.status_chart = ChartWidget()
        invoice_card.layout.addWidget(self.status_chart)
        layout.addWidget(invoice_card)
        layout.addStretch()
        
        return tab

    def create_safety_tab(self):
        tab = QScrollArea()
        tab.setWidgetResizable(True)
        tab.setStyleSheet("background: transparent; border: none;")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Safety Alert Banner Zone
        self.safety_alerts_vbox = QVBoxLayout()
        self.safety_alerts_vbox.setSpacing(10)
        layout.addLayout(self.safety_alerts_vbox)
        
        # Top Row: Expiry Monitor and Hazard Distribution
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        
        expiry_card = self._create_card_container("Expiry Countdown Tracking")
        self.expiry_chart = ChartWidget()
        expiry_card.layout.addWidget(self.expiry_chart)
        
        hazard_card = self._create_card_container("Hazard Classification Distribution")
        hazard_card.setFixedWidth(380)
        self.hazard_chart = ChartWidget()
        hazard_card.layout.addWidget(self.hazard_chart)
        
        top_row.addWidget(expiry_card, 2)
        top_row.addWidget(hazard_card, 1)
        layout.addLayout(top_row)
        
        # Bottom Row: Detailed Expiry Alerts
        self.expiry_details_card = self._create_card_container("Critical Expiry Alerts (< 30 Days)")
        self.expiry_table = QTableWidget()
        self.expiry_table.setColumnCount(4)
        self.expiry_table.setHorizontalHeaderLabels(["MATERIAL", "CLASS", "EXPIRY", "DAYS LEFT"])
        self.expiry_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.expiry_table.setMinimumHeight(200)
        self.expiry_table.verticalHeader().setVisible(False)
        self.expiry_table.setStyleSheet("border: none; gridline-color: #f1f5f9;")
        self.expiry_details_card.layout.addWidget(self.expiry_table)
        layout.addWidget(self.expiry_details_card)
        
        layout.addStretch()
        tab.setWidget(container)
        return tab

    def _create_card_container(self, title):
        card = CardWidget()
        card.layout.setContentsMargins(20, 20, 20, 20)
        card.layout.setSpacing(12)
        t = QLabel(title.upper())
        t.setStyleSheet("font-size: 10px; font-weight: 900; color: #475569; letter-spacing: 0.8px;")
        card.layout.insertWidget(0, t)
        return card

    def create_metric_card(self, title, val, color_key):
        card = CardWidget()
        card.setFixedHeight(110)
        card.layout.setContentsMargins(20, 16, 20, 16)
        card.layout.setSpacing(0) # Let stretches handle centering
        
        t = QLabel(title.upper())
        t.setStyleSheet("font-size: 9px; color: #64748b; font-weight: 800; letter-spacing: 0.5px;")
        t.setAlignment(Qt.AlignCenter)
        
        v = QLabel(val)
        colors = {'rose': '#8B5E3C', 'amber': '#A67B5B', 'indigo': '#734D31'}
        v.setStyleSheet(f"font-size: 32px; font-weight: 900; color: {colors.get(color_key, '#000000')};")
        v.setAlignment(Qt.AlignCenter)
        
        card.layout.addWidget(t)
        card.add_centered_widget(v)
        card.value_label = v 
        return card

    def load_data(self):
        self.last_updated.setText(f"LAST SYNC: {datetime.datetime.now().strftime('%H:%M:%S')}")
        
        # 1. Inventory Insights
        inv = AnalyticsService.get_inventory_health()
        self.low_stock_card.value_label.setText(str(len(inv['low_stock'])))
        self.dead_stock_card.value_label.setText(str(len(inv['dead_stock'])))
        self.total_sku_card.value_label.setText(str(len(inv['all_materials'])))
        
        low_only = len(inv['low_stock']) - len(inv['dead_stock'])
        healthy = len(inv['all_materials']) - len(inv['low_stock'])
        self.inv_chart.draw_pie(
            ['Healthy', 'Low Stock', 'Dead Stock'], 
            [healthy, low_only, len(inv['dead_stock'])],
            "Inventory Health Ratio"
        )
        
        demands = AnalyticsService.get_material_insights()
        if demands:
            self.demand_chart.draw_bar(
                [d['name'] for d in demands],
                [d['value'] for d in demands],
                "Highest Consumption Velocity",
                color='#8B5E3C'
            )
            
        # 2. Sales & Finance
        sales = AnalyticsService.get_sales_performance()
        if sales['trends']:
            self.revenue_chart.draw_line(
                [t['date'] for t in sales['trends']],
                [t['revenue'] for t in sales['trends']],
                "Monthly Revenue Trajectory (INR)",
                color='#734D31'
            )
        
        if sales['consumers']:
            self.consumer_chart.draw_pie(
                [c['name'][:15] for c in sales['consumers'][:5]],
                [c['value'] for c in sales['consumers'][:5]],
                "Consumer Contribution Share"
            )
            
        status_stats = AnalyticsService.get_invoice_stats()
        if status_stats:
            self.status_chart.draw_bar(
                [s['name'] for s in status_stats],
                [s['value'] for s in status_stats],
                "Invoicing Lifecycle Maturity",
                color='#8B5E3C'
            )

        # 3. Safety Intelligence
        hazards = AnalyticsService.get_hazardous_materials()
        if hazards:
            self.hazard_chart.draw_pie(
                list(hazards.keys()),
                [len(v) for v in hazards.values()],
                "Chemical Hazard Composition"
            )
            
        expiry = AnalyticsService.get_expiry_alerts(warning_days=30)
        self.expiry_chart.draw_bar(
            ['Expired', 'Expiring <30d', 'Safe'],
            [len(expiry['expired']), len(expiry['expiring_soon']), len(expiry['safe'])],
            "Time-to-Expiry Monitor",
            color='#A67B5B'
        )
        
        # Fill Expiry Table
        total_soon = expiry['expired'] + expiry['expiring_soon']
        self.expiry_table.setRowCount(len(total_soon))
        for i, item in enumerate(total_soon):
            self.expiry_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.expiry_table.setItem(i, 1, QTableWidgetItem(item['hazard_class']))
            self.expiry_table.setItem(i, 2, QTableWidgetItem(str(item['expiry_date'])))
            
            days_left = item['days_left']
            lbl = f"{days_left}d left" if days_left >= 0 else "EXPIRED"
            status = 'critical' if days_left <= 7 else 'warning'
            badge = StatusBadge(lbl, status)
            self.expiry_table.setCellWidget(i, 3, badge)

        # Load Safety Warnings
        # Clear old alerts first
        while self.safety_alerts_vbox.count():
            item = self.safety_alerts_vbox.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            
        warnings = AnalyticsService.get_safety_warnings()
        for w in warnings:
            alert = QFrame()
            alert.setStyleSheet("background: #fff1f2; border: 1px solid #fecaca; border-radius: 8px;")
            alert_layout = QHBoxLayout(alert)
            msg = QLabel(f"⚠️ <b>SAFETY ALERT:</b> {w['message']}")
            msg.setStyleSheet("color: #991b1b; font-size: 12px;")
            alert_layout.addWidget(msg)
            self.safety_alerts_vbox.addWidget(alert)
