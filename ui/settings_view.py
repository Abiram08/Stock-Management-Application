from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QSpinBox,
                             QDoubleSpinBox, QMessageBox, QTabWidget)
from PySide6.QtCore import Qt
from database.models import Setting, CompanyProfile
from services.audit_service import AuditService


class SettingsView(QWidget):
    """Admin settings panel."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Header
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0F172A;")
        subtitle = QLabel("System configuration and defaults")
        subtitle.setStyleSheet("font-size: 13px; color: #64748B;")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_notifications_tab(), "Notifications")
        tabs.addTab(self._create_defaults_tab(), "System Defaults")
        layout.addWidget(tabs)

    def _create_notifications_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Expiry Warning Days
        card1 = self._create_setting_card(
            "Expiry Warning Threshold",
            "Number of days before expiry to show warning alerts for chemicals.",
            "days"
        )
        self.expiry_days_input = card1.findChild(QSpinBox)
        layout.addWidget(card1)

        # Low Stock Multiplier
        card2 = self._create_setting_card(
            "Low Stock Alert Multiplier",
            "Multiplier for minimum stock threshold. E.g., 1.0 = alert at min_stock, 1.5 = alert at 1.5x min_stock.",
            "multiplier",
            is_float=True
        )
        self.low_stock_input = card2.findChild(QDoubleSpinBox)
        layout.addWidget(card2)

        layout.addStretch()

        # Save button
        btn_save = QPushButton("  Save Notification Settings")
        btn_save.setProperty("class", "PrimaryButton")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setMinimumHeight(42)
        btn_save.setMaximumWidth(280)
        btn_save.clicked.connect(self.save_notifications)
        layout.addWidget(btn_save)

        return widget

    def _create_defaults_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Default Shelf Life
        card1 = self._create_setting_card(
            "Default Shelf Life",
            "Default shelf life in days for new chemicals/dyes when not specified.",
            "days"
        )
        self.default_shelf_life = card1.findChild(QSpinBox)
        layout.addWidget(card1)

        # Default Tax Rate 
        card2 = self._create_setting_card(
            "Default GST Rate",
            "Default GST percentage for invoices.",
            "percent",
            is_float=True
        )
        self.default_tax = card2.findChild(QDoubleSpinBox)
        layout.addWidget(card2)

        layout.addStretch()

        # Save button
        btn_save = QPushButton("  Save Default Settings")
        btn_save.setProperty("class", "PrimaryButton")
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.setMinimumHeight(42)
        btn_save.setMaximumWidth(280)
        btn_save.clicked.connect(self.save_defaults)
        layout.addWidget(btn_save)

        return widget

    def _create_setting_card(self, title, description, suffix, is_float=False):
        card = QFrame()
        card.setStyleSheet("background-color: #FFFFFF; border-radius: 12px; border: none;")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(20)

        # Text side
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
        lbl_desc = QLabel(description)
        lbl_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        lbl_desc.setWordWrap(True)
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_desc)
        card_layout.addLayout(text_layout, 3)

        # Input side
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        if is_float:
            spin = QDoubleSpinBox()
            spin.setRange(0, 9999)
            spin.setDecimals(1)
            spin.setSingleStep(0.5)
        else:
            spin = QSpinBox()
            spin.setRange(0, 9999)

        spin.setMinimumHeight(40)
        spin.setMinimumWidth(100)
        input_layout.addWidget(spin)

        lbl_suffix = QLabel(suffix)
        lbl_suffix.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 600;")
        input_layout.addWidget(lbl_suffix)

        card_layout.addLayout(input_layout, 1)

        return card

    def load_settings(self):
        try:
            expiry_days = Setting.get_value('expiry_warning_days', '30')
            self.expiry_days_input.setValue(int(expiry_days))

            low_stock = Setting.get_value('low_stock_multiplier', '1.0')
            self.low_stock_input.setValue(float(low_stock))

            shelf_life = Setting.get_value('default_shelf_life', '365')
            self.default_shelf_life.setValue(int(shelf_life))

            profile = CompanyProfile.get_or_none()
            if profile:
                self.default_tax.setValue(profile.default_tax_rate)
            else:
                self.default_tax.setValue(18.0)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_notifications(self):
        try:
            Setting.set_value('expiry_warning_days', str(self.expiry_days_input.value()), 'notifications')
            Setting.set_value('low_stock_multiplier', str(self.low_stock_input.value()), 'defaults')
            AuditService.log('SETTINGS_UPDATED', details={'category': 'notifications'})
            QMessageBox.information(self, "Saved", "Notification settings saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save settings: {e}")

    def save_defaults(self):
        try:
            Setting.set_value('default_shelf_life', str(self.default_shelf_life.value()), 'defaults')
            
            profile = CompanyProfile.get_or_none()
            if profile:
                profile.default_tax_rate = self.default_tax.value()
                profile.save()
            
            AuditService.log('SETTINGS_UPDATED', details={'category': 'defaults'})
            QMessageBox.information(self, "Saved", "Default settings saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save settings: {e}")
