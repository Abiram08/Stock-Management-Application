from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFrame,
                             QDialog, QFormLayout, QLineEdit, QMessageBox)
from PySide6.QtCore import Qt
from pathlib import Path
from database.models import Consumer
from services.communication_service import relay
from services.validators import validate_required, validate_phone, validate_gst, collect_errors

class ConsumerFormDialog(QDialog):
    def __init__(self, consumer=None, parent=None):
        super().__init__(parent)
        self.consumer = consumer
        self.setWindowTitle("Add New Consumer" if not consumer else "Edit Consumer")
        self.setMinimumWidth(450)
        self.resize(450, 420)
        
        # Load Styles
        styles_path = Path(__file__).parent / "styles.qss"
        with open(styles_path, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter company name")
        if self.consumer: self.name_input.setText(self.consumer.company_name)
        
        self.person_input = QLineEdit()
        self.person_input.setPlaceholderText("Contact person name")
        if self.consumer: self.person_input.setText(self.consumer.contact_person)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("e.g. 9876543210 or +91 9876543210")
        if self.consumer: self.phone_input.setText(self.consumer.phone)
        
        self.gst_input = QLineEdit()
        self.gst_input.setPlaceholderText("e.g. 33AAAAA0000A1Z5 (Optional)")
        self.gst_input.setMaxLength(15)
        # Auto-uppercase GST input
        self.gst_input.textChanged.connect(
            lambda text: self.gst_input.setText(text.upper()) if text != text.upper() else None
        )
        if self.consumer: self.gst_input.setText(self.consumer.gst_no or "")
        
        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("City / Region / Location")
        if self.consumer: self.location_input.setText(self.consumer.location or "")
        
        form_layout.addRow("Company Name *:", self.name_input)
        form_layout.addRow("Contact Person *:", self.person_input)
        form_layout.addRow("Phone Number *:", self.phone_input)
        form_layout.addRow("GST No:", self.gst_input)
        form_layout.addRow("Location:", self.location_input)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Button Row
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "SecondaryButton")
        btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("Update Consumer" if self.consumer else "Save Consumer")
        self.btn_save.setProperty("class", "PrimaryButton")
        self.btn_save.clicked.connect(self.save)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def save(self):
        name = self.name_input.text().strip()
        person = self.person_input.text().strip()
        phone = self.phone_input.text().strip()
        gst = self.gst_input.text().strip()

        all_valid, error_msg = collect_errors([
            validate_required(name, "Company Name"),
            validate_required(person, "Contact Person"),
            validate_required(phone, "Phone Number"),
            validate_phone(phone),
            validate_gst(gst),
        ])

        if not all_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return
            
        if self.consumer:
            self.consumer.company_name = name
            self.consumer.contact_person = person
            self.consumer.phone = phone
            self.consumer.gst_no = gst.upper() if gst else None
            self.consumer.location = self.location_input.text().strip()
            self.consumer.save()
        else:
            Consumer.create(
                company_name=name,
                contact_person=person,
                phone=phone,
                gst_no=gst.upper() if gst else None,
                location=self.location_input.text().strip()
            )
        
        # Notify reactivity system
        relay.data_changed.emit()
        self.accept()

class ConsumerManagementView(QWidget):
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
        
        # Header
        header_layout = QHBoxLayout()
        title_container = QVBoxLayout()
        title = QLabel("Consumer Management")
        title.setObjectName("TitleLabel")
        subtitle = QLabel("Manage your client list, their contact details and billing locations.")
        subtitle.setObjectName("SubtitleLabel")
        title_container.addWidget(title)
        title_container.addWidget(subtitle)
        header_layout.addLayout(title_container)
        
        header_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search consumers...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_data)
        header_layout.addWidget(self.search_input)
        
        self.btn_add = QPushButton("+ Add New Consumer")
        self.btn_add.setProperty("class", "PrimaryButton")
        self.btn_add.clicked.connect(self.show_add_consumer)
        header_layout.addWidget(self.btn_add)
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "S.No", "Company Name", "Contact Person", "Mobile", "GST No", "Location", "Actions"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(6, 180)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60) 
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget { 
                background: white; 
                border-radius: 12px; 
                gridline-color: transparent;
                border: 1px solid #E5E7EB;
            }
        """)
        
        layout.addWidget(self.table)

    def load_data(self):
        self.all_consumers = list(Consumer.select().order_by(Consumer.company_name))
        self.display_data(self.all_consumers)

    def filter_data(self):
        term = self.search_input.text().lower()
        filtered = [c for c in self.all_consumers if
                    term in c.company_name.lower() or
                    term in (c.contact_person or '').lower() or
                    term in (c.phone or '').lower()]
        self.display_data(filtered)

    def display_data(self, consumers):
        self.table.setRowCount(len(consumers))
        
        for i, c in enumerate(consumers):
            # 0. S.No
            sno_item = QTableWidgetItem(str(i + 1))
            sno_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, sno_item)

            self.table.setItem(i, 1, QTableWidgetItem(c.company_name))
            self.table.setItem(i, 2, QTableWidgetItem(c.contact_person))
            self.table.setItem(i, 3, QTableWidgetItem(c.phone))
            self.table.setItem(i, 4, QTableWidgetItem(c.gst_no or "N/A"))
            self.table.setItem(i, 5, QTableWidgetItem(c.location or "N/A"))
            
            btn_edit = QPushButton("✎")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.setToolTip("Edit Consumer")
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #FFFFFF;
                    color: #8B5E3C;
                    border: 1px solid rgba(139, 94, 60, 0.2);
                    border-radius: 16px;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #8B5E3C;
                    color: white;
                    border: none;
                }
            """)
            btn_edit.clicked.connect(lambda checked=False, consumer=c: self.show_edit_consumer(consumer))
            
            btn_delete = QPushButton("✕")
            btn_delete.setFixedSize(32, 32)
            btn_delete.setCursor(Qt.PointingHandCursor)
            btn_delete.setToolTip("Delete Consumer")
            btn_delete.setStyleSheet("""
                QPushButton {
                    background-color: #FEE2E2;
                    color: #991B1B;
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
            btn_delete.clicked.connect(lambda checked=False, consumer=c: self.confirm_delete(consumer))

            # Container for centering
            container = QWidget()
            btn_layout = QHBoxLayout(container)
            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_layout.setSpacing(12)
            btn_layout.setAlignment(Qt.AlignCenter)
            btn_layout.addWidget(btn_edit)
            btn_layout.addWidget(btn_delete)
            self.table.setCellWidget(i, 6, container)

    def confirm_delete(self, consumer):
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete {consumer.company_name}?\nThis action cannot be undone.",
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            consumer.delete_instance()
            relay.data_changed.emit()
            self.load_data()

    def show_add_consumer(self):
        dialog = ConsumerFormDialog(parent=self)
        dialog.exec()

    def show_edit_consumer(self, consumer):
        dialog = ConsumerFormDialog(consumer=consumer, parent=self)
        dialog.exec()
