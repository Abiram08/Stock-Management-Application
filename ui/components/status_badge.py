from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt

class StatusBadge(QLabel):
    def __init__(self, text, status='neutral', parent=None):
        super().__init__(text, parent)
        self.set_status(status)
        self.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(8, 4, 8, 4)
        self.setFixedHeight(24)

    def set_status(self, status):
        # status: success, warning, critical, neutral
        # Tailored for Beige/Light theme
        styles = {
            'success': "background-color: #EFF6FF; color: #734D31; border-radius: 12px; font-size: 11px; font-weight: 700; padding: 4px 12px; border: 1px solid #BFDBFE;",
            'warning': "background-color: #F8FAFC; color: #000000; border-radius: 12px; font-size: 11px; font-weight: 700; padding: 4px 12px; border: 1px solid #CBD5E1;",
            'critical': "background-color: #000000; color: #FFFFFF; border-radius: 12px; font-size: 11px; font-weight: 700; padding: 4px 12px; border: 1px solid #000000;",
            'neutral': "background-color: #F1F5F9; color: #475569; border-radius: 12px; font-size: 11px; font-weight: 700; padding: 4px 12px; border: 1px solid #E2E8F0;"
        }
        self.setStyleSheet(styles.get(status, styles['neutral']))
