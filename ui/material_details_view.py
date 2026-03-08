from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QFrame)
from PySide6.QtCore import Qt
from pathlib import Path
from services.inventory_service import InventoryService
from ui.components.status_badge import StatusBadge

class MaterialDetailsDialog(QDialog):
    def __init__(self, material_id, parent=None):
        super().__init__(parent)
        self.material_id = material_id
        self.setWindowTitle("Material Details - Stock Card")
        self.resize(800, 600)
        
        # Load Styles
        styles_path = Path(__file__).parent / "styles.qss"
        with open(styles_path, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())
            
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # Header Section
        self.header_card = QFrame()
        self.header_card.setObjectName("Card")
        header_layout = QVBoxLayout(self.header_card)
        
        self.name_label = QLabel("Loading...")
        self.name_label.setObjectName("TitleLabel")
        
        self.unit_info = QLabel("")
        self.unit_info.setObjectName("SubtitleLabel")
        
        header_layout.addWidget(self.name_label)
        header_layout.addWidget(self.unit_info)
        self.layout.addWidget(self.header_card)
        
        # History Table
        table_title = QLabel("Transaction History (Stock Card)")
        table_title.setStyleSheet("font-weight: bold; font-size: 16px; margin-top: 10px;")
        self.layout.addWidget(table_title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date/Time", "Type", "Performed By", "Quantity"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.layout.addWidget(self.table)
        
        # Close Button
        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "SecondaryButton")
        btn_close.clicked.connect(self.accept)
        self.layout.addWidget(btn_close, alignment=Qt.AlignRight)

    def load_data(self):
        material = InventoryService.get_material_details(self.material_id)
        if material:
            self.name_label.setText(material.name)
            self.unit_info.setText(f"Unit: {material.unit} | Current Quantity: {material.quantity}")
            
            transactions = InventoryService.get_transaction_history(self.material_id)
            self.table.setRowCount(len(transactions))
            
            for i, tx in enumerate(transactions):
                # Date
                self.table.setItem(i, 0, QTableWidgetItem(tx.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
                
                # Type (Badge)
                type_badge = StatusBadge(tx.type, 'success' if tx.type == 'INWARD' else 'critical' if tx.type == 'ISSUE' else 'neutral')
                self.table.setCellWidget(i, 1, type_badge)
                
                # Performed By
                self.table.setItem(i, 2, QTableWidgetItem(tx.performed_by.username))
                
                # Quantity
                qty_str = f"{'+' if tx.quantity > 0 else ''}{tx.quantity}"
                qty_item = QTableWidgetItem(qty_str)
                qty_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                qty_item.setForeground(Qt.darkGreen if tx.quantity > 0 else Qt.darkRed)
                self.table.setItem(i, 3, qty_item)
