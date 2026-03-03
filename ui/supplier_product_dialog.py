from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFormLayout, QComboBox, QMessageBox)
from PySide6.QtCore import Qt
from database.models import Material, Supplier, db
from services.inventory_service import InventoryService
from services.communication_service import relay
from services.validators import validate_required, validate_positive_float, collect_errors
from ui.components.card_widget import CardWidget

class SupplierProductDialog(QDialog):
    def __init__(self, supplier_id, parent=None):
        super().__init__(parent)
        self.supplier = Supplier.get_by_id(supplier_id)
        self.setWindowTitle(f"Manage Products - {self.supplier.name}")
        self.resize(700, 500)
        
        # Load Styles
        with open("ui/styles.qss", "r") as f:
            self.setStyleSheet(f.read())
            
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        # Header
        header = QLabel(f"Products from {self.supplier.name}")
        header.setObjectName("TitleLabel")
        self.main_layout.addWidget(header)

        # Add Product Form (Collapsed in a Card)
        self.form_card = CardWidget()
        form_layout = QFormLayout(self.form_card)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")
        
        self.unit_input = QComboBox()
        self.unit_input.addItems(["kg", "ltr", "pcs", "mtr", "bag"])
        
        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("Unit Cost (₹) e.g. 150.00")
        
        self.stock_available_input = QLineEdit()
        self.stock_available_input.setPlaceholderText("Current Stock Available")
        self.stock_available_input.setText("0")

        self.category_input = QComboBox()
        self.category_input.addItems([
            "Reactive Dye (Cotton)", 
            "Disperse Dye (Polyester)", 
            "Acid Dye (Wool/Silk)", 
            "Direct Dye (Cellulose)", 
            "Vat Dye (Indigo)",
            "Other Chemicals",
            "Auxiliaries"
        ])

        self.btn_add = QPushButton("Add Product to Inventory")
        self.btn_add.setProperty("class", "PrimaryButton")
        self.btn_add.clicked.connect(self.add_product)

        form_layout.addRow("Name *:", self.name_input)
        form_layout.addRow("Category:", self.category_input)
        form_layout.addRow("Unit:", self.unit_input)
        form_layout.addRow("Unit Cost *:", self.cost_input)
        form_layout.addRow("Stock Available:", self.stock_available_input)
        form_layout.addRow("", self.btn_add)
        
        self.main_layout.addWidget(self.form_card)

        # Product Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Unit", "Cost", "Stock"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.main_layout.addWidget(self.table)

    def load_products(self):
        products = Material.select().where(Material.supplier == self.supplier)
        self.table.setRowCount(len(products))
        for i, p in enumerate(products):
            self.table.setItem(i, 0, QTableWidgetItem(p.name))
            self.table.setItem(i, 1, QTableWidgetItem(p.unit))
            self.table.setItem(i, 2, QTableWidgetItem(f"₹{p.unit_cost}"))
            self.table.setItem(i, 3, QTableWidgetItem(str(p.quantity)))

    def add_product(self):
        name = self.name_input.text().strip()

        # Validate numeric fields
        cost_valid, cost_msg, cost_val = validate_positive_float(
            self.cost_input.text(), "Unit Cost")
        stock_valid, stock_msg, stock_val = validate_positive_float(
            self.stock_available_input.text(), "Stock Available")

        all_valid, error_msg = collect_errors([
            validate_required(name, "Product Name"),
            (cost_valid, cost_msg),
            (stock_valid, stock_msg),
        ])

        if not all_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
            
        try:
            data = {
                'name': name,
                'unit': self.unit_input.currentText(),
                'unit_cost': cost_val,
                'quantity': stock_val, # Maps to physical stock
                'min_stock': 10.0, # Default min stock for safety
                'supplier': self.supplier,
                'category': self.category_input.currentText()
            }
            
            InventoryService.create_material(data)
            
            # Clear form and reload
            self.name_input.clear()
            self.cost_input.clear()
            self.stock_available_input.setText("0")
            self.load_products()
            relay.data_changed.emit()
            QMessageBox.information(self, "Success", "Product added and visible in Inventory")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
