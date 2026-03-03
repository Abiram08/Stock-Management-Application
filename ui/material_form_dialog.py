from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QComboBox, QPushButton, QLabel, QMessageBox)
from database.models import Supplier, Material
from services.inventory_service import InventoryService
from services.communication_service import relay
from services.validators import validate_required, validate_positive_float, collect_errors

class MaterialFormDialog(QDialog):
    def __init__(self, material=None, parent=None):
        super().__init__(parent)
        self.material = material
        self.setWindowTitle("Edit Material" if material else "Add New Material")
        self.resize(400, 350)
        
        # Load Styles
        with open("ui/styles.qss", "r") as f:
            self.setStyleSheet(f.read())
            
        self.setup_ui()
        if material:
            self.load_material_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel(self.windowTitle().upper())
        title.setObjectName("TitleLabel")
        title.setStyleSheet("font-size: 18px; margin-bottom: 10px;")
        layout.addWidget(title)
        
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Reactive Red 195")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("SKU / Product Code (optional)")
        
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
        
        self.unit_input = QComboBox()
        self.unit_input.addItems(["kg", "ltr", "pcs", "mtr", "bag"])
        
        self.initial_stock_input = QLineEdit()
        self.initial_stock_input.setPlaceholderText("0.0")
        self.initial_stock_input.setText("0")
        
        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("0.0")
        
        self.min_stock_input = QLineEdit()
        self.min_stock_input.setPlaceholderText("10.0")
        self.min_stock_input.setText("10")
        
        self.supplier_input = QComboBox()
        self.supplier_input.addItem("No Supplier", None)
        suppliers = Supplier.select()
        for s in suppliers:
            self.supplier_input.addItem(s.name, s.id)
            
        form.addRow("Name *:", self.name_input)
        form.addRow("Code:", self.code_input)
        form.addRow("Category:", self.category_input)
        form.addRow("Unit:", self.unit_input)
        form.addRow("Initial Stock:", self.initial_stock_input)
        form.addRow("Unit Cost (₹):", self.cost_input)
        form.addRow("Min Stock Level:", self.min_stock_input)
        form.addRow("Supplier:", self.supplier_input)
        
        layout.addLayout(form)
        
        self.btn_save = QPushButton("Save Material")
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_save.clicked.connect(self.save)
        layout.addWidget(self.btn_save)

    def load_material_data(self):
        self.name_input.setText(self.material.name)
        self.code_input.setText(self.material.code or "")
        self.category_input.setCurrentText(self.material.category)
        self.unit_input.setCurrentText(self.material.unit)
        self.initial_stock_input.setText(str(self.material.quantity))
        self.cost_input.setText(str(self.material.unit_cost))
        self.min_stock_input.setText(str(self.material.min_stock))
        
        if self.material.supplier:
            index = self.supplier_input.findData(self.material.supplier.id)
            if index >= 0:
                self.supplier_input.setCurrentIndex(index)

    def save(self):
        name = self.name_input.text().strip()

        # Validate numeric fields
        stock_valid, stock_msg, stock_val = validate_positive_float(
            self.initial_stock_input.text(), "Initial Stock")
        cost_valid, cost_msg, cost_val = validate_positive_float(
            self.cost_input.text(), "Unit Cost")
        min_stock_valid, min_stock_msg, min_stock_val = validate_positive_float(
            self.min_stock_input.text(), "Min Stock Level")

        all_valid, error_msg = collect_errors([
            validate_required(name, "Material Name"),
            (stock_valid, stock_msg),
            (cost_valid, cost_msg),
            (min_stock_valid, min_stock_msg),
        ])

        if not all_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
            
        try:
            data = {
                'name': name,
                'code': self.code_input.text().strip() or None,
                'category': self.category_input.currentText(),
                'unit': self.unit_input.currentText(),
                'quantity': stock_val,
                'min_stock': min_stock_val,
                'unit_cost': cost_val,
                'supplier_id': self.supplier_input.currentData()
            }
            
            if self.material:
                InventoryService.update_material(self.material.id, data)
            else:
                InventoryService.create_material(data)
            
            relay.data_changed.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save material: {str(e)}")
