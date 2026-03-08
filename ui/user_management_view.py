from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QDialog, QLineEdit, QComboBox,
                             QMessageBox, QFrame)
from PySide6.QtCore import Qt
from services.auth_service import AuthService
from services.audit_service import AuditService
from services.communication_service import relay
from services.validators import validate_username, validate_password, collect_errors


class UserFormDialog(QDialog):
    """Dialog for creating or editing a user."""
    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Edit User" if user else "Create User")
        self.setFixedSize(420, 380)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Title
        title = QLabel("Edit User" if self.user else "New User")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1E293B;")
        layout.addWidget(title)

        subtitle = QLabel("Update details below" if self.user else "Fill in the details below")
        subtitle.setStyleSheet("font-size: 12px; color: #64748B; margin-bottom: 8px;")
        layout.addWidget(subtitle)

        # Username
        lbl_user = QLabel("Username")
        lbl_user.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;")
        layout.addWidget(lbl_user)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumHeight(40)
        if self.user:
            self.username_input.setText(self.user.username)
            self.username_input.setEnabled(False)
        layout.addWidget(self.username_input)

        # Password
        lbl_pass = QLabel("Password" if not self.user else "New Password (leave blank to keep)")
        lbl_pass.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;")
        layout.addWidget(lbl_pass)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(40)
        layout.addWidget(self.password_input)

        # Role
        lbl_role = QLabel("Role")
        lbl_role.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.5px;")
        layout.addWidget(lbl_role)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["ADMIN", "SUPERVISOR", "STORE_MANAGER"])
        self.role_combo.setMinimumHeight(40)
        if self.user:
            idx = self.role_combo.findText(self.user.role)
            if idx >= 0:
                self.role_combo.setCurrentIndex(idx)
        layout.addWidget(self.role_combo)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setProperty("class", "SecondaryButton")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Update" if self.user else "Create")
        btn_save.setProperty("class", "PrimaryButton")
        btn_save.setMinimumHeight(40)
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self.handle_save)

        btn_row.addWidget(btn_cancel, 1)
        btn_row.addWidget(btn_save, 1)
        layout.addLayout(btn_row)

    def handle_save(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        role = self.role_combo.currentText()

        if not self.user:
            # Creating new user — validate both username and password
            validations = [
                validate_username(username),
                validate_password(password),
            ]
            all_valid, error_msg = collect_errors(validations)
            if not all_valid:
                QMessageBox.warning(self, "Validation Error", error_msg)
                return
            try:
                AuthService.create_user(username, password, role)
                AuditService.log('USER_CREATED', details={'username': username, 'role': role})
                self.accept()
            except ValueError as e:
                QMessageBox.warning(self, "Validation Error", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create user: {e}")
        else:
            # Editing existing user
            try:
                if password:
                    valid, msg = validate_password(password)
                    if not valid:
                        QMessageBox.warning(self, "Validation Error", msg)
                        return
                    AuthService.update_password(self.user.id, password)
                AuthService.update_user_role(self.user.id, role)
                AuditService.log('USER_UPDATED', details={'username': self.user.username, 'role': role})
                self.accept()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not update user: {e}")


class UserManagementView(QWidget):
    """Admin view for managing users."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()
        relay.data_changed.connect(self.load_data)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("User Management")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #1E293B;")
        subtitle = QLabel("Manage system users and roles")
        subtitle.setStyleSheet("font-size: 13px; color: #64748B;")

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        btn_create = QPushButton("  + New User")
        btn_create.setProperty("class", "PrimaryButton")
        btn_create.setCursor(Qt.PointingHandCursor)
        btn_create.setMinimumHeight(40)
        btn_create.clicked.connect(self.show_create_dialog)
        header.addWidget(btn_create)
        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Username", "Role", "Created", "Status", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.table.setColumnWidth(4, 180)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

    def load_data(self):
        users = AuthService.get_all_users()
        self.table.setRowCount(len(users))
        for i, user in enumerate(users):
            self.table.setRowHeight(i, 48)
            self.table.setItem(i, 0, QTableWidgetItem(user.username))
            
            role_item = QTableWidgetItem(user.role)
            role_item.setForeground(Qt.darkBlue if user.role == 'ADMIN' else Qt.darkGreen if user.role == 'STORE_MANAGER' else Qt.darkYellow)
            self.table.setItem(i, 1, role_item)
            
            self.table.setItem(i, 2, QTableWidgetItem(user.created_at.strftime("%d %b %Y") if user.created_at else "—"))
            
            status_item = QTableWidgetItem("Active")
            status_item.setForeground(Qt.darkGreen)
            self.table.setItem(i, 3, status_item)

            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(4, 4, 4, 4)
            actions_layout.setSpacing(6)

            btn_edit = QPushButton("Edit")
            btn_edit.setStyleSheet("""
                QPushButton { 
                    background-color: #EFF6FF; color: #734D31; border-radius: 6px; 
                    padding: 6px 14px; font-size: 11px; font-weight: 700; border: 1px solid #BFDBFE;
                }
                QPushButton:hover { background-color: #DBEAFE; }
            """)
            btn_edit.setCursor(Qt.PointingHandCursor)
            btn_edit.clicked.connect(lambda checked, u=user: self.show_edit_dialog(u))
            actions_layout.addWidget(btn_edit)

            if user.username != 'admin':
                btn_delete = QPushButton("Delete")
                btn_delete.setStyleSheet("""
                    QPushButton { 
                        background-color: #FEF2F2; color: #DC2626; border-radius: 6px; 
                        padding: 6px 14px; font-size: 11px; font-weight: 700; border: 1px solid #FECACA;
                    }
                    QPushButton:hover { background-color: #FEE2E2; }
                """)
                btn_delete.setCursor(Qt.PointingHandCursor)
                btn_delete.clicked.connect(lambda checked, u=user: self.handle_delete(u))
                actions_layout.addWidget(btn_delete)

            actions_layout.addStretch()
            self.table.setCellWidget(i, 4, actions_widget)

    def show_create_dialog(self):
        dialog = UserFormDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
            relay.data_changed.emit()

    def show_edit_dialog(self, user):
        dialog = UserFormDialog(self, user=user)
        if dialog.exec() == QDialog.Accepted:
            self.load_data()
            relay.data_changed.emit()

    def handle_delete(self, user):
        confirm = QMessageBox.question(
            self, "Delete User",
            f"Are you sure you want to delete user '{user.username}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            try:
                AuthService.delete_user(user.id)
                AuditService.log('USER_DELETED', details={'username': user.username})
                self.load_data()
                relay.data_changed.emit()
            except ValueError as e:
                QMessageBox.warning(self, "Cannot Delete", str(e))
