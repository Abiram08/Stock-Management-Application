from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                             QPushButton, QLabel, QMessageBox, QHBoxLayout)
from pathlib import Path
from database.models import Supplier, db
from services.communication_service import relay
from services.validators import validate_required, validate_phone, validate_gst, collect_errors

class SupplierFormDialog(QDialog):
    def __init__(self, supplier=None, parent=None):
        super().__init__(parent)
        self.supplier = supplier
        self.setWindowTitle("Edit Supplier" if supplier else "Register New Supplier")
        self.resize(450, 450)
        
        # Load Styles
        styles_path = Path(__file__).parent / "styles.qss"
        with open(styles_path, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())
            
        self.setup_ui()
        if self.supplier:
            self.fill_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title_text = "EDIT SUPPLIER" if self.supplier else "SUPPLIER REGISTRATION"
        title = QLabel(title_text)
        title.setObjectName("TitleLabel")
        title.setStyleSheet("font-size: 18px; letter-spacing: 1px;")
        layout.addWidget(title)
        
        form_container = QFormLayout()
        form_container.setSpacing(15)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Acme Chemicals Pvt Ltd")
        
        self.contact_person = QLineEdit()
        self.contact_person.setPlaceholderText("Primary Contact Person")
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. 9876543210 or +91 9876543210")
        
        self.gst_no_input = QLineEdit()
        self.gst_no_input.setPlaceholderText("e.g. 33AAAAA0000A1Z5")
        self.gst_no_input.setMaxLength(15)
        # Auto-uppercase GST input
        self.gst_no_input.textChanged.connect(
            lambda text: self.gst_no_input.setText(text.upper()) if text != text.upper() else None
        )
        
        self.categories_input = QLineEdit()
        self.categories_input.setPlaceholderText("e.g. Dyes, Chemicals, Tools")
        
        form_container.addRow("Company Name *:", self.name_input)
        form_container.addRow("Contact Person *:", self.contact_person)
        form_container.addRow("Phone / Mobile *:", self.phone_input)
        form_container.addRow("GST No:", self.gst_no_input)
        form_container.addRow("Categories *:", self.categories_input)
        
        layout.addLayout(form_container)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "SecondaryButton")
        btn_cancel.clicked.connect(self.reject)
        
        save_btn_text = "Update Supplier" if self.supplier else "Register Supplier"
        self.btn_save = QPushButton(save_btn_text)
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_save.clicked.connect(self.save)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def fill_data(self):
        self.name_input.setText(self.supplier.name)
        self.contact_person.setText(self.supplier.contact_person)
        self.phone_input.setText(self.supplier.phone)
        self.gst_no_input.setText(self.supplier.gst_no or "")
        self.categories_input.setText(self.supplier.material_categories)

    def save(self):
        # Collect all validation errors at once
        name = self.name_input.text().strip()
        contact = self.contact_person.text().strip()
        phone = self.phone_input.text().strip()
        gst = self.gst_no_input.text().strip()
        categories = self.categories_input.text().strip()

        all_valid, error_msg = collect_errors([
            validate_required(name, "Company Name"),
            validate_required(contact, "Contact Person"),
            validate_required(phone, "Phone Number"),
            validate_phone(phone),
            validate_gst(gst),
            validate_required(categories, "Categories"),
        ])

        if not all_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
            
        try:
            with db.atomic():
                if self.supplier:
                    # Update
                    self.supplier.name = name
                    self.supplier.contact_person = contact
                    self.supplier.phone = phone
                    self.supplier.gst_no = gst.upper() if gst else None
                    self.supplier.material_categories = categories
                    self.supplier.save()
                else:
                    # Create
                    Supplier.create(
                        name=name,
                        contact_person=contact,
                        phone=phone,
                        gst_no=gst.upper() if gst else None,
                        material_categories=categories
                    )
            relay.data_changed.emit()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save supplier: {str(e)}")
