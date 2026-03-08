from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QComboBox, QFrame, QScrollArea, QTabWidget, QMessageBox, QGridLayout, QDateEdit)
from PySide6.QtCore import Qt, QDate
from services.mrs_service import MRSService
from services.inventory_service import InventoryService
from services.communication_service import relay
from services.validators import validate_required, validate_batch_id, validate_gst, validate_positive_float, collect_errors
from database.models import Consumer
from ui.mrs_issue_dialog import MRSIssueDialog
from ui.components.status_badge import StatusBadge

class MRSWorkflowView(QWidget):
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setup_ui()
        self.load_data()
        
        # Connect to reactivity system
        relay.data_changed.connect(self.refresh_consumers)
        relay.data_changed.connect(self.load_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        title_container = QVBoxLayout()
        title = QLabel("Invoices")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Generate sales invoices and manage billing history.")
        subtitle.setObjectName("SubtitleLabel")
        title_container.addWidget(title)
        title_container.addWidget(subtitle)
        layout.addLayout(title_container)
        
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
        
        # Tab 1: Create Invoice
        if self.user.role in ['SUPERVISOR', 'ADMIN']:
            self.tabs.addTab(self.create_new_request_tab(), "Create Invoice")
            
        # Tab 2: Invoice History
        self.invoice_tab = self.create_invoice_history_tab()
        self.tabs.addTab(self.invoice_tab, "Invoice History")
        
        layout.addWidget(self.tabs)

    def create_new_request_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        
        from ui.components.card_widget import CardWidget
        form_card = CardWidget()
        form_layout = form_card.layout
        
        grid = QGridLayout()
        grid.setSpacing(10)
        grid.setContentsMargins(0, 0, 0, 0)
        
        lbl_style = "font-weight: 700; font-size: 10px; color: #64748b; letter-spacing: 0.5px;"
        
        # New: Invoice Type Selection
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Existing Consumer", "New User / Manual Entry"])
        self.type_combo.setMinimumHeight(36)
        self.type_combo.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        self.type_combo.currentIndexChanged.connect(self.on_invoice_type_changed)
        
        self.consumer_combo = QComboBox()
        self.consumer_combo.setPlaceholderText("Select Consumer")
        self.consumer_combo.setMinimumHeight(36)
        self.consumer_combo.setStyleSheet("border: 1.5px solid #8B5E3C; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        self.consumer_combo.currentIndexChanged.connect(self.on_consumer_selected)

        # Row 0: Invoice Type
        type_lbl = QLabel("INVOICE FOR")
        type_lbl.setStyleSheet(lbl_style)
        grid.addWidget(type_lbl, 0, 0)
        grid.addWidget(self.type_combo, 0, 1)
        grid.addWidget(self.consumer_combo, 0, 2, 1, 2)
        
        # Load Consumers initially
        self.refresh_consumers()
        
        # Batch ID
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("e.g. BATCH-2026-001")
        self.batch_input.setMinimumHeight(36)
        self.batch_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")
        
        # Recipient Name
        self.client_input = QLineEdit()
        self.client_input.setPlaceholderText("Enter client or department name")
        self.client_input.setMinimumHeight(36)
        self.client_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")
        
        # Row 1: Batch & Client
        batch_lbl = QLabel("BATCH ID")
        batch_lbl.setStyleSheet(lbl_style)
        grid.addWidget(batch_lbl, 1, 0)
        grid.addWidget(self.batch_input, 1, 1)
        
        client_lbl = QLabel("CUSTOMER")
        client_lbl.setStyleSheet(lbl_style)
        grid.addWidget(client_lbl, 1, 2)
        grid.addWidget(self.client_input, 1, 3)
        
        # New: Address
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Enter client address")
        self.address_input.setMinimumHeight(36)
        self.address_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")

        # New: GSTIN
        self.gstin_input = QLineEdit()
        self.gstin_input.setPlaceholderText("e.g. 33AAAAA0000A1Z5")
        self.gstin_input.setMinimumHeight(36)
        self.gstin_input.setMaxLength(15)
        self.gstin_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")
        # Auto-uppercase GSTIN input
        self.gstin_input.textChanged.connect(
            lambda text: self.gstin_input.setText(text.upper()) if text != text.upper() else None
        )

        # Row 2: Address & GSTIN
        addr_lbl = QLabel("ADDRESS")
        addr_lbl.setStyleSheet(lbl_style)
        grid.addWidget(addr_lbl, 2, 0)
        grid.addWidget(self.address_input, 2, 1)
        
        gstin_lbl = QLabel("GSTIN")
        gstin_lbl.setStyleSheet(lbl_style)
        grid.addWidget(gstin_lbl, 2, 2)
        grid.addWidget(self.gstin_input, 2, 3)
        
        # Row 3: Due Date
        self.due_date_input = QDateEdit()
        self.due_date_input.setCalendarPopup(True)
        self.due_date_input.setDate(QDate.currentDate().addDays(14))
        self.due_date_input.setMinimumHeight(36)
        self.due_date_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white;")

        # Row 3: Due Date
        due_lbl = QLabel("DUE DATE")
        due_lbl.setStyleSheet(lbl_style)
        grid.addWidget(due_lbl, 3, 0)
        grid.addWidget(self.due_date_input, 3, 1)
        
        form_layout.addLayout(grid)
        form_layout.addSpacing(10)
        
        # Items Section
        items_header = QHBoxLayout()
        items_label = QLabel("INVOICE ITEMS")
        items_label.setStyleSheet("font-weight: 700; font-size: 11px; color: #94a3b8; letter-spacing: 0.5px;")
        self.btn_add_item = QPushButton("+ Add Item")
        self.btn_add_item.setStyleSheet("color: #8B5E3C; background: rgba(139, 94, 60, 0.1); border: none; padding: 6px 14px; border-radius: 14px; font-weight: 700;")
        self.btn_add_item.clicked.connect(self.add_item_row)
        items_header.addWidget(items_label)
        items_header.addStretch()
        items_header.addWidget(self.btn_add_item)
        form_layout.addLayout(items_header)
        
        self.items_scroll = QScrollArea()
        self.items_scroll.setWidgetResizable(True)
        self.items_scroll.setStyleSheet("background: transparent; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px;")
        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setAlignment(Qt.AlignTop)
        self.items_layout.setSpacing(10)
        self.items_scroll.setWidget(self.items_container)
        form_layout.addWidget(self.items_scroll)
        
        self.rows = []
        self.add_item_row() # Initial row
        
        # Submit Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_submit_invoice = QPushButton("Generate Invoice")
        self.btn_submit_invoice.setStyleSheet("""
            QPushButton {
                background-color: #8B5E3C;
                color: white;
                border: none;
                padding: 10px 30px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #734D31;
            }
        """)
        self.btn_submit_invoice.setFixedWidth(240)
        self.btn_submit_invoice.clicked.connect(lambda: self.submit_request(generate_invoice=True))
        
        button_layout.addWidget(self.btn_submit_invoice)
        form_layout.addLayout(button_layout)
        
        layout.addWidget(form_card)
        return tab

    def refresh_consumers(self):
        self.consumer_combo.clear()
        self.consumer_combo.addItem("Select a Consumer...", None)
        consumers = Consumer.select().order_by(Consumer.company_name)
        for c in consumers:
            self.consumer_combo.addItem(c.company_name, c)

    def on_invoice_type_changed(self, index):
        is_existing = (index == 0)
        self.consumer_combo.setVisible(is_existing)
        
        # If new user, clear and enable everything
        if not is_existing:
            self.client_input.clear()
            self.client_input.setReadOnly(False)
            self.client_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
            
            self.address_input.clear()
            self.address_input.setReadOnly(False)
            self.address_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
            
            self.gstin_input.clear()
            self.gstin_input.setReadOnly(False)
            self.gstin_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        else:
            # Re-trigger selection logic to populate if something is already selected
            self.on_consumer_selected(self.consumer_combo.currentIndex())

    def on_consumer_selected(self, index):
        if self.type_combo.currentIndex() != 0:
            return
            
        consumer = self.consumer_combo.currentData()
        readonly_style = "border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: #f1f5f9; color: #475569;"
        editable_style = "border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;"

        if consumer:
            self.client_input.setText(consumer.company_name)
            self.client_input.setReadOnly(True)
            self.client_input.setStyleSheet(readonly_style)
            
            self.address_input.setText(consumer.location or "")
            self.address_input.setReadOnly(True)
            self.address_input.setStyleSheet(readonly_style)
            
            self.gstin_input.setText(consumer.gst_no or "")
            self.gstin_input.setReadOnly(True)
            self.gstin_input.setStyleSheet(readonly_style)
            
            from PySide6.QtCore import QDate
            self.due_date_input.setDate(QDate.currentDate().addDays(14))
        else:
            self.client_input.clear()
            self.client_input.setReadOnly(False)
            self.client_input.setStyleSheet(editable_style)
            
            self.address_input.clear()
            self.address_input.setReadOnly(False)
            self.address_input.setStyleSheet(editable_style)
            
            self.gstin_input.clear()
            self.gstin_input.setReadOnly(False)
            self.gstin_input.setStyleSheet(editable_style)
            
            from PySide6.QtCore import QDate
            self.due_date_input.setDate(QDate.currentDate().addDays(14))

    def add_item_row(self):
        row = QFrame()
        row.setStyleSheet("background: #F8FAFC; border-radius: 8px; border: 1px solid #E5E7EB;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 12, 12, 12)
        
        combo = QComboBox()
        combo.setPlaceholderText("Select Material")
        combo.setMinimumHeight(36)
        combo.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        materials = InventoryService.get_all_materials()
        for m in materials:
            combo.addItem(f"{m.name} (Available: {m.quantity} {m.unit})", m.id)
            
        qty_input = QLineEdit()
        qty_input.setPlaceholderText("Qty")
        qty_input.setFixedWidth(100)
        qty_input.setMinimumHeight(36)
        qty_input.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 8px; padding: 0 12px; background: white; color: #000000;")
        
        from PySide6.QtGui import QDoubleValidator
        validator = QDoubleValidator(0.0, 1000000.0, 3)
        validator.setNotation(QDoubleValidator.StandardNotation)
        qty_input.setValidator(validator)
        
        btn_remove = QPushButton("✕")
        btn_remove.setStyleSheet("color: #EF4444; background: transparent; font-weight: 800; border: none;")
        btn_remove.clicked.connect(lambda: self.remove_row(row))
        
        row_layout.addWidget(combo, 3)
        row_layout.addWidget(qty_input, 1)
        row_layout.addWidget(btn_remove)
        
        self.items_layout.addWidget(row)
        self.rows.append({'row': row, 'combo': combo, 'qty': qty_input})

    def remove_row(self, row_widget):
        row_widget.deleteLater()
        self.rows = [r for r in self.rows if r['row'] != row_widget]

    def create_invoice_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Search bar for invoice history
        search_layout = QHBoxLayout()
        self.invoice_search = QLineEdit()
        self.invoice_search.setPlaceholderText("Search by invoice #, batch ID, or client name...")
        self.invoice_search.setMinimumHeight(36)
        self.invoice_search.textChanged.connect(self.filter_invoices)
        search_layout.addWidget(self.invoice_search)
        layout.addLayout(search_layout)
        
        self.invoice_table = QTableWidget()
        headers = ["Invoice #", "Batch Ref", "Date", "Total Amount", "Status", "Due Date", "Days Overdue", "Action"]
        self.invoice_table.setColumnCount(len(headers))
        self.invoice_table.setHorizontalHeaderLabels(headers)
        self.invoice_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.invoice_table.verticalHeader().setVisible(False)
        self.invoice_table.verticalHeader().setDefaultSectionSize(52)
        self.invoice_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.invoice_table.setStyleSheet("QTableWidget { border: none; background: white; gridline-color: #f1f5f9; }")
        
        layout.addWidget(self.invoice_table)
        return tab

    def load_invoice_history(self):
        from services.invoice_service import InvoiceService
        self.all_invoices = list(InvoiceService.get_all_invoices())
        self.display_invoices(self.all_invoices)

    def filter_invoices(self):
        term = self.invoice_search.text().lower()
        filtered = [inv for inv in self.all_invoices if
                    term in inv.invoice_no.lower() or
                    term in inv.mrs.batch_id.lower() or
                    term in (inv.client_name or '').lower()]
        self.display_invoices(filtered)

    def display_invoices(self, invoices):
        self.invoice_table.setRowCount(len(invoices))
        for i, inv in enumerate(invoices):
            self.invoice_table.setItem(i, 0, QTableWidgetItem(inv.invoice_no))
            self.invoice_table.setItem(i, 1, QTableWidgetItem(inv.mrs.batch_id))
            self.invoice_table.setItem(i, 2, QTableWidgetItem(inv.created_at.strftime("%Y-%m-%d")))
            self.invoice_table.setItem(i, 3, QTableWidgetItem(f"₹{inv.grand_total:.2f}"))
            
            # Status & Overdue Logic
            status = inv.status.upper()
            from datetime import date
            today = date.today()
            is_overdue = False
            days_overdue = 0
            if status != "PAID" and inv.due_date:
                if today > inv.due_date:
                    is_overdue = True
                    days_overdue = (today - inv.due_date).days
            
            # Status Badge
            from ui.components.status_badge import StatusBadge
            if is_overdue:
                badge = StatusBadge("OVERDUE", "critical")
            else:
                badge_type = "neutral"
                if status == "PAID": badge_type = "success"
                elif status == "DRAFT": badge_type = "warning"
                badge = StatusBadge(status, badge_type)
            
            status_widget = QWidget()
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)
            status_layout.addWidget(badge, alignment=Qt.AlignCenter)
            self.invoice_table.setCellWidget(i, 4, status_widget)

            # Due Date
            due_str = inv.due_date.strftime("%Y-%m-%d") if inv.due_date else "N/A"
            self.invoice_table.setItem(i, 5, QTableWidgetItem(due_str))
            
            # Days Overdue
            overdue_text = f"{days_overdue} days" if days_overdue > 0 else "-"
            self.invoice_table.setItem(i, 6, QTableWidgetItem(overdue_text))
            
            # Action Button Container
            widget = QWidget()
            btn_view = QPushButton("View")
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.setFixedSize(80, 32)
            btn_view.setStyleSheet("""
                QPushButton {
                    background-color: #8B5E3C;
                    color: white;
                    border: none;
                    border-radius: 16px;
                    font-size: 11px;
                    font-weight: 700;
                    text-transform: uppercase;
                }
                QPushButton:hover {
                    background-color: #734D31;
                }
            """)
            btn_view.clicked.connect(lambda checked=False, iv=inv: self.open_invoice_dialog(iv))
            
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(btn_view, alignment=Qt.AlignCenter)
            self.invoice_table.setCellWidget(i, 7, widget)

    def show_invoice_dialog(self, mrs, client_name=None, client_address=None, client_gstin=None, due_date=None):
        from services.invoice_service import InvoiceService
        invoice = InvoiceService.get_invoice_by_mrs(mrs.id)
        if not invoice:
            invoice = InvoiceService.create_invoice_from_mrs(mrs.id, client_name=client_name, client_address=client_address, client_gstin=client_gstin, due_date=due_date)
            self.load_invoice_history()
        
        self.open_invoice_dialog(invoice)

    def open_invoice_dialog(self, invoice):
        from ui.invoice_dialog import InvoiceDialog
        dialog = InvoiceDialog(invoice, self)
        dialog.exec()


    def load_data(self):
        # Only load invoice history now
        self.load_invoice_history()

    def handle_action(self, mrs):
        if self.user.role != 'SUPERVISOR':
            dialog = MRSIssueDialog(mrs, self)
            if dialog.exec():
                if dialog.issue_items:
                    MRSService.issue_mrs(mrs.id, self.user.id, dialog.issue_items)
                    self.load_data()
        else:
            # Show details (could expand further)
            msg = QMessageBox()
            msg.setWindowTitle(f"Request {mrs.batch_id}")
            text = f"Status: {mrs.status}\n\nItems:\n"
            for it in mrs.items:
                text += f"- {it.material.name}: {it.quantity_issued}/{it.quantity_requested} {it.material.unit}\n"
            msg.setText(text)
            msg.exec()

    def submit_request(self, generate_invoice=False):
        batch_id = self.batch_input.text().strip()
        client_name = self.client_input.text().strip()
        client_address = self.address_input.text().strip()
        client_gstin = self.gstin_input.text().strip()
        due_date = self.due_date_input.date().toPython()

        # Validate header fields
        validations = [
            validate_batch_id(batch_id),
            validate_required(client_name, "Customer Name"),
            validate_gst(client_gstin),
        ]

        # Validate item rows
        items = []
        has_valid_item = False
        for i, r in enumerate(self.rows):
            mid = r['combo'].currentData()
            qty_text = r['qty'].text().strip()
            if not mid and not qty_text:
                continue  # Skip fully empty rows
            if mid and qty_text:
                qty_valid, qty_msg, qty_val = validate_positive_float(qty_text, f"Item {i+1} Quantity", allow_zero=False)
                if not qty_valid:
                    validations.append((False, qty_msg))
                else:
                    items.append({'material_id': mid, 'quantity_requested': qty_val})
                    has_valid_item = True
            elif mid and not qty_text:
                validations.append((False, f"Item {i+1}: Quantity is required."))
            elif not mid and qty_text:
                validations.append((False, f"Item {i+1}: Please select a material."))

        if not has_valid_item:
            validations.append((False, "Add at least one material with a valid quantity."))

        all_valid, error_msg = collect_errors(validations)
        if not all_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return

        # Check for zero-price items and warn
        zero_price_items = []
        for it in items:
            mat = InventoryService.get_material_details(it['material_id'])
            if mat and mat.unit_cost == 0:
                zero_price_items.append(mat.name)
        
        if zero_price_items:
            names = ", ".join(zero_price_items)
            confirm = QMessageBox.question(
                self, "Zero Price Warning",
                f"The following items have ₹0 unit cost:\n{names}\n\n"
                "The invoice will show ₹0 for these items. Continue anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return
            
        try:
            mrs = MRSService.create_mrs(self.user.id, batch_id, items)
            
            # Automatically ISSUE materials and update stock when invoice is generated
            issue_items = [{'material_id': it['material_id'], 'quantity_issued': it['quantity_requested']} for it in items]
            MRSService.issue_mrs(mrs.id, self.user.id, issue_items)
            
            QMessageBox.information(self, "Success", "Invoice Generated Successfully")
            
            # Clean up form
            self.batch_input.clear()
            self.client_input.clear()
            self.client_input.setEnabled(True)
            self.address_input.clear()
            self.address_input.setEnabled(True)
            self.gstin_input.clear()
            self.gstin_input.setEnabled(True)
            self.type_combo.setCurrentIndex(0)
            self.consumer_combo.setCurrentIndex(0)
            
            for r in self.rows: r['row'].deleteLater()
            self.rows = []
            self.add_item_row()
            
            if generate_invoice:
                self.show_invoice_dialog(mrs, client_name=client_name, client_address=client_address, client_gstin=client_gstin, due_date=due_date)
            
            # Switch to History tab
            self.tabs.setCurrentIndex(1)
            self.load_invoice_history()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create request: {str(e)}")
