from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QStackedWidget, QLabel, QFrame, QMessageBox, QApplication)
from PySide6.QtCore import Qt, Signal

from ui.inventory_management import InventoryManagementView
from ui.mrs_workflow import MRSWorkflowView
from ui.procurement_manager import ProcurementManagerView
from ui.analytics_view import AnalyticsView
from ui.supplier_management import SupplierManagementView

class MainWindow(QMainWindow):
    logout_signal = Signal()  # Signal to return to login screen
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.setWindowTitle("TEXKNIT COLORS - Management System")
        self.resize(1200, 850)
        
        # Load Styles
        with open("ui/styles.qss", "r") as f:
            self.setStyleSheet(f.read())
            
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 40, 0, 40)
        
        # App Title in Sidebar
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
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
        sidebar_layout.addSpacing(40)
        
        # Navigation Buttons
        self.nav_buttons = []
        
        self.btn_dashboard = self.create_nav_btn("  Command Center")
        self.btn_dashboard.setChecked(True)
        self.nav_buttons.append(self.btn_dashboard)
        
        self.btn_inventory = self.create_nav_btn("  Inventory")
        self.nav_buttons.append(self.btn_inventory)
        
        self.btn_mrs = self.create_nav_btn("  Invoices")
        self.nav_buttons.append(self.btn_mrs)
        
        self.btn_consumers = self.create_nav_btn("  Consumers")
        self.nav_buttons.append(self.btn_consumers)
        
        self.btn_suppliers = self.create_nav_btn("  Suppliers")
        self.nav_buttons.append(self.btn_suppliers)
        
        self.btn_procurement = self.create_nav_btn("  Procurement")
        self.nav_buttons.append(self.btn_procurement)
        
        for btn in self.nav_buttons:
            sidebar_layout.addWidget(btn)
            btn.clicked.connect(self.handle_nav_click)
            
        sidebar_layout.addStretch()
        
        # User Info & Actions at Bottom
        user_container = QFrame()
        user_container.setObjectName("UserCard")
        user_container.setStyleSheet("""
            #UserCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                margin: 12px;
                border: 1px solid rgba(0, 0, 0, 0.05);
            }
        """)
        
        user_main_layout = QVBoxLayout(user_container)
        user_main_layout.setContentsMargins(12, 12, 12, 12)
        user_main_layout.setSpacing(12)
        
        # Identity Row (Avatar + Text)
        identity_row = QHBoxLayout()
        identity_row.setSpacing(10)
        
        avatar = QLabel(self.user.username[0].upper())
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet("""
            background-color: #FDFBF7;
            color: #8B5E3C;
            border-radius: 18px;
            font-weight: 800;
            font-size: 14px;
            border: 1px solid rgba(139, 94, 60, 0.2);
        """)
        
        info_vbox = QVBoxLayout()
        info_vbox.setSpacing(1)
        user_name = QLabel(self.user.username.upper())
        user_name.setStyleSheet("color: #1E293B; font-weight: 800; font-size: 13px;")
        user_role = QLabel(self.user.role)
        user_role.setStyleSheet("color: #8B5E3C; font-weight: 700; font-size: 10px; text-transform: uppercase; letter-spacing: 0.8px;")
        
        info_vbox.addWidget(user_name)
        info_vbox.addWidget(user_role)
        info_vbox.addStretch()
        
        identity_row.addWidget(avatar)
        identity_row.addLayout(info_vbox)
        identity_row.addStretch()
        
        user_main_layout.addLayout(identity_row)
        
        # Actions Row
        actions_row = QHBoxLayout()
        actions_row.setSpacing(8)
        
        self.btn_profile = QPushButton("View Profile")
        self.btn_profile.setCursor(Qt.PointingHandCursor)
        self.btn_profile.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC;
                color: #475569;
                border-radius: 8px;
                padding: 6px 0px;
                font-size: 10px;
                font-weight: 700;
                border: 1px solid #E2E8F0;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                color: #1E293B;
                border-color: #CBD5E1;
            }
        """)
        self.btn_profile.clicked.connect(self.show_profile)
        
        self.btn_logout = QPushButton("Logout")
        self.btn_logout.setCursor(Qt.PointingHandCursor)
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #FFF1F2;
                color: #E11D48;
                border-radius: 8px;
                padding: 6px 0px;
                font-size: 10px;
                font-weight: 700;
                border: 1px solid #FECDD3;
            }
            QPushButton:hover {
                background-color: #FFE4E6;
                color: #BE123C;
                border-color: #FDA4AF;
            }
        """)
        self.btn_logout.clicked.connect(self.handle_logout)
        
        actions_row.addWidget(self.btn_profile, 1)
        actions_row.addWidget(self.btn_logout, 1)
        user_main_layout.addLayout(actions_row)
        
        sidebar_layout.addWidget(user_container)
        
        main_layout.addWidget(self.sidebar)
        
        # Content Layer
        content_layer = QWidget()
        content_layer.setObjectName("ContentArea")
        cl_layout = QVBoxLayout(content_layer)
        cl_layout.setContentsMargins(0, 0, 0, 0)
        
        # Content Area (Stacked Widget)
        self.content_stack = QStackedWidget()
        
        # Pages
        self.dashboard_view = AnalyticsView()
        self.inventory_view = InventoryManagementView()
        self.mrs_view = MRSWorkflowView(self.user)
        from ui.consumer_management import ConsumerManagementView
        self.consumers_view = ConsumerManagementView(self.user)
        self.suppliers_view = SupplierManagementView()
        self.procurement_view = ProcurementManagerView(self.user)
        from ui.profile_view import ProfileView
        self.profile_view = ProfileView()
        
        self.content_stack.addWidget(self.dashboard_view)
        self.content_stack.addWidget(self.inventory_view)
        self.content_stack.addWidget(self.mrs_view)
        self.content_stack.addWidget(self.consumers_view)
        self.content_stack.addWidget(self.suppliers_view)
        self.content_stack.addWidget(self.procurement_view)
        self.content_stack.addWidget(self.profile_view)
        
        cl_layout.addWidget(self.content_stack)
        main_layout.addWidget(content_layer)

    def create_nav_btn(self, text):
        btn = QPushButton(text)
        btn.setCheckable(True)
        return btn
        
    def handle_nav_click(self):
        btn = self.sender()
        # Uncheck others
        for b in self.nav_buttons:
            if b != btn: b.setChecked(False)
        btn.setChecked(True)
            
        index = self.nav_buttons.index(btn)
        self.content_stack.setCurrentIndex(index)

    def show_profile(self):
        # Uncheck all nav buttons
        for b in self.nav_buttons:
            b.setChecked(False)
        # Assuming ProfileView is the last widget added before admin_view
        self.content_stack.setCurrentWidget(self.profile_view)

    def handle_logout(self):
        confirm = QMessageBox.question(self, "Logout", "Are you sure you want to logout?", 
                                     QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            self.logout_signal.emit()
            self.close()
