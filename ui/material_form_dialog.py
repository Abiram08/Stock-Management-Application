from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QPushButton, QLabel, QMessageBox, QDateEdit,
                             QSpinBox, QDoubleSpinBox, QTabWidget, QWidget)
from PySide6.QtCore import Qt, QDate
from pathlib import Path
from database.models import Supplier, Material
from services.inventory_service import InventoryService
from services.communication_service import relay
from services.validators import validate_required, validate_positive_float, validate_temp_range, validate_date_order, collect_errors


class MaterialFormDialog(QDialog):
    def __init__(self, material=None, parent=None):
        super().__init__(parent)
        self.material = material
        self.setWindowTitle("Edit Material" if material else "Add New Material")
        self.resize(520, 580)

        # Load Styles
        styles_path = Path(__file__).parent / "styles.qss"
        with open(styles_path, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

        self.setup_ui()
        if material:
            self.load_material_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel(self.windowTitle().upper())
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F172A; margin-bottom: 6px;")
        layout.addWidget(title)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_basic_tab(), "Basic Info")
        tabs.addTab(self._create_safety_tab(), "Chemical Safety")
        layout.addWidget(tabs)

        # Button Row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "SecondaryButton")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setMinimumHeight(40)
        btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Update Material" if self.material else "Save Material")
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setMinimumHeight(40)
        self.btn_save.clicked.connect(self.save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def _create_basic_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(8, 12, 8, 12)
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Reactive Red 195")
        self.name_input.setMinimumHeight(36)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("SKU / Product Code (optional)")
        self.code_input.setMinimumHeight(36)

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
        self.category_input.setMinimumHeight(36)

        self.unit_input = QComboBox()
        self.unit_input.addItems(["kg", "ltr", "pcs", "mtr", "bag"])
        self.unit_input.setMinimumHeight(36)

        self.initial_stock_input = QLineEdit()
        self.initial_stock_input.setPlaceholderText("0.0")
        self.initial_stock_input.setText("0")
        self.initial_stock_input.setMinimumHeight(36)

        self.cost_input = QLineEdit()
        self.cost_input.setPlaceholderText("0.0")
        self.cost_input.setMinimumHeight(36)

        self.min_stock_input = QLineEdit()
        self.min_stock_input.setPlaceholderText("10.0")
        self.min_stock_input.setText("10")
        self.min_stock_input.setMinimumHeight(36)

        self.supplier_input = QComboBox()
        self.supplier_input.addItem("No Supplier", None)
        suppliers = Supplier.select()
        for s in suppliers:
            self.supplier_input.addItem(s.name, s.id)
        self.supplier_input.setMinimumHeight(36)

        form.addRow("Name *:", self.name_input)
        form.addRow("Code:", self.code_input)
        form.addRow("Category:", self.category_input)
        form.addRow("Unit:", self.unit_input)
        form.addRow("Initial Stock:", self.initial_stock_input)
        form.addRow("Unit Cost (₹):", self.cost_input)
        form.addRow("Min Stock:", self.min_stock_input)
        form.addRow("Supplier:", self.supplier_input)

        return widget

    def _create_safety_tab(self):
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(8, 12, 8, 12)
        form.setSpacing(10)

        self.hazard_input = QComboBox()
        self.hazard_input.addItems(["None", "Flammable", "Corrosive", "Irritant", "Toxic", "Oxidizing"])
        self.hazard_input.setMinimumHeight(36)

        self.shelf_life_input = QSpinBox()
        self.shelf_life_input.setRange(0, 9999)
        self.shelf_life_input.setValue(0)
        self.shelf_life_input.setSuffix(" days")
        self.shelf_life_input.setSpecialValueText("Not set")
        self.shelf_life_input.setMinimumHeight(36)

        self.manufacture_date_input = QDateEdit()
        self.manufacture_date_input.setCalendarPopup(True)
        self.manufacture_date_input.setDate(QDate.currentDate())
        self.manufacture_date_input.setMinimumHeight(36)
        self.manufacture_date_input.setSpecialValueText("Not set")

        self.expiry_date_input = QDateEdit()
        self.expiry_date_input.setCalendarPopup(True)
        self.expiry_date_input.setDate(QDate.currentDate().addYears(1))
        self.expiry_date_input.setMinimumHeight(36)
        self.expiry_date_input.setSpecialValueText("Not set")

        self.storage_min_input = QDoubleSpinBox()
        self.storage_min_input.setRange(-50, 100)
        self.storage_min_input.setValue(5)
        self.storage_min_input.setSuffix(" °C")
        self.storage_min_input.setMinimumHeight(36)

        self.storage_max_input = QDoubleSpinBox()
        self.storage_max_input.setRange(-50, 100)
        self.storage_max_input.setValue(35)
        self.storage_max_input.setSuffix(" °C")
        self.storage_max_input.setMinimumHeight(36)

        form.addRow("Hazard Class:", self.hazard_input)
        form.addRow("Shelf Life:", self.shelf_life_input)
        form.addRow("Manufacture Date:", self.manufacture_date_input)
        form.addRow("Expiry Date:", self.expiry_date_input)
        form.addRow("Storage Min Temp:", self.storage_min_input)
        form.addRow("Storage Max Temp:", self.storage_max_input)

        # Info label
        info = QLabel("⚠️ These fields help track chemical safety and compliance.\n"
                      "Leave shelf life at 0 if not applicable.")
        info.setStyleSheet("font-size: 11px; color: #64748B; margin-top: 8px;")
        info.setWordWrap(True)
        form.addRow(info)

        return widget

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

        # Safety fields
        if self.material.hazard_class:
            self.hazard_input.setCurrentText(self.material.hazard_class)
        if self.material.shelf_life_days:
            self.shelf_life_input.setValue(self.material.shelf_life_days)
        if self.material.manufacture_date:
            self.manufacture_date_input.setDate(QDate(
                self.material.manufacture_date.year,
                self.material.manufacture_date.month,
                self.material.manufacture_date.day
            ))
        if self.material.expiry_date:
            self.expiry_date_input.setDate(QDate(
                self.material.expiry_date.year,
                self.material.expiry_date.month,
                self.material.expiry_date.day
            ))
        if self.material.storage_temp_min is not None:
            self.storage_min_input.setValue(self.material.storage_temp_min)
        if self.material.storage_temp_max is not None:
            self.storage_max_input.setValue(self.material.storage_temp_max)

    def save(self):
        name = self.name_input.text().strip()

        # Validate numeric fields
        stock_valid, stock_msg, stock_val = validate_positive_float(
            self.initial_stock_input.text(), "Initial Stock")
        cost_valid, cost_msg, cost_val = validate_positive_float(
            self.cost_input.text(), "Unit Cost")
        min_stock_valid, min_stock_msg, min_stock_val = validate_positive_float(
            self.min_stock_input.text(), "Min Stock Level")

        # Cross-field validations
        temp_min = self.storage_min_input.value()
        temp_max = self.storage_max_input.value()

        validations = [
            validate_required(name, "Material Name"),
            (stock_valid, stock_msg),
            (cost_valid, cost_msg),
            (min_stock_valid, min_stock_msg),
            validate_temp_range(temp_min, temp_max),
        ]

        # Validate manufacture < expiry date when shelf life is set
        if self.shelf_life_input.value() > 0:
            mfg_date = self.manufacture_date_input.date().toPython()
            exp_date = self.expiry_date_input.date().toPython()
            validations.append(
                validate_date_order(mfg_date, exp_date, "Manufacture Date", "Expiry Date")
            )

        all_valid, error_msg = collect_errors(validations)

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
                'supplier_id': self.supplier_input.currentData(),
                # Safety fields
                'hazard_class': self.hazard_input.currentText(),
                'shelf_life_days': self.shelf_life_input.value() if self.shelf_life_input.value() > 0 else None,
                'manufacture_date': self.manufacture_date_input.date().toPython() if self.shelf_life_input.value() > 0 else None,
                'expiry_date': self.expiry_date_input.date().toPython() if self.shelf_life_input.value() > 0 else None,
                'storage_temp_min': self.storage_min_input.value(),
                'storage_temp_max': self.storage_max_input.value(),
            }

            if self.material:
                InventoryService.update_material(self.material.id, data)
            else:
                InventoryService.create_material(data)

            relay.data_changed.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save material: {str(e)}")
