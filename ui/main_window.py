from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame, QMessageBox, QApplication, QSizePolicy)
from PySide6.QtCore import Qt, Signal
from pathlib import Path

from ui.inventory_management import InventoryManagementView
from ui.mrs_workflow import MRSWorkflowView
from ui.procurement_manager import ProcurementManagerView
from ui.analytics_view import AnalyticsView
from ui.supplier_management import SupplierManagementView


class MainWindow(QMainWindow):
    logout_signal = Signal()

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("TEXKNIT COLORS — Management System")
        self.resize(1280, 880)

        # Load Styles
        styles_path = Path(__file__).parent / "styles.qss"
        with open(styles_path, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ═══════════════════ SIDEBAR ═══════════════════
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 24, 0, 20)
        sidebar_layout.setSpacing(0)

        # App Title
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(20, 0, 20, 0)
        title_layout.setSpacing(2)
        app_title = QLabel("TEXKNIT")
        app_title.setObjectName("TitleLabel")
        app_title.setAlignment(Qt.AlignCenter)
        app_subtitle = QLabel("COLORS")
        app_subtitle.setObjectName("SubtitleLabel")
        app_subtitle.setAlignment(Qt.AlignCenter)

        title_layout.addWidget(app_title)
        title_layout.addWidget(app_subtitle)
        sidebar_layout.addWidget(title_container)
        sidebar_layout.addSpacing(28)

        # Navigation buttons storage
        self.nav_buttons = []
        self.nav_views = []

        # ─── MAIN SECTION ───
        main_section = QLabel("MAIN")
        main_section.setObjectName("SectionLabel")
        sidebar_layout.addWidget(main_section)

        self._add_nav("📊  Dashboard", sidebar_layout)
        self._add_nav("📦  Inventory", sidebar_layout)
        self._add_nav("📄  Invoices", sidebar_layout)
        self._add_nav("👥  Consumers", sidebar_layout)
        self._add_nav("🏭  Suppliers", sidebar_layout)
        self._add_nav("🛒  Procurement", sidebar_layout)

        sidebar_layout.addSpacing(12)

        # ─── ADMIN SECTION ─── (only for ADMIN)
        if self.user.role == 'ADMIN':
            admin_section = QLabel("ADMINISTRATION")
            admin_section.setObjectName("SectionLabel")
            sidebar_layout.addWidget(admin_section)

            self._add_nav("👤  Users", sidebar_layout)
            self._add_nav("📋  Audit Logs", sidebar_layout)
            self._add_nav("⚙️  Settings", sidebar_layout)

        sidebar_layout.addStretch()

        # ─── USER CARD ───
        user_container = QFrame()
        user_container.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: none;
                border-radius: 10px;
                margin: 4px 10px;
            }
        """)

        user_main_layout = QVBoxLayout(user_container)
        user_main_layout.setContentsMargins(12, 12, 12, 12)
        user_main_layout.setSpacing(10)

        # Identity Row
        identity_row = QHBoxLayout()
        identity_row.setSpacing(10)

        avatar = QLabel(self.user.username[0].upper())
        avatar.setFixedSize(34, 34)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #FFFFFF;
            color: #000000;
            border-radius: 17px;
            font-weight: 900;
            font-size: 16px;
            border: 1px solid #E2E8F0;
        """)

        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(2)
        user_name = QLabel(self.user.username.upper())
        user_name.setStyleSheet("color: #000000; font-weight: 800; font-size: 13px; border: none;")
        user_name.setAlignment(Qt.AlignCenter)
        
        user_role = QLabel(self.user.role.replace('_', ' '))
        user_role.setStyleSheet("color: #000000; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; border: none;")
        user_role.setAlignment(Qt.AlignCenter)

        info_vbox.addWidget(user_name)
        info_vbox.addWidget(user_role)

        identity_row.addStretch()
        identity_row.addWidget(avatar)
        identity_row.addLayout(info_vbox)
        identity_row.addStretch()

        user_main_layout.addLayout(identity_row)

        # Actions Row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(6)

        self.btn_profile = QPushButton("Profile")
        self.btn_profile.setCursor(Qt.PointingHandCursor)
        self.btn_profile.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_profile.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border-radius: 6px;
                padding: 6px 0px;
                font-size: 10px;
                font-weight: 700;
                border: 1px solid #E2E8F0;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
        """)
        self.btn_profile.clicked.connect(self.show_profile)

        self.btn_logout = QPushButton("Logout")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.1);
                color: #EF4444;
                border-radius: 6px;
                padding: 6px 0px;
                font-size: 10px;
                font-weight: 700;
                border: none;
                text-align: center;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.2);
            }
        """)
        self.btn_logout.clicked.connect(self.handle_logout)

        actions_row.addWidget(self.btn_profile, 1)
        actions_row.addWidget(self.btn_logout, 1)
        user_main_layout.addLayout(actions_row)

        sidebar_layout.addWidget(user_container)

        main_layout.addWidget(self.sidebar)

        # ═══════════════════ CONTENT AREA ═══════════════════
        content_layer = QWidget()
        content_layer.setObjectName("ContentArea")
        cl_layout = QVBoxLayout(content_layer)
        cl_layout.setContentsMargins(0, 0, 0, 0)

        self.content_stack = QStackedWidget()

        # ── Create all pages ──
        self.dashboard_view = AnalyticsView()
        self.inventory_view = InventoryManagementView()
        self.mrs_view = MRSWorkflowView(self.user)
        from ui.consumer_management import ConsumerManagementView
        self.consumers_view = ConsumerManagementView(self.user)
        self.suppliers_view = SupplierManagementView()
        self.procurement_view = ProcurementManagerView(self.user)
        from ui.profile_view import ProfileView
        self.profile_view = ProfileView()

        # Add main pages to stack (these map 1:1 with main nav buttons)
        main_views = [
            self.dashboard_view,
            self.inventory_view,
            self.mrs_view,
            self.consumers_view,
            self.suppliers_view,
            self.procurement_view,
        ]

        for view in main_views:
            self.content_stack.addWidget(view)
            self.nav_views.append(view)

        # Add admin pages if admin
        if self.user.role == 'ADMIN':
            from ui.user_management_view import UserManagementView
            from ui.audit_log_view import AuditLogView
            from ui.settings_view import SettingsView

            self.users_view = UserManagementView()
            self.audit_view = AuditLogView()
            self.settings_view = SettingsView()

            admin_views = [self.users_view, self.audit_view, self.settings_view]
            for view in admin_views:
                self.content_stack.addWidget(view)
                self.nav_views.append(view)

        # Profile view (not in nav, accessed separately)
        self.content_stack.addWidget(self.profile_view)

        cl_layout.addWidget(self.content_stack)
        main_layout.addWidget(content_layer)

        # Set first button active
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)

    def _add_nav(self, text, layout):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.handle_nav_click)
        self.nav_buttons.append(btn)
        layout.addWidget(btn)

    def handle_nav_click(self):
        btn = self.sender()
        # Uncheck all others
        for b in self.nav_buttons:
            if b != btn:
                b.setChecked(False)
        btn.setChecked(True)

        index = self.nav_buttons.index(btn)
        if index < len(self.nav_views):
            self.content_stack.setCurrentWidget(self.nav_views[index])

    def show_profile(self):
        for b in self.nav_buttons:
            b.setChecked(False)
        self.content_stack.setCurrentWidget(self.profile_view)

    def handle_logout(self):
        confirm = QMessageBox.question(self, "Logout", "Are you sure you want to logout?",
                                     QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.logout_signal.emit()
            self.close()
