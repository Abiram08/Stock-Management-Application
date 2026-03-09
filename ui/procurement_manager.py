from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QComboBox, QFrame, QScrollArea, QTabWidget, QMessageBox, QTextEdit, QDialog)
from PySide6.QtCore import Qt
from services.procurement_service import ProcurementService
from services.inventory_service import InventoryService
from services.validators import validate_required, validate_positive_float, collect_errors
from ui.components.status_badge import StatusBadge
from services.communication_service import relay

class PIDialog(QDialog):
    def __init__(self, pi, parent=None, is_review=True):
        super().__init__(parent)
        self.pi = pi
        self.is_review = is_review
        self.setWindowTitle(f"Purchase Indent: {pi.reason if pi.reason else 'No Title'}")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header Details
        header = QVBoxLayout()
        header.setSpacing(6)
        
        lbl_supp = QLabel(f"Supplier: {self.pi.supplier.name}")
        lbl_supp.setStyleSheet("font-weight: 800; color: #1e293b; font-size: 14px;")
        
        lbl_reason = QLabel(f"Reason: {self.pi.reason}")
        lbl_reason.setStyleSheet("color: #475569; font-size: 13px;")
        
        lbl_raised = QLabel(f"Raised By: {self.pi.store_manager.username if self.pi.store_manager else 'System'}")
        lbl_raised.setStyleSheet("color: #64748b; font-size: 11px;")
        
        header.addWidget(lbl_supp)
        header.addWidget(lbl_reason)
        header.addWidget(lbl_raised)
        layout.addLayout(header)

        # Items Preview
        lbl_items = QLabel("ORDERED MATERIALS")
        lbl_items.setStyleSheet("font-size: 10px; font-weight: 800; color: #94a3b8; letter-spacing: 0.5px; margin-top: 10px;")
        layout.addWidget(lbl_items)
        
        items_frame = QFrame()
        items_frame.setStyleSheet("background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;")
        items_layout = QVBoxLayout(items_frame)
        
        for item in self.pi.items:
            row = QHBoxLayout()
            name = QLabel(item.material.name)
            name.setStyleSheet("color: #1e293b; font-weight: 600;")
            
            qty = QLabel(f"{item.quantity} {item.material.unit}")
            qty.setStyleSheet("color: #1e293b; background: #e2e8f0; padding: 2px 8px; border-radius: 4px; font-weight: 700;")
            
            row.addWidget(name)
            row.addStretch()
            row.addWidget(qty)
            items_layout.addLayout(row)
        layout.addWidget(items_frame)

        if self.is_review:
            lbl_rem = QLabel("Admin Remarks / Approval Notes:")
            lbl_rem.setStyleSheet("font-weight: 700; color: #1e293b; margin-top: 10px;")
            layout.addWidget(lbl_rem)
            
            self.remarks = QTextEdit()
            self.remarks.setPlaceholderText("Add approval/rejection notes...")
            self.remarks.setStyleSheet("color: #000000; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px;")
            self.remarks.setFixedHeight(60)
            layout.addWidget(self.remarks)

            btn_box = QHBoxLayout()
            btn_reject = QPushButton("Reject Order")
            btn_reject.setCursor(Qt.PointingHandCursor)
            btn_reject.setStyleSheet("background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; padding: 12px; border-radius: 6px; font-weight: bold;")
            btn_reject.clicked.connect(lambda: self.done_with_status('REJECTED'))
            
            btn_approve = QPushButton("Approve & Procure")
            btn_approve.setCursor(Qt.PointingHandCursor)
            btn_approve.setStyleSheet("background: #000000; color: white; padding: 12px; border-radius: 6px; font-weight: bold;")
            btn_approve.clicked.connect(lambda: self.done_with_status('APPROVED'))
            
            btn_box.addWidget(btn_reject)
            btn_box.addWidget(btn_approve)
            layout.addLayout(btn_box)
        else:
            # Inward Confirmation View
            lbl_confirm = QLabel("Confirm that all ordered quantities have safely arrived at the warehouse.")
            lbl_confirm.setStyleSheet("color: #475569; font-style: italic; font-size: 12px; margin-top: 10px;")
            lbl_confirm.setWordWrap(True)
            layout.addWidget(lbl_confirm)

            btn_box = QHBoxLayout()
            btn_reject = QPushButton("Reject Shipment")
            btn_reject.setStyleSheet("background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; padding: 10px; border-radius: 6px; font-weight: bold;")
            btn_reject.clicked.connect(lambda: self.done_with_status('REJECTED'))
            
            btn_done = QPushButton("Yes, Stock Inwarded")
            btn_done.setStyleSheet("background: #000000; color: white; padding: 12px; border-radius: 6px; font-weight: bold;")
            btn_done.clicked.connect(lambda: self.done_with_status('COMPLETED'))
            
            btn_box.addWidget(btn_reject)
            btn_box.addWidget(btn_done)
            layout.addLayout(btn_box)

    def done_with_status(self, status):
        self.selected_status = status
        self.approval_remarks = self.remarks.toPlainText().strip() if hasattr(self, 'remarks') else "Inward Action"
        self.accept()

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
        self.pi_reason.setPlaceholderText("e.g. Monthly Restock Required for Batch-7...")
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
        rec_layout = rec_card.layout
        
        rec_title = QLabel("PROCUREMENT INTELLIGENCE")
        rec_title.setStyleSheet("font-weight: 800; font-size: 11px; color: #1E293B; letter-spacing: 1.5px;")
        rec_layout.addWidget(rec_title)
        
        self.rec_info = QLabel("Analyzing Stock Health...")
        self.rec_info.setStyleSheet("font-size: 13px; color: #475569; margin-top: 10px; font-weight: 500; line-height: 1.4;")
        self.rec_info.setWordWrap(True)
        rec_layout.addWidget(self.rec_info)

        purpose_label = QLabel("Purpose: Identifying materials below safety thresholds to prevent production delays.")
        purpose_label.setStyleSheet("font-size: 11px; color: #64748b; font-style: italic;")
        purpose_label.setWordWrap(True)
        rec_layout.addWidget(purpose_label)
        
        btn_autofill = QPushButton("Auto-Fill Recommendations")
        btn_autofill.setStyleSheet("background: #000000; color: white; font-weight: 700; padding: 12px; border-radius: 8px; border: none; margin-top: 20px;")
        btn_autofill.clicked.connect(self.autofill_recommended)
        
        rec_layout.addStretch()
        rec_layout.addWidget(btn_autofill)
        layout.addWidget(rec_card, 1)
        
        return tab

    def add_pi_row(self, material_id=None, qty=0):
        row = QFrame()
        row_layout = QHBoxLayout(row)
        
        combo = QComboBox()
        combo.setStyleSheet("color: black; background: white; border: 1px solid #e2e8f0; padding: 4px;")
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
        
        for r in self.pi_rows: r['row'].deleteLater()
        self.pi_rows = []
        
        for r in recs:
            self.add_pi_row(r['material_id'], r['quantity'])
        self.pi_reason.setText("Replenishing stock for low-quantity chemicals.")

    def create_approvals_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        search_layout = QHBoxLayout()
        self.approval_search = QLineEdit()
        self.approval_search.setPlaceholderText("Search by PI Code or Requester...")
        self.approval_search.setMinimumHeight(36)
        self.approval_search.textChanged.connect(self.filter_approvals)
        
        self.approval_filter = QComboBox()
        self.approval_filter.addItems(["All Requests", "Needs Approval", "Approved", "Rejected"])
        self.approval_filter.setFixedWidth(160)
        self.approval_filter.setMinimumHeight(36)
        self.approval_filter.currentIndexChanged.connect(self.filter_approvals)
        
        search_layout.addWidget(self.approval_search, 1)
        search_layout.addWidget(self.approval_filter)
        layout.addLayout(search_layout)

        self.approval_table = QTableWidget()
        self.approval_table.setColumnCount(6)
        self.approval_table.setHorizontalHeaderLabels(["S.No", "PI Code", "Raised By", "Date", "Status", "Action"])
        
        header = self.approval_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.approval_table.setColumnWidth(0, 50)
        self.approval_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.approval_table)
        return tab

    def create_inward_tab(self):
        tab = QWidget()
        search_layout = QHBoxLayout()
        self.inward_search = QLineEdit()
        self.inward_search.setPlaceholderText("Search by Order # or Supplier...")
        self.inward_search.setMinimumHeight(36)
        self.inward_search.textChanged.connect(self.filter_inward)
        
        self.inward_filter = QComboBox()
        self.inward_filter.addItems(["All Records", "Pending Delivery", "Received / Done", "Rejected"])
        self.inward_filter.setFixedWidth(180)
        self.inward_filter.setMinimumHeight(36)
        self.inward_filter.currentIndexChanged.connect(self.filter_inward)
        
        search_layout.addWidget(self.inward_search, 1)
        search_layout.addWidget(self.inward_filter)
        layout.addLayout(search_layout)

        self.inward_table = QTableWidget()
        self.inward_table.setColumnCount(6)
        self.inward_table.setHorizontalHeaderLabels(["S.No", "Order #", "Supplier", "Date", "Workflow Status", "Action"])
        
        header = self.inward_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.inward_table.setColumnWidth(0, 50)
        self.inward_table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.inward_table)
        return tab

    def load_data(self):
        pis = ProcurementService.get_all_pis()
        self.refresh_approvals(pis)
        self.refresh_inward(pis)
        
        if self.has_raise_tab and hasattr(self, 'rec_info'):
            recs = ProcurementService.get_recommendations()
            if recs:
                self.rec_info.setText(f"Low Stock Alert: {len(recs)} items below limit.")
                self.rec_info.setStyleSheet("color: #B45309; font-weight: 600;")
            else:
                self.rec_info.setText("Stock levels healthy.")
                self.rec_info.setStyleSheet("color: #15803D; font-weight: 600;")

    def refresh_approvals(self, pis):
        if self.user.role != 'ADMIN': return
        self.approval_records_all = pis
        self.filter_approvals()

    def filter_approvals(self):
        term = self.approval_search.text().lower()
        f_idx = self.approval_filter.currentIndex()
        
        filtered = []
        for p in self.approval_records_all:
            # Search
            match_search = (term in f"PI-{str(p.id).zfill(4)}".lower() or 
                            term in p.created_by.username.lower())
            
            # Status
            match_status = True
            if f_idx == 1: # Needs Approval
                match_status = p.status == 'RAISED'
            elif f_idx == 2: # Approved
                match_status = p.status in ['APPROVED', 'COMPLETED']
            elif f_idx == 3: # Rejected
                match_status = p.status == 'REJECTED'
                
            if match_search and match_status:
                filtered.append(p)
                
        self.display_approvals(filtered)

    def display_approvals(self, records):
        self.approval_table.setRowCount(len(records))
        for i, p in enumerate(records):
            # 0. S.No
            sno_item = QTableWidgetItem(str(i + 1))
            sno_item.setTextAlignment(Qt.AlignCenter)
            self.approval_table.setItem(i, 0, sno_item)

            self.approval_table.setItem(i, 1, QTableWidgetItem(f"PI-{str(p.id).zfill(4)}"))
            self.approval_table.setItem(i, 2, QTableWidgetItem(p.store_manager.username))
            self.approval_table.setItem(i, 3, QTableWidgetItem(p.created_at.strftime("%Y-%m-%d")))
            self.approval_table.setCellWidget(i, 4, StatusBadge(p.status, 'warning'))
            
            # Action buttons row
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)

            btn_edit = QPushButton("✎ Edit")
            btn_edit.setToolTip("Modify Indent before approval")
            btn_edit.clicked.connect(lambda checked=False, pi=p: self.edit_pi_before_approval(pi))
            btn_edit.setFixedWidth(60)
            
            btn_review = QPushButton("Review & Decide")
            btn_review.setStyleSheet("background: #000000; color: white; border-radius: 4px; padding: 4px 8px;")
            btn_review.clicked.connect(lambda checked=False, pi=p: self.review_pi(pi))
            
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_review)
            self.approval_table.setCellWidget(i, 4, btn_container)

    def edit_pi_before_approval(self, pi):
        # Switch to raise tab and populate
        self.tabs.setCurrentIndex(0)
        self.pi_reason.setText(pi.reason)
        
        # Clear existing rows
        for r in self.pi_rows: r['row'].deleteLater()
        self.pi_rows = []
        
        for item in pi.items:
            self.add_pi_row(item.material.id, item.quantity)
            
        # Optional: Delete the old PI so this becomes the new version
        # ProcurementService.delete_pi(pi.id)
        # relay.data_changed.emit()
        QMessageBox.information(self, "Edit Mode", f"Purchase Indent {pi.id} details loaded into the 'Raise PI' form. You can modify and submit again.")

    def review_pi(self, pi):
        dlg = PIDialog(pi, self, is_review=True)
        if dlg.exec():
            ProcurementService.update_pi_status(pi.id, self.user.id, dlg.selected_status, dlg.approval_remarks)
            self.load_data()

    def refresh_inward(self, pis):
        self.inward_records_all = [p for p in pis if p.status in ['APPROVED', 'COMPLETED', 'REJECTED']]
        self.filter_inward()

    def filter_inward(self):
        term = self.inward_search.text().lower()
        f_idx = self.inward_filter.currentIndex()
        
        filtered = []
        for p in self.inward_records_all:
            # Search
            match_search = term in f"PO-{str(p.id).zfill(4)}".lower() or term in p.supplier.name.lower()
            
            # Label/Status
            match_status = True
            if f_idx == 1: # Pending
                match_status = p.status == 'APPROVED'
            elif f_idx == 2: # Received
                match_status = p.status == 'COMPLETED'
            elif f_idx == 3: # Rejected
                match_status = p.status == 'REJECTED'
                
            if match_search and match_status:
                filtered.append(p)

        self.display_inward(filtered)

    def display_inward(self, records):
        self.inward_table.setRowCount(len(records))
        for i, p in enumerate(records):
            # 0. S.No
            sno_item = QTableWidgetItem(str(i + 1))
            sno_item.setTextAlignment(Qt.AlignCenter)
            self.inward_table.setItem(i, 0, sno_item)

            self.inward_table.setItem(i, 1, QTableWidgetItem(f"PO-{str(p.id).zfill(4)}"))
            self.inward_table.setItem(i, 2, QTableWidgetItem(p.supplier.name))
            self.inward_table.setItem(i, 3, QTableWidgetItem(p.created_at.strftime("%Y-%m-%d")))
            
            status_map = {'APPROVED': ('Pending Delivery', 'warning'), 'COMPLETED': ('Received / Done', 'success'), 'REJECTED': ('Order Rejected', 'critical')}
            lbl, level = status_map.get(p.status, (p.status, 'indigo'))
            self.inward_table.setCellWidget(i, 4, StatusBadge(lbl, level))
            
            # Action container
            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(8)

            # Always show Edit button to allow re-submission or viewing details
            btn_edit = QPushButton("✎ Edit")
            btn_edit.setToolTip("Load this order back into the form to modify")
            btn_edit.clicked.connect(lambda checked=False, pi=p: self.edit_pi_before_approval(pi))
            btn_edit.setFixedWidth(60)
            btn_layout.addWidget(btn_edit)

            if p.status == 'APPROVED':
                btn_confirm = QPushButton("Confirm Receipt")
                btn_confirm.setStyleSheet("background: #000000; color: white; border-radius: 4px; padding: 4px 8px;")
                btn_confirm.clicked.connect(lambda checked=False, pi=p: self.complete_inward(pi))
                btn_layout.addWidget(btn_confirm)
            elif p.status == 'COMPLETED':
                btn_reverse = QPushButton("↺ Reverse/Fix")
                btn_reverse.setStyleSheet("color: #b91c1c; background: transparent; border: 1px solid #fecaca; font-size: 10px; padding: 2px 4px; border-radius: 4px;")
                btn_reverse.clicked.connect(lambda checked=False, pi=p: self.confirm_reverse_inward(pi))
                btn_layout.addWidget(btn_reverse)
            else:
                lbl_status = QLabel("Rejected" if p.status == 'REJECTED' else "Stock Updated")
                lbl_status.setStyleSheet("color: #64748b; font-size: 11px;")
                btn_layout.addWidget(lbl_status)
            
            self.inward_table.setCellWidget(i, 5, btn_container)

    def complete_inward(self, pi):
        dlg = PIDialog(pi, self, is_review=False)
        if dlg.exec():
            status = getattr(dlg, 'selected_status', 'COMPLETED')
            remarks = getattr(dlg, 'approval_remarks', '')

            if status == 'COMPLETED':
                ProcurementService.process_inward(pi.id, self.user.id)
                QMessageBox.information(self, "Inventory Updated", f"Materials from {pi.supplier.name} added to stock.")
            else:
                # Rejected during inward
                ProcurementService.update_pi_status(pi.id, self.user.id, 'REJECTED', f"Rejected at Inward: {remarks}")
                QMessageBox.warning(self, "Order Rejected", "Shipment marked as rejected. No stock updated.")

            self.load_data()
            relay.data_changed.emit()

    def confirm_reverse_inward(self, pi):
        reply = QMessageBox.question(self, "Confirm Reversal", 
                                   f"Reverse inward for order PO-{str(pi.id).zfill(4)}?\n\n"
                                   "This will:\n"
                                   "1. DEDUCT the materials from current inventory.\n"
                                   "2. Put the status back to 'Pending Delivery'.\n\n"
                                   "Use this for correcting wrong entries.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                ProcurementService.reverse_inward(pi.id, self.user.id)
                QMessageBox.information(self, "Success", "Record reversed. Stock deducted.")
                self.load_data()
                relay.data_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not reverse: {str(e)}")

    def submit_pi(self):
        reason = self.pi_reason.toPlainText().strip()
        items = []
        for r in self.pi_rows:
            mid = r['combo'].currentData()
            qty = r['qty'].text().strip()
            if mid and qty:
                items.append({'material_id': mid, 'quantity': float(qty)})
        
        if not reason or not items:
            QMessageBox.warning(self, "Invalid Indent", "Please provide a reason and at least one item.")
            return

        mat = InventoryService.get_material_details(items[0]['material_id'])
        sid = mat.supplier.id if mat.supplier else 1
        ProcurementService.create_pi(self.user.id, items, reason, sid)
        QMessageBox.information(self, "Success", "Purchase Indent raised for approval.")
        self.pi_reason.clear()
        self.load_data()
