from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QComboBox, QFrame, QScrollArea, QTabWidget, QMessageBox, QTextEdit)
from PySide6.QtCore import Qt
from services.procurement_service import ProcurementService
from services.inventory_service import InventoryService
from services.validators import validate_required, validate_positive_float, collect_errors
from ui.components.status_badge import StatusBadge
from services.communication_service import relay

class ProcurementManagerView(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setup_ui()
        self.load_data()

        # Connect to reactivity system
        relay.data_changed.connect(self.load_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
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
        
        # Tab 1: Raise PI
        self.has_raise_tab = self.user.role in ['STORE_MANAGER', 'ADMIN']
        if self.has_raise_tab:
            self.tabs.addTab(self.create_raise_pi_tab(), "Raise Purchase Indent")
            
        # Tab 2: Approvals (Admin Only)
        if self.user.role == 'ADMIN':
            self.tabs.addTab(self.create_approvals_tab(), "PI Approvals")
            
        # Tab 3: Inward Entry
        if self.user.role in ['STORE_MANAGER', 'ADMIN']:
            self.inward_tab_widget = self.create_inward_tab()
            self.tabs.addTab(self.inward_tab_widget, "Inward Entry")
        else:
            self.inward_tab_widget = None
            
        layout.addWidget(self.tabs)

    def create_raise_pi_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)
        
        from ui.components.card_widget import CardWidget
        
        # Form Side
        form_card = CardWidget()
        form_layout = form_card.layout
        
        h_label = QLabel("PURCHASE INDENT DETAILS")
        h_label.setStyleSheet("font-size: 11px; font-weight: 700; color: #94a3b8; letter-spacing: 1px;")
        form_layout.addWidget(h_label)
        
        form_layout.addWidget(QLabel("REASON / REMARKS"))
        self.pi_reason = QTextEdit()
        self.pi_reason.setPlaceholderText("e.g. Monthly Restock...")
        self.pi_reason.setFixedHeight(80)
        form_layout.addWidget(self.pi_reason)
        
        items_header = QHBoxLayout()
        items_header.addWidget(QLabel("ORDER ITEMS"))
        self.btn_add_pi_row = QPushButton("+ Add Item")
        self.btn_add_pi_row.setStyleSheet("color: #8B5E3C; background: rgba(139, 94, 60, 0.1); border: none; padding: 6px 14px; border-radius: 14px; font-weight: 700;")
        self.btn_add_pi_row.clicked.connect(self.add_pi_row)
        items_header.addStretch()
        items_header.addWidget(self.btn_add_pi_row)
        form_layout.addLayout(items_header)
        
        self.pi_items_scroll = QScrollArea()
        self.pi_items_scroll.setWidgetResizable(True)
        self.pi_items_scroll.setStyleSheet("background: transparent; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px;")
        self.pi_items_container = QWidget()
        self.pi_items_layout = QVBoxLayout(self.pi_items_container)
        self.pi_items_layout.setAlignment(Qt.AlignTop)
        self.pi_items_layout.setSpacing(8)
        self.pi_items_scroll.setWidget(self.pi_items_container)
        form_layout.addWidget(self.pi_items_scroll)
        
        self.pi_rows = []
        self.add_pi_row()
        
        self.btn_submit_pi = QPushButton("Submit Purchase Indent")
        self.btn_submit_pi.setProperty("class", "PrimaryButton")
        self.btn_submit_pi.setFixedWidth(220)
        self.btn_submit_pi.clicked.connect(self.submit_pi)
        form_layout.addWidget(self.btn_submit_pi, alignment=Qt.AlignRight)
        
        layout.addWidget(form_card, 3)
        
        # Recommendation Side
        rec_card = CardWidget()
        rec_card.setStyleSheet("background: #FFFFFF; border: 1px solid #E2E8F0;")
        rec_layout = rec_card.layout
        
        rec_title = QLabel("AI PROCUREMENT ASSISTANT")
        rec_title.setStyleSheet("font-weight: 800; font-size: 11px; color: #1E293B; letter-spacing: 1.5px;")
        rec_layout.addWidget(rec_title)
        
        self.rec_info = QLabel("Analyzing stock levels...")
        self.rec_info.setStyleSheet("font-size: 13px; color: #000000; margin-top: 10px; font-weight: 500;")
        self.rec_info.setWordWrap(True)
        rec_layout.addWidget(self.rec_info)
        
        btn_autofill = QPushButton("Auto-Fill Recommendations")
        btn_autofill.setStyleSheet("background: #000000; color: white; font-weight: 700; padding: 12px; border-radius: 8px; border: none; margin-top: 20px;")
        btn_autofill.clicked.connect(self.autofill_recommended)
        btn_autofill.setCursor(Qt.PointingHandCursor)
        
        rec_layout.addStretch()
        rec_layout.addWidget(btn_autofill)
        
        layout.addWidget(rec_card, 1)
        
        return tab

    def add_pi_row(self, material_id=None, qty=0):
        row = QFrame()
        row.setObjectName("Card")
        row_layout = QHBoxLayout(row)
        
        combo = QComboBox()
        materials = InventoryService.get_all_materials()
        for m in materials:
            combo.addItem(m.name, m.id)
        if material_id:
            idx = combo.findData(material_id)
            if idx >= 0: combo.setCurrentIndex(idx)
            
        qty_input = QLineEdit()
        qty_input.setPlaceholderText("Qty")
        qty_input.setText(str(qty) if qty > 0 else "")
        qty_input.setFixedWidth(80)
        
        btn_del = QPushButton("✕")
        btn_del.clicked.connect(lambda checked=False, r=row: self.remove_pi_row(r))
        
        row_layout.addWidget(combo, 3)
        row_layout.addWidget(qty_input, 1)
        row_layout.addWidget(btn_del)
        
        self.pi_items_layout.addWidget(row)
        self.pi_rows.append({'row': row, 'combo': combo, 'qty': qty_input})

    def remove_pi_row(self, row_widget):
        row_widget.deleteLater()
        self.pi_rows = [r for r in self.pi_rows if r['row'] != row_widget]

    def autofill_recommended(self):
        recs = ProcurementService.get_recommendations()
        if not recs:
            QMessageBox.information(self, "Healthy Stock", "No low stock items found.")
            return
        
        # Clear existing
        for r in self.pi_rows: r['row'].deleteLater()
        self.pi_rows = []
        
        for r in recs:
            self.add_pi_row(r['material_id'], r['quantity'])
        self.pi_reason.setText("Auto-generated replenishment for low stock items.")

    def create_approvals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.approval_table = QTableWidget()
        self.approval_table.setColumnCount(5)
        self.approval_table.setHorizontalHeaderLabels(["PI Code", "Raised By", "Date", "Status", "Action"])
        self.approval_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.approval_table)
        return tab

    def create_inward_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.inward_table = QTableWidget()
        self.inward_table.setColumnCount(5)
        self.inward_table.setHorizontalHeaderLabels(["Order #", "Supplier", "Date", "Status", "Action"])
        self.inward_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.inward_table)
        return tab

    def load_data(self):
        pis = ProcurementService.get_all_pis()
        self.refresh_approvals(pis)
        self.refresh_inward(pis)
        
        # Update rec info (only if the Raise PI tab was created)
        if self.has_raise_tab and hasattr(self, 'rec_info'):
            recs = ProcurementService.get_recommendations()
            self.rec_info.setText(f"{len(recs)} items below threshold. Action: Restock immediately.")

    def refresh_approvals(self, pis):
        if self.user.role != 'ADMIN': return
        pending = [p for p in pis if p.status == 'RAISED']
        self.approval_table.setRowCount(len(pending))
        for i, p in enumerate(pending):
            self.approval_table.setItem(i, 0, QTableWidgetItem(f"PI-{str(p.id)[-4:].upper()}"))
            self.approval_table.setItem(i, 1, QTableWidgetItem(p.store_manager.username))
            self.approval_table.setItem(i, 2, QTableWidgetItem(p.created_at.strftime("%Y-%m-%d")))
            self.approval_table.setCellWidget(i, 3, StatusBadge(p.status, 'warning'))
            
            btn = QPushButton("Review")
            btn.clicked.connect(lambda checked=False, pi=p: self.review_pi(pi))
            self.approval_table.setCellWidget(i, 4, btn)

    def review_pi(self, pi):
        # Quick dialog for approval
        reply = QMessageBox.question(self, "Approve PI", f"Approve {pi.reason}?\nAdd remarks:", QMessageBox.Yes | QMessageBox.No)
        status = 'APPROVED' if reply == QMessageBox.Yes else 'REJECTED'
        ProcurementService.update_pi_status(pi.id, self.user.id, status, "Desktop Approval")
        self.load_data()

    def refresh_inward(self, pis):
        active = [p for p in pis if p.status in ['APPROVED', 'COMPLETED']]
        self.inward_table.setRowCount(len(active))
        for i, p in enumerate(active):
            self.inward_table.setItem(i, 0, QTableWidgetItem(f"PO-{str(p.id)[-4:].upper()}"))
            self.inward_table.setItem(i, 1, QTableWidgetItem(p.supplier.name))
            self.inward_table.setItem(i, 2, QTableWidgetItem(p.created_at.strftime("%Y-%m-%d")))
            self.inward_table.setCellWidget(i, 3, StatusBadge(p.status, 'success' if p.status=='COMPLETED' else 'warning'))
            
            if p.status == 'APPROVED':
                btn = QPushButton("Inward")
                btn.clicked.connect(lambda checked=False, pi=p: self.complete_inward(pi))
                self.inward_table.setCellWidget(i, 4, btn)
            else:
                self.inward_table.setItem(i, 4, QTableWidgetItem("Completed"))

    def complete_inward(self, pi):
        ProcurementService.process_inward(pi.id, self.user.id, 5) # Default 5 star
        QMessageBox.information(self, "Stock Updated", "Goods received and stock totals updated.")
        self.load_data()

    def submit_pi(self):
        reason = self.pi_reason.toPlainText().strip()

        # Validate header
        validations = [
            validate_required(reason, "Reason / Remarks"),
        ]

        # Validate item rows
        items = []
        has_valid_item = False
        for i, r in enumerate(self.pi_rows):
            mid = r['combo'].currentData()
            qty_text = r['qty'].text().strip()
            if not mid and not qty_text:
                continue
            if mid and qty_text:
                qty_valid, qty_msg, qty_val = validate_positive_float(qty_text, f"Item {i+1} Quantity", allow_zero=False)
                if not qty_valid:
                    validations.append((False, qty_msg))
                else:
                    items.append({'material_id': mid, 'quantity': qty_val})
                    has_valid_item = True
            elif mid and not qty_text:
                validations.append((False, f"Item {i+1}: Quantity is required."))
            elif not mid and qty_text:
                validations.append((False, f"Item {i+1}: Please select a material."))

        if not has_valid_item:
            validations.append((False, "Add at least one item with a valid quantity."))

        all_valid, error_msg = collect_errors(validations)
        if not all_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
        
        # Find supplier for PI - use the material's supplier if available
        mat = InventoryService.get_material_details(items[0]['material_id'])
        if mat.supplier:
            sid = mat.supplier.id
        else:
            from database.models import Supplier
            first_supplier = Supplier.select().first()
            if not first_supplier:
                QMessageBox.warning(self, "Error", "No suppliers registered. Please add a supplier first.")
                return
            sid = first_supplier.id
        
        ProcurementService.create_pi(self.user.id, items, reason, sid)
        QMessageBox.information(self, "PI Raised", "Purchase Indent submitted for Admin approval.")
        relay.data_changed.emit()
        self.load_data()
        if self.inward_tab_widget:
            self.tabs.setCurrentWidget(self.inward_tab_widget)
