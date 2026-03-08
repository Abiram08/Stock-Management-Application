from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                             QPushButton, QFrame, QHBoxLayout)
from PySide6.QtCore import Qt, Signal
from pathlib import Path


class LoginView(QWidget):
    login_success = Signal(object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login — TEXKNIT COLORS")
        self.resize(460, 560)

        # Load Styles
        styles_path = Path(__file__).parent / "styles.qss"
        with open(styles_path, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

        self.setStyleSheet(self.styleSheet() + """
            LoginView {
                background: #000000;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Card
        card = QFrame()
        card.setFixedSize(400, 480)
        card.setObjectName("LoginCard")
        card.setStyleSheet("""
            #LoginCard {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 44, 40, 40)
        card_layout.setSpacing(8)

        # Logo / Brand
        brand_icon = QLabel("◆")
        brand_icon.setAlignment(Qt.AlignCenter)
        brand_icon.setStyleSheet("font-size: 32px; color: #8B5E3C; margin-bottom: 4px;")

        title = QLabel("Welcome Back")
        title.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A;")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("TEXKNIT COLORS MANAGEMENT")
        subtitle.setStyleSheet("font-size: 10px; font-weight: 800; color: #8B5E3C; letter-spacing: 2px; text-transform: uppercase;")
        subtitle.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(brand_icon)
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(24)

        # Form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(14)

        lbl_user = QLabel("USERNAME")
        lbl_user.setStyleSheet("font-size: 10px; font-weight: 800; color: #475569; letter-spacing: 1px;")
        form_layout.addWidget(lbl_user)

        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter your username")
        self.username.setMinimumHeight(44)
        form_layout.addWidget(self.username)

        lbl_pass = QLabel("PASSWORD")
        lbl_pass.setStyleSheet("font-size: 10px; font-weight: 800; color: #475569; letter-spacing: 1px;")
        form_layout.addWidget(lbl_pass)

        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter your password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(44)
        form_layout.addWidget(self.password)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #EF4444; font-size: 11px; font-weight: 700;")
        self.error_label.setAlignment(Qt.AlignCenter)
        form_layout.addWidget(self.error_label)

        form_layout.addSpacing(8)

        self.btn_login = QPushButton("Sign In")
        self.btn_login.setProperty("class", "PrimaryButton")
        self.btn_login.setCursor(Qt.PointingHandCursor)
        self.btn_login.setMinimumHeight(46)
        self.btn_login.setStyleSheet("""
            QPushButton {
                background-color: #8B5E3C;
                color: #FFFFFF;
                border-radius: 10px;
                font-weight: 800;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #734D31;
            }
            QPushButton:pressed {
                background-color: #000000;
            }
        """)
        form_layout.addWidget(self.btn_login)

        card_layout.addLayout(form_layout)
        card_layout.addStretch()

        # Footer
        footer = QLabel("© 2026 Texknit Colors. All rights reserved.")
        footer.setStyleSheet("font-size: 10px; color: #94A3B8;")
        footer.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(footer)

        layout.addWidget(card)

    def set_error(self, message):
        self.error_label.setText(message)
