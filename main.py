import sys
from PySide6.QtWidgets import QApplication
from database.models import initialize_db
from ui.login_view import LoginView
from ui.main_window import MainWindow
from services.auth_service import AuthService
from utils.logger import global_exception_handler, app_logger
from utils.backup_service import BackupService

class ConsultancyApp:
    def __init__(self):
        # Setup global exception handler for crash reporting
        sys.excepthook = global_exception_handler
        
        self.app = QApplication(sys.argv)
        self.auth_service = AuthService()
        self.main_window = None
        
        # Initialize Database
        initialize_db()
        
        # Trigger automated backup on startup
        app_logger.info("Application starting - running backup protocol")
        BackupService.create_database_backup()
        
        # Show Login
        self.show_login()

    def show_login(self):
        self.login_window = LoginView()
        self.login_window.btn_login.clicked.connect(self.handle_login)
        # Allow Enter key to submit login
        self.login_window.password.returnPressed.connect(self.handle_login)
        self.login_window.username.returnPressed.connect(lambda: self.login_window.password.setFocus())
        self.login_window.show()

    def handle_login(self):
        username = self.login_window.username.text().strip()
        password = self.login_window.password.text()
        
        if not username:
            self.login_window.set_error("Username is required.")
            return
        if not password:
            self.login_window.set_error("Password is required.")
            return
        
        user = self.auth_service.login(username, password)
        if user:
            self.login_window.close()
            self.show_main_window(user)
        else:
            self.login_window.set_error("Invalid username or password.")

    def show_main_window(self, user):
        self.main_window = MainWindow(user)
        self.main_window.logout_signal.connect(self.handle_logout)
        self.main_window.show()

    def handle_logout(self):
        """Return to login screen instead of quitting."""
        self.auth_service.logout()
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        self.show_login()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = ConsultancyApp()
    app.run()
