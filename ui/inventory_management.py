from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QMessageBox)
from PySide6.QtCore import Qt
from services.inventory_service import InventoryService
from services.communication_service import relay
from ui.components.status_badge import StatusBadge
from ui.material_details_view import MaterialDetailsDialog
from utils.export_service import ExportService
from utils.async_worker import QueryWorker

class InventoryManagementView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()
        
        # Connect to reactivity system
        relay.data_changed.connect(self.load_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Header Card
        from ui.components.card_widget import CardWidget
        header_card = CardWidget()
        header_card.layout.setContentsMargins(20, 20, 20, 20)
        
        header_row = QHBoxLayout()
        title_container = QVBoxLayout()
        title = QLabel("Inventory Overview")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Manage stock levels, track consumption, and monitor critical items.")
        subtitle.setObjectName("SubtitleLabel")
        title_container.addWidget(title)
        title_container.addWidget(subtitle)
        header_row.addLayout(title_container)
        header_row.addStretch()
        
        # Search & Actions
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search materials...")
        self.search_input.setFixedWidth(280)
        self.search_input.setFixedHeight(38)
        self.search_input.textChanged.connect(self.filter_data)
        
        self.btn_add_material = QPushButton("+ Add Material")
        self.btn_add_material.setProperty("class", "PrimaryButton")
        self.btn_add_material.clicked.connect(self.show_add_material)

        self.btn_refresh = QPushButton("↻ Refresh")
        self.btn_refresh.setProperty("class", "SecondaryButton")
        self.btn_refresh.clicked.connect(self.load_data)

        self.btn_abc = QPushButton("ABC Analysis")
        self.btn_abc.setProperty("class", "SecondaryButton")
        self.btn_abc.clicked.connect(self.run_abc_analysis)
        
        self.btn_export = QPushButton("⬇ Export CSV")
        self.btn_export.setProperty("class", "SecondaryButton")
        self.btn_export.clicked.connect(lambda: ExportService.export_table_to_csv(self.table, self, "inventory_data.csv"))
        
        actions_layout.addWidget(self.search_input)
        actions_layout.addWidget(self.btn_add_material)
        actions_layout.addWidget(self.btn_export)
        actions_layout.addWidget(self.btn_abc)
        actions_layout.addWidget(self.btn_refresh)
        header_row.addLayout(actions_layout)
        header_card.addLayout(header_row)
        
        layout.addWidget(header_card)
        
        # Table Section
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Material Details", "Supplier", "Live Stock", "Status", "Actions"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Material Details
        header.setSectionResizeMode(4, QHeaderView.Fixed) # Actions
        
        self.table.setColumnWidth(4, 160) # Actions column
        
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60) # Standard premium height
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { 
                background: #FFFFFF; 
                border-radius: 12px; 
                padding: 10px;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Context Menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # Footer Legends
        footer_layout = QHBoxLayout()

        legend_style = "font-size: 11px; font-weight: 600; padding: 4px 12px; border-radius: 6px;"
        
        legend1 = QLabel("● Low / Out of Stock")
        legend1.setStyleSheet(f"color: #ef4444; background: rgba(239, 68, 68, 0.1); {legend_style}")
        
        legend2 = QLabel("● Sufficient Stock")
        legend2.setStyleSheet(f"color: #22c55e; background: rgba(34, 197, 94, 0.1); {legend_style}")
        
        footer_layout.addWidget(legend1)
        footer_layout.addWidget(legend2)
        footer_layout.addStretch()
        layout.addLayout(footer_layout)

    def load_data(self):
        # Display a simple placeholder while loading
        self.table.setRowCount(0)
        self.search_input.setEnabled(False)
        self.btn_refresh.setText("↻ Loading...")
        self.btn_refresh.setEnabled(False)
        
        self.worker = QueryWorker(InventoryService.get_all_materials)
        self.worker.finished.connect(self._on_data_loaded)
        self.worker.error.connect(self._on_data_error)
        self.worker.start()

    def _on_data_loaded(self, materials_list):
        self.search_input.setEnabled(True)
        self.btn_refresh.setText("↻ Refresh")
        self.btn_refresh.setEnabled(True)
        self.materials = materials_list
        # Re-apply current search filter if any
        self.filter_data()

    def _on_data_error(self, err_msg):
        self.search_input.setEnabled(True)
        self.btn_refresh.setText("↻ Refresh")
        self.btn_refresh.setEnabled(True)
        QMessageBox.critical(self, "Data Load Error", f"Failed to load inventory:\n{err_msg}")

    def display_data(self, materials_list):
        self.table.setRowCount(len(materials_list))
        for i, m in enumerate(materials_list):
            # 1. Details (Name + ABC Category + Cost)
            detail_widget = QWidget()
            detail_layout = QVBoxLayout(detail_widget)
            detail_layout.setContentsMargins(10, 5, 10, 5)
            
            name_layout = QHBoxLayout()
            name_label = QLabel(m.name)
            name_label.setStyleSheet("font-weight: bold; color: #1E293B;")
            name_layout.addWidget(name_label)
            
            if m.code:
                code_label = QLabel(m.code)
                code_label.setStyleSheet("font-size: 10px; color: #64748B; background: #F1F5F9; padding: 2px 6px; border-radius: 4px; font-weight: 600;")
                name_layout.addWidget(code_label)
            
            if m.abc_category and m.abc_category != 'None':
                abc_label = QLabel(m.abc_category)
                abc_colors = {'A': '#dc2626', 'B': '#d97706', 'C': '#65a30d'}
                abc_color = abc_colors.get(m.abc_category, '#64748B')
                abc_label.setStyleSheet(f"font-size: 10px; color: white; background: {abc_color}; padding: 2px 6px; border-radius: 4px; font-weight: 700;")
                name_layout.addWidget(abc_label)
            
            name_layout.addStretch()
            
            detail_layout.addLayout(name_layout)
            cost_label = QLabel(f"Unit Cost: ₹{m.unit_cost:,.2f}")
            cost_label.setStyleSheet("color: #64748B; font-size: 11px;")
            detail_layout.addWidget(cost_label)
            
            self.table.setCellWidget(i, 0, detail_widget)
            
            # 2. Supplier
            supplier_name = m.supplier.name if m.supplier else "N/A"
            supplier_item = QTableWidgetItem(supplier_name)
            supplier_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, supplier_item)
            
            # 3. Live Stock
            stock_item = QTableWidgetItem(f"{m.quantity} {m.unit}")
            stock_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, stock_item)
            
            # 4. Status (Wrapped for centering)
            status_type = 'critical' if m.quantity == 0 else 'warning' if m.quantity <= m.min_stock else 'success'
            status_text = 'Dead Stock' if m.quantity == 0 else 'Low Stock' if m.quantity <= m.min_stock else 'In Stock'
            status_badge = StatusBadge(status_text, status_type)
            
            status_container = QWidget()
            status_layout = QHBoxLayout(status_container)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.setAlignment(Qt.AlignCenter)
            status_layout.addWidget(status_badge)
            self.table.setCellWidget(i, 3, status_container)
            
            # 5. Action
            btn_details = QPushButton("ⓘ")
            btn_details.setFixedSize(32, 32)
            btn_details.setCursor(Qt.PointingHandCursor)
            btn_details.setToolTip("View History & Details")
            btn_details.setStyleSheet("""
                QPushButton {
                    background-color: #F8FAFC;
                    color: #475569;
                    border: 1px solid #E2E8F0;
                    border-radius: 16px;
                    font-size: 16px;
                    font-weight: 800;
                }
                QPushButton:hover {
                    background-color: #475569;
                    color: white;
                    border: none;
                }
            """)
            btn_details.clicked.connect(lambda checked=False, mid=m.id: self.show_details(mid))
            
            btn_edit = QPushButton("✎")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setToolTip("Edit Material")
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #8B5E3C;
                    border: 1px solid #E5E7EB;
                    border-radius: 16px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #8B5E3C;
                    color: white;
                    border: none;
                }
            """)
            btn_edit.clicked.connect(lambda checked=False, mat=m: self.show_edit_material(mat))

            btn_del = QPushButton("✕")
            btn_del.setFixedSize(32, 32)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setToolTip("Delete Material")
            btn_del.setStyleSheet("""
                QPushButton {
                    background-color: #FEE2E2;
                    color: #EF4444;
                    border: 1px solid #FECACA;
                    border-radius: 16px;
                    font-size: 14px;
                    font-weight: 800;
                }
                QPushButton:hover {
                    background-color: #EF4444;
                    color: white;
                    border: none;
                }
            """)
            btn_del.clicked.connect(lambda checked=False, mid=m.id: self.confirm_delete_material(mid))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 10, 0) # Added right margin to prevent clipping
            action_layout.setSpacing(12)
            action_layout.addStretch()
            action_layout.addWidget(btn_details)
            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_del)
            # action_layout.addStretch() # Removed trailing stretch to favor left-leaning/centered alignment
            self.table.setCellWidget(i, 4, action_widget)

    def show_add_material(self):
        from ui.material_form_dialog import MaterialFormDialog
        dialog = MaterialFormDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def show_edit_material(self, material):
        from ui.material_form_dialog import MaterialFormDialog
        dialog = MaterialFormDialog(material=material, parent=self)
        if dialog.exec():
            self.load_data()

    def confirm_delete_material(self, material_id):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   "Are you sure you want to delete this material and all its history?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            InventoryService.delete_material(material_id)
            self.load_data()

    def filter_data(self):
        term = self.search_input.text().lower()
        filtered = [m for m in self.materials if term in m.name.lower()]
        self.display_data(filtered)


    def show_details(self, material_id):
        dialog = MaterialDetailsDialog(material_id, self)
        dialog.exec()

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        row = item.row()
        # Find material associated with this row
        # (Assuming the list hasn't changed since load_data)
        # Better: store ID in a hidden column or map row to ID
        # For now, we'll re-fetch or use the list
        try:
            material = self.materials[row]
            from PySide6.QtWidgets import QMenu
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 4px; }
                QMenu::item { padding: 8px 24px; border-radius: 4px; color: #1e293b; font-size: 11px; font-weight: 500; }
                QMenu::item:selected { background-color: #f1f5f9; color: #6366f1; }
            """)
            
            act_details = menu.addAction("View Transaction History")
            act_edit = menu.addAction("Edit Material")
            menu.addSeparator()
            act_delete = menu.addAction("Delete Record")
            
            action = menu.exec(self.table.mapToGlobal(pos))
            
            if action == act_details: self.show_details(material.id)
            elif action == act_edit: self.show_edit_material(material)
            elif action == act_delete: self.confirm_delete_material(material.id)
        except Exception:
            pass


    def run_abc_analysis(self):
        from database.models import Material as MaterialModel
        result = InventoryService.calculate_abc_analysis()
        if not result:
            QMessageBox.information(self, "ABC Analysis", "No inventory data available for analysis.")
            return
        
        updated = 0
        for item in result:
            try:
                mat = MaterialModel.get_by_id(item['material_id'])
                mat.abc_category = item['category']
                mat.save()
                updated += 1
            except Exception:
                pass
        
        self.load_data()
        QMessageBox.information(self, "ABC Analysis Complete", 
                               f"Classified {updated} materials into A/B/C categories.\n\n"
                               "• A = High value (top 70% of inventory value)\n"
                               "• B = Medium value (next 20%)\n"
                               "• C = Low value (bottom 10%)")
