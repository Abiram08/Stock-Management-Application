from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFrame)
from PySide6.QtCore import Qt
from database.models import Supplier
from services.communication_service import relay

class SupplierManagementView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()
        
        # Connect to reactivity system
        relay.data_changed.connect(self.load_data)

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(24)
        
        # Header
        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()
        title = QLabel("Supplier & Catalog Management")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Select a supplier to manage their product catalog and performance.")
        subtitle.setObjectName("SubtitleLabel")
        title_container.addWidget(title)
        title_container.addWidget(subtitle)
        header_layout.addLayout(title_container)
        
        header_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search suppliers...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_data)
        header_layout.addWidget(self.search_input)
        
        self.btn_register = QPushButton("+ Register New Supplier")
        self.btn_register.setProperty("class", "PrimaryButton")
        self.btn_register.clicked.connect(self.show_register_supplier)
        header_layout.addWidget(self.btn_register)
        self.main_layout.addLayout(header_layout)

        # Splitter for Master-Detail
        from PySide6.QtWidgets import QSplitter
        self.splitter = QSplitter(Qt.Vertical)
        
        # Master: Supplier List
        self.master_card = QFrame()
        self.master_card.setObjectName("Card")
        self.master_card.setProperty("class", "Card")
        self.master_card.setStyleSheet("#Card { background-color: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 16px; }")
        master_layout = QVBoxLayout(self.master_card)
        
        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(7)
        self.supplier_table.setHorizontalHeaderLabels(["S.No", "Company Name", "Contact Person", "Mobile", "GST No", "Products", "Actions"])
        
        header = self.supplier_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        
        self.supplier_table.setColumnWidth(0, 50)
        self.supplier_table.setColumnWidth(6, 120)
        self.supplier_table.verticalHeader().setVisible(False)
        self.supplier_table.verticalHeader().setDefaultSectionSize(52)
        self.supplier_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.supplier_table.setSelectionMode(QTableWidget.SingleSelection)
        self.supplier_table.setShowGrid(False)
        self.supplier_table.setAlternatingRowColors(True)
        self.supplier_table.itemSelectionChanged.connect(self.on_supplier_selected)
        master_layout.addWidget(self.supplier_table)
        
        # Detail: Product Catalog
        from ui.components.card_widget import CardWidget
        self.detail_card = CardWidget()
        self.detail_card.layout.setContentsMargins(20, 20, 20, 20)
        
        detail_header = QHBoxLayout()
        self.detail_title = QLabel("PRODUCT CATALOG")
        self.detail_title.setStyleSheet("font-weight: 800; font-size: 13px; color: #1E293B;")
        detail_header.addWidget(self.detail_title)
        detail_header.addStretch()
        
        self.btn_add_product = QPushButton("+ Add Product")
        self.btn_add_product.setProperty("class", "SecondaryButton")
        self.btn_add_product.clicked.connect(self.show_add_product)
        self.btn_add_product.setEnabled(False)
        detail_header.addWidget(self.btn_add_product)
        self.detail_card.layout.addLayout(detail_header)
        
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(6)
        self.product_table.setHorizontalHeaderLabels(["S.No", "Name", "Unit", "Cost", "Stock", "Actions"])
        
        header = self.product_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Name
        header.setSectionResizeMode(5, QHeaderView.Fixed) # Actions
        
        self.product_table.setColumnWidth(0, 50)
        self.product_table.setColumnWidth(5, 180) # Increased width
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.verticalHeader().setDefaultSectionSize(52)
        self.product_table.setShowGrid(False)
        self.product_table.setAlternatingRowColors(True)
        self.detail_card.layout.addWidget(self.product_table)
        
        self.splitter.addWidget(self.master_card)
        self.splitter.addWidget(self.detail_card)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        
        self.main_layout.addWidget(self.splitter)

    def load_data(self):
        from database.models import Material
        suppliers = Supplier.select()
        self.all_suppliers = list(suppliers)
        self.display_suppliers(self.all_suppliers)

    def filter_data(self):
        term = self.search_input.text().lower()
        filtered = [s for s in self.all_suppliers if 
                    term in s.name.lower() or 
                    term in (s.contact_person or '').lower() or 
                    term in (s.gst_no or '').lower()]
        self.display_suppliers(filtered)

    def display_suppliers(self, suppliers):
        from database.models import Material
        self.supplier_table.setRowCount(len(suppliers))
        self.supplier_data = list(suppliers) # Keep for reference
        for i, s in enumerate(suppliers):
            # 0. S.No
            sno_item = QTableWidgetItem(str(i + 1))
            sno_item.setTextAlignment(Qt.AlignCenter)
            self.supplier_table.setItem(i, 0, sno_item)

            self.supplier_table.setItem(i, 1, QTableWidgetItem(s.name))
            self.supplier_table.setItem(i, 2, QTableWidgetItem(s.contact_person))
            self.supplier_table.setItem(i, 3, QTableWidgetItem(s.phone))
            self.supplier_table.setItem(i, 4, QTableWidgetItem(s.gst_no or "N/A"))
            
            # Count products
            product_count = Material.select().where(Material.supplier == s).count()
            count_item = QTableWidgetItem(str(product_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.supplier_table.setItem(i, 5, count_item)

            # Actions Cell
            btn_edit = QPushButton("✎")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setToolTip("Edit Supplier Details")
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
            btn_edit.clicked.connect(lambda checked=False, supplier=s: self.show_edit_supplier(supplier))

            btn_del = QPushButton("✕")
            btn_del.setFixedSize(32, 32)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setToolTip("Delete Supplier")
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
            btn_del.clicked.connect(lambda checked=False, supplier=s: self.confirm_delete_supplier(supplier))

            action_container = QWidget()
            action_layout = QHBoxLayout(action_container)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setAlignment(Qt.AlignCenter)
            action_layout.addWidget(btn_edit)
            action_layout.addWidget(btn_del)
            self.supplier_table.setCellWidget(i, 6, action_container)

    def on_supplier_selected(self):
        rows = self.supplier_table.selectionModel().selectedRows()
        if not rows:
            self.btn_add_product.setEnabled(False)
            self.product_table.setRowCount(0)
            self.detail_title.setText("SELECT A SUPPLIER")
            return
            
        index = rows[0].row()
        self.current_supplier = self.supplier_data[index]
        self.btn_add_product.setEnabled(True)
        self.detail_title.setText(f"CATALOG: {self.current_supplier.name.upper()}")
        self.load_products()

    def load_products(self):
        from database.models import Material
        products = Material.select().where(Material.supplier == self.current_supplier)
        self.product_table.setRowCount(len(products))
        for i, p in enumerate(products):
            # 0. S.No
            sno_item = QTableWidgetItem(str(i + 1))
            sno_item.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(i, 0, sno_item)

            # 1. Name
            name_item = QTableWidgetItem(p.name)
            self.product_table.setItem(i, 1, name_item)
            
            # 2. Unit
            unit_item = QTableWidgetItem(p.unit)
            unit_item.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(i, 2, unit_item)
            
            # 3. Cost
            cost_item = QTableWidgetItem(f"₹{p.unit_cost}")
            cost_item.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(i, 3, cost_item)
            
            # 4. Stock
            stock_item = QTableWidgetItem(str(p.quantity))
            stock_item.setTextAlignment(Qt.AlignCenter)
            self.product_table.setItem(i, 4, stock_item)
            
            # 5. Actions
            btn_edit = QPushButton("✎")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setToolTip("Edit Product")
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
            btn_edit.clicked.connect(lambda checked=False, mat=p: self.show_edit_product(mat))

            btn_del = QPushButton("✕")
            btn_del.setFixedSize(32, 32)
            btn_del.setCursor(Qt.PointingHandCursor)
            btn_del.setToolTip("Remove from Catalog")
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
            btn_del.clicked.connect(lambda checked=False, mid=p.id: self.confirm_delete_product(mid))

            cell_widget = QWidget()
            cell_layout = QHBoxLayout(cell_widget)
            cell_layout.setContentsMargins(0, 0, 0, 0)
            cell_layout.setSpacing(10)
            cell_layout.addStretch() # Push to center
            cell_layout.addWidget(btn_edit)
            cell_layout.addWidget(btn_del)
            cell_layout.addStretch() # Push to center
            self.product_table.setCellWidget(i, 5, cell_widget)

    def show_register_supplier(self):
        from ui.supplier_form_dialog import SupplierFormDialog
        dialog = SupplierFormDialog(parent=self)
        if dialog.exec():
            self.load_data()

    def show_edit_supplier(self, supplier):
        from ui.supplier_form_dialog import SupplierFormDialog
        dialog = SupplierFormDialog(supplier=supplier, parent=self)
        if dialog.exec():
            self.load_data()

    def confirm_delete_supplier(self, supplier):
        from PySide6.QtWidgets import QMessageBox
        from database.models import Material
        
        # Check if supplier has products
        product_count = Material.select().where(Material.supplier == supplier).count()
        
        if product_count > 0:
            QMessageBox.critical(self, "Cannot Delete", 
                               f"This supplier has {product_count} products in your catalog.\n"
                               "Please remove all products from their catalog before deleting the supplier.")
            return

        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete supplier '{supplier.name}'?\n"
                                   "This action cannot be undone.",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                supplier.delete_instance()
                self.load_data()
                QMessageBox.information(self, "Success", f"Supplier '{supplier.name}' deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete supplier: {str(e)}")

    def show_add_product(self):
        from ui.material_form_dialog import MaterialFormDialog
        # Pass current supplier to pre-fill
        dialog = MaterialFormDialog(parent=self)
        # Pre-select supplier in the dialog
        index = dialog.supplier_input.findData(self.current_supplier.id)
        if index >= 0:
            dialog.supplier_input.setCurrentIndex(index)
            dialog.supplier_input.setEnabled(False) # Lock it for this flow
            
        if dialog.exec():
            self.load_products()

    def show_edit_product(self, material):
        from ui.material_form_dialog import MaterialFormDialog
        dialog = MaterialFormDialog(material=material, parent=self)
        if dialog.exec():
            self.load_products()

    def confirm_delete_product(self, material_id):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   "Delete this product from catalog and inventory?",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            from services.inventory_service import InventoryService
            InventoryService.delete_material(material_id)
            self.load_products()
