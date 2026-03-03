import os
import shutil
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QFileDialog, QFormLayout, QMessageBox, QFrame)
from PySide6.QtGui import QPixmap, QTransform
from PySide6.QtCore import Qt
from database.models import CompanyProfile, db
from services.communication_service import relay
from services.validators import (validate_required, validate_gst, validate_email, 
                                  validate_phone, validate_positive_float, 
                                  validate_percentage, collect_errors)

class ProfileView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Header
        header_container = QVBoxLayout()
        title = QLabel("Company Settings")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Update your company identity and billing information for invoices.")
        subtitle.setObjectName("SubtitleLabel")
        header_container.addWidget(title)
        header_container.addWidget(subtitle)
        layout.addLayout(header_container)
        
        # Main Content area (Split in two)
        content_row = QHBoxLayout()
        content_row.setSpacing(40)
        
        # LEFT: Form
        form_card = QFrame()
        form_card.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E2E8F0;")
        form_layout = QFormLayout(form_card)
        form_layout.setContentsMargins(30, 30, 30, 30)
        form_layout.setSpacing(20)
        
        self.name_input = QLineEdit()
        self.address_input = QLineEdit()
        self.gstin_input = QLineEdit()
        self.gstin_input.setMaxLength(15)
        # Auto-uppercase GSTIN input
        self.gstin_input.textChanged.connect(
            lambda text: self.gstin_input.setText(text.upper()) if text != text.upper() else None
        )
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("e.g. accounts@texknit.com")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. 9876543210 or +91 9876543210")
        self.tax_input = QLineEdit()
        self.tax_input.setPlaceholderText("0 - 100")
        self.late_fee_input = QLineEdit()
        self.late_fee_input.setPlaceholderText("e.g. 100.00")
        
        for inp in [self.name_input, self.address_input, self.gstin_input, self.email_input, self.phone_input, self.tax_input, self.late_fee_input]:
            inp.setMinimumHeight(45)
            inp.setStyleSheet("border: 1px solid #CBD5E1; border-radius: 8px; padding: 0 12px;")

        form_layout.addRow("<b>Company Name *</b>", self.name_input)
        form_layout.addRow("<b>Address *</b>", self.address_input)
        form_layout.addRow("<b>GSTIN</b>", self.gstin_input)
        form_layout.addRow("<b>Email</b>", self.email_input)
        form_layout.addRow("<b>Phone *</b>", self.phone_input)
        form_layout.addRow("<b>Default Sales Tax (%)</b>", self.tax_input)
        form_layout.addRow("<b>Daily Late Fee (INR)</b>", self.late_fee_input)
        
        # RIGHT: Logo Upload
        logo_card = QFrame()
        logo_card.setFixedWidth(300)
        logo_card.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #E2E8F0;")
        logo_layout = QVBoxLayout(logo_card)
        logo_layout.setContentsMargins(30, 30, 30, 30)
        logo_layout.setSpacing(20)
        
        lbl_logo = QLabel("COMPANY LOGO")
        lbl_logo.setStyleSheet("font-weight: 700; font-size: 11px; color: #64748B; text-align: center;")
        lbl_logo.setAlignment(Qt.AlignCenter)
        
        self.logo_preview = QLabel("No Logo Uploaded")
        self.logo_preview.setFixedSize(200, 200)
        self.logo_preview.setStyleSheet("background: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 8px; color: #94A3B8;")
        self.logo_preview.setAlignment(Qt.AlignCenter)
        
        self.btn_upload = QPushButton("Upload Logo")
        self.btn_upload.setProperty("class", "SecondaryButton")
        self.btn_upload.setStyleSheet("background: #F1F5F9; border: 1px solid #E2E8F0; padding: 8px;")
        self.btn_upload.clicked.connect(self.upload_logo)
        
        self.btn_rotate = QPushButton("Rotate 90°")
        self.btn_rotate.setProperty("class", "SecondaryButton")
        self.btn_rotate.setStyleSheet("background: #F1F5F9; border: 1px solid #E2E8F0; padding: 8px;")
        self.btn_rotate.clicked.connect(self.rotate_logo)
        self.btn_rotate.setEnabled(False) # Enable only after upload or load
        
        logo_layout.addWidget(lbl_logo)
        logo_layout.addWidget(self.logo_preview, alignment=Qt.AlignCenter)
        logo_layout.addWidget(self.btn_upload)
        logo_layout.addWidget(self.btn_rotate)
        logo_layout.addStretch()
        
        content_row.addWidget(form_card, 2)
        content_row.addWidget(logo_card, 1)
        layout.addLayout(content_row)
        
        # Bottom Actions
        self.btn_save = QPushButton("Save Company Profile")
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_save.setFixedWidth(250)
        self.btn_save.setMinimumHeight(50)
        self.btn_save.clicked.connect(self.save)
        layout.addWidget(self.btn_save, alignment=Qt.AlignRight)
        
        self.selected_logo_path = None

    def load_data(self):
        profile = CompanyProfile.get_or_none()
        if not profile:
            profile = CompanyProfile.create()
            
        self.name_input.setText(profile.name)
        self.address_input.setText(profile.address)
        self.gstin_input.setText(profile.gstin)
        self.email_input.setText(profile.email)
        self.phone_input.setText(profile.phone)
        self.tax_input.setText(str(profile.default_tax_rate))
        self.late_fee_input.setText(str(profile.daily_late_fee))
        
        if profile.logo_path and os.path.exists(profile.logo_path):
            self.display_logo(profile.logo_path)
            self.btn_rotate.setEnabled(True)

    def upload_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            self.selected_logo_path = file_path
            self.display_logo(file_path)
            self.btn_rotate.setEnabled(True)

    def rotate_logo(self):
        # We need the current pixmap to rotate it
        current_pixmap = self.logo_preview.pixmap()
        if not current_pixmap or current_pixmap.isNull():
            # If we just uploaded but haven't saved, we might have selected_logo_path
            if self.selected_logo_path:
                current_pixmap = QPixmap(self.selected_logo_path)
            else:
                return

        transform = QTransform().rotate(90)
        rotated_pixmap = current_pixmap.transformed(transform, Qt.SmoothTransformation)
        
        # We must save this temporarily or mark for saving
        # To make it simple, we'll save it as a temporary file in assets/logos
        temp_path = os.path.join("assets/logos", "rotated_temp.png")
        os.makedirs("assets/logos", exist_ok=True)
        rotated_pixmap.save(temp_path, "PNG")
        
        self.selected_logo_path = temp_path
        self.display_logo(temp_path)

    def display_logo(self, path):
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            scaled = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_preview.setPixmap(scaled)
            self.logo_preview.setStyleSheet("border: 2px solid #E2E8F0; border-radius: 8px;")
        else:
            self.logo_preview.setText("Invalid Image")

    def save(self):
        name = self.name_input.text().strip()
        address = self.address_input.text().strip()
        gstin = self.gstin_input.text().strip()
        email = self.email_input.text().strip()
        phone = self.phone_input.text().strip()

        # Validate numeric fields
        tax_valid, tax_msg, tax_val = validate_percentage(self.tax_input.text(), "Sales Tax (%)")
        fee_valid, fee_msg, fee_val = validate_positive_float(self.late_fee_input.text(), "Daily Late Fee")

        all_valid, error_msg = collect_errors([
            validate_required(name, "Company Name"),
            validate_required(address, "Address"),
            validate_gst(gstin),
            validate_email(email),
            validate_required(phone, "Phone"),
            validate_phone(phone),
            (tax_valid, tax_msg),
            (fee_valid, fee_msg),
        ])

        if not all_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return

        profile = CompanyProfile.get_or_none()
        if not profile:
            profile = CompanyProfile()
            
        profile.name = name
        profile.address = address
        profile.gstin = gstin.upper() if gstin else ""
        profile.email = email
        profile.phone = phone
        profile.default_tax_rate = tax_val if tax_val is not None else 18.0
        profile.daily_late_fee = fee_val if fee_val is not None else 0.0
        
        if self.selected_logo_path:
            import time
            timestamp = int(time.time())
            new_filename = f"logo_{timestamp}.png"
            local_path = os.path.join("assets/logos", new_filename)
            
            try:
                os.makedirs("assets/logos", exist_ok=True)
                
                # Only copy if it's not already the target file
                if os.path.abspath(self.selected_logo_path) != os.path.abspath(local_path):
                    shutil.copy2(self.selected_logo_path, local_path)
                
                # Cleanup old logo file if it exists
                if profile.logo_path and os.path.exists(profile.logo_path) and profile.logo_path != local_path:
                    try:
                        os.remove(profile.logo_path)
                    except:
                        pass # Ignore cleanup errors
                        
                profile.logo_path = local_path
            except Exception as e:
                QMessageBox.warning(self, "Logo Error", f"Failed to save logo file: {e}")

        profile.save()
        QMessageBox.information(self, "Success", "Company profile updated successfully. This will be reflected in all invoices.")
        
        # Trigger reactivity
        relay.data_changed.emit()
