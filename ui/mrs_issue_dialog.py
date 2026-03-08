from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QScrollArea, QWidget, QFrame)
from PySide6.QtCore import Qt
from pathlib import Path
class MRSIssueDialog(QDialog):
    def __init__(self, mrs, parent=None):
        super().__init__(parent)
        self.mrs = mrs
        self.setWindowTitle(f"Issue Materials - {mrs.batch_id}")
        self.resize(500, 400)
        
        # Result data
        self.issue_items = []
        
        # Load Styles
        styles_path = Path(__file__).parent / "styles.qss"
        with open(styles_path, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())
            
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel(f"Processing Batch: {self.mrs.batch_id}")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content = QWidget()
        self.items_layout = QVBoxLayout(content)
        
        self.inputs = {}
        
        for item in self.mrs.items:
            pending = item.quantity_requested - item.quantity_issued
            if pending <= 0: continue
            
            item_frame = QFrame()
            item_frame.setObjectName("Card")
            item_layout = QVBoxLayout(item_frame)
            
            name = QLabel(f"{item.material.name}")
            name.setStyleSheet("font-weight: bold;")
            stock = QLabel(f"Current Stock: {item.material.quantity} {item.material.unit} | Pending: {pending}")
            stock.setStyleSheet("font-size: 11px; color: #94a3b8;")
            
            input_box = QLineEdit()
            input_box.setPlaceholderText("Enter quantity to issue")
            input_box.setText(str(min(pending, item.material.quantity)))
            self.inputs[item.material.id] = input_box
            
            item_layout.addWidget(name)
            item_layout.addWidget(stock)
            item_layout.addWidget(input_box)
            
            self.items_layout.addWidget(item_frame)
            
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_confirm = QPushButton("Confirm Issue")
        btn_confirm.setProperty("class", "PrimaryButton")
        btn_confirm.clicked.connect(self.collect_data)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_confirm)
        layout.addLayout(btn_layout)

    def collect_data(self):
        for mid, input_box in self.inputs.items():
            try:
                val = float(input_box.text())
                if val > 0:
                    self.issue_items.append({
                        'material_id': mid,
                        'quantity_issued': val
                    })
            except ValueError:
                pass
        self.accept()
