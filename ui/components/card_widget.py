from PySide6.QtWidgets import QFrame, QVBoxLayout
from PySide6.QtCore import Qt

class CardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setProperty("class", "Card")
        # Base styling moved to CSS for robustness, but keeping here as fallback
        self.setStyleSheet("#Card { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; }")
        
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(24, 24, 24, 24)
        self.card_layout.setSpacing(12)
        self.layout = self.card_layout # Maintain compatibility

    def addWidget(self, widget, stretch=0, alignment=Qt.Alignment()):
        self.layout.addWidget(widget, stretch, alignment)

    def addLayout(self, layout, stretch=0):
        self.layout.addLayout(layout, stretch)
        
    def add_centered_widget(self, widget):
        """Utility to add a widget that is centered both ways."""
        self.layout.addStretch()
        self.layout.addWidget(widget, 0, Qt.AlignCenter)
        self.layout.addStretch()
