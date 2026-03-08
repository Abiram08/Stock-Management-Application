import csv
from PySide6.QtWidgets import QFileDialog, QMessageBox
from utils.logger import app_logger

class ExportService:
    @staticmethod
    def export_table_to_csv(table_widget, parent_window, default_filename="export.csv"):
        """Exports a QTableWidget's contents to a CSV file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                parent_window,
                "Export to CSV",
                default_filename,
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return False
                
            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write headers
                headers = []
                for column in range(table_widget.columnCount()):
                    # Skip 'Actions' column globally if present
                    header_item = table_widget.horizontalHeaderItem(column)
                    header_text = header_item.text() if header_item else f"Column {column+1}"
                    if header_text.upper() == "ACTIONS":
                        continue
                        
                    headers.append(header_text)
                writer.writerow(headers)
                
                # Write rows
                for row in range(table_widget.rowCount()):
                    row_data = []
                    for column in range(table_widget.columnCount()):
                        header_item = table_widget.horizontalHeaderItem(column)
                        if header_item and header_item.text().upper() == "ACTIONS":
                            continue
                            
                        item = table_widget.item(row, column)
                        if item is not None:
                            # Standard text item
                            row_data.append(item.text().replace("\n", " - "))
                        else:
                            # Widget cell (e.g., StatusBadge or Custom View)
                            cell_widget = table_widget.cellWidget(row, column)
                            if cell_widget:
                                # StatusBadge or child QLabel extraction
                                extracted_text = ExportService._extract_text_from_widget(cell_widget)
                                row_data.append(extracted_text)
                            else:
                                row_data.append("")
                    writer.writerow(row_data)
                    
            app_logger.info(f"Successfully exported table to {file_path}")
            QMessageBox.information(parent_window, "Export Successful", f"Data successfully exported to:\n{file_path}")
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to export CSV: {str(e)}")
            QMessageBox.critical(parent_window, "Export Error", f"Failed to export data:\n{str(e)}")
            return False

    @staticmethod
    def _extract_text_from_widget(widget):
        """Recursively attempts to extract meaningful text from a compound widget."""
        from PySide6.QtWidgets import QLabel
        from ui.components.status_badge import StatusBadge
        
        # Check if direct match
        if isinstance(widget, StatusBadge):
            return widget.label.text()
        if isinstance(widget, QLabel):
            return widget.text().replace("\n", " - ")
            
        # Check children
        texts = []
        for child in widget.findChildren(QLabel):
            txt = child.text().strip()
            # Ignored styled code labels or empty
            if txt and len(txt) > 0 and not txt.startswith("●"):
                texts.append(txt)
                
        if texts:
            # e.g., "Dye A - Unit Cost: $10"
            return " | ".join(texts)
            
        return "N/A"
