from PySide6 import QtWidgets, QtCore, QtGui, QtPrintSupport
from datetime import datetime

class InvoiceDialog(QtWidgets.QDialog):
    def __init__(self, invoice, parent=None):
        super().__init__(parent)
        self.invoice = invoice
        self.setWindowTitle(f"Invoice Preview - {invoice.invoice_no}")
        self.setMinimumSize(900, 800)
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header with branding color
        branding_box = QtWidgets.QFrame()
        branding_box.setStyleSheet("background-color: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;")
        branding_layout = QtWidgets.QHBoxLayout(branding_box)
        
        title_label = QtWidgets.QLabel("INVOICE PREVIEW")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000;")
        
        toolbar = QtWidgets.QHBoxLayout()
        self.btn_save = QtWidgets.QPushButton("  Save as PDF")
        self.btn_print = QtWidgets.QPushButton("  Print Invoice")
        self.btn_mark_paid = QtWidgets.QPushButton("  Mark as Paid")
        
        for btn in [self.btn_save, self.btn_print, self.btn_mark_paid]:
            btn.setMinimumHeight(42)
            btn.setCursor(QtCore.Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #8B5E3C;
                    color: white;
                    border-radius: 8px;
                    font-weight: bold;
                    border: none;
                    padding: 0 20px;
                }
                QPushButton:hover {
                    background-color: #734D31;
                }
            """)
            toolbar.addWidget(btn)
        
        self.btn_print.setStyleSheet(self.btn_save.styleSheet().replace("#8B5E3C", "#000000").replace("#734D31", "#333333"))
        self.btn_mark_paid.setStyleSheet(self.btn_save.styleSheet().replace("#8B5E3C", "#000000").replace("#734D31", "#333333"))
        
        # Hide "Mark as Paid" if already paid
        if self.invoice.status.upper() == 'PAID':
            self.btn_mark_paid.setVisible(False)
        
        branding_layout.addWidget(title_label)
        branding_layout.addStretch()
        branding_layout.addLayout(toolbar)
        layout.addWidget(branding_box)

        # Professional HTML View
        from PySide6.QtWidgets import QTextBrowser
        self.view = QTextBrowser()
        self.view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.view.setHtml(self.generate_invoice_html())
        self.view.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 10px; background: white; padding: 20px;")
        layout.addWidget(self.view)

        self.btn_save.clicked.connect(self.save_invoice)
        self.btn_print.clicked.connect(self.print_invoice)
        self.btn_mark_paid.clicked.connect(self.mark_as_paid)

    def generate_invoice_html(self):
        from datetime import timedelta
        import os
        import base64
        
        from database.models import CompanyProfile
        from datetime import datetime, date
        profile = CompanyProfile.get_or_none()
        daily_fee_rate = profile.daily_late_fee if profile else 0.0
        
        # Calculate Overdue Penalty
        today = date.today()
        days_overdue = 0
        penalty_amount = 0.0
        if self.invoice.status.upper() != "PAID" and self.invoice.due_date:
            if today > self.invoice.due_date:
                days_overdue = (today - self.invoice.due_date).days
                penalty_amount = days_overdue * daily_fee_rate
        
        final_total = self.invoice.grand_total + penalty_amount
        
        late_fee_html = ""
        if penalty_amount > 0:
            late_fee_html = f"""
            <tr>
                <td class="total-label" style="color: #ef4444;">Late Fee ({days_overdue} days)</td>
                <td class="total-val" style="color: #ef4444;">{penalty_amount:.2f}</td>
            </tr>
            """
            
        company_name = self.invoice.company_name or "TEXKNIT COLORS"
        
        # Build the detail labels
        gstin = self.invoice.company_gstin or ""
        phone = self.invoice.company_phone or ""
        email = self.invoice.company_email or ""
        
        logo_html = ""
        if self.invoice.company_logo_data:
            logo_html = f'<div class="logo-container"><img class="logo-img" src="{self.invoice.company_logo_data}"></div>'
        else:
            # Final fallback to CompanyProfile for very old invoices (should be rare now after lock script)
            from database.models import CompanyProfile
            profile = CompanyProfile.get_or_none()
            if profile and profile.logo_path and os.path.exists(profile.logo_path):
                try:
                    with open(profile.logo_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode()
                        logo_html = f'<div class="logo-container"><img class="logo-img" src="data:image/png;base64,{encoded_string}"></div>'
                except: pass
        
        items_html = ""
        for item in self.invoice.mrs.items:
            qty = item.quantity_issued if item.quantity_issued > 0 else item.quantity_requested
            items_html += f"""
                <tr>
                    <td align="center" style="padding: 12px 10px; font-weight: bold; font-size: 10pt; color: #1e293b;">{qty}</td>
                    <td style="padding: 12px 10px; font-size: 10pt; color: #1e293b;">{item.material.name}</td>
                    <td align="right" style="padding: 12px 10px; font-size: 10pt; color: #1e293b;">{item.material.unit_cost:.2f}</td>
                    <td align="right" style="padding: 12px 10px; font-size: 10pt; color: #1e293b;">{qty * item.material.unit_cost:.2f}</td>
                </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; color: #1e293b; margin: 0; padding: 0; background: #fff; }}
                .container {{ padding: 40px; padding-bottom: 100px; }}
                
                /* Header Layout */
                .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .company-name {{ font-size: 20pt; color: #1e293b; margin-bottom: 10px; font-weight: bold; }}
                .detail-text {{ font-size: 10pt; color: #475569; padding: 2px 0; }}
                
                .logo-box {{ 
                    width: 250px; 
                    height: 100px; 
                    text-align: right; 
                }}

                .title-section {{ text-align: center; margin: 20px 0; }}
                .invoice-title {{ font-size: 28pt; font-weight: bold; color: #1e293b; letter-spacing: 2px; }}
                
                /* Status Bar */
                .status-bg {{ 
                    width: 100%; 
                    background-color: #F8FAFC; 
                    padding: 8px 0; 
                    text-align: center; 
                    margin-bottom: 30px; 
                    border: 1px solid #E2E8F0;
                }}
                .status-text {{ 
                    font-weight: bold; 
                    font-size: 11pt; 
                    color: #475569; 
                    text-transform: uppercase; 
                }}
                .status-paid-bg {{ background-color: #F8FAFC; border-color: #1E293B; }}
                .status-paid-text {{ color: #000000; }}

                /* Info Boxes */
                .info-table {{ width: 100%; border-collapse: collapse; margin-bottom: 40px; }}
                .bill-to-label {{ font-weight: bold; font-size: 10pt; color: #334155; margin-bottom: 5px; }}
                .bill-to-val {{ font-size: 11pt; color: #1e293b; }}
                
                .meta-table {{ border-collapse: collapse; }}
                .meta-label {{ font-weight: bold; font-size: 10pt; color: #334155; text-align: right; padding: 3px 10px; }}
                .meta-val {{ font-size: 10pt; color: #1e293b; text-align: right; padding: 3px 0; }}

                /* Items Table */
                .items-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
                .items-table th {{ background-color: #334155; color: #ffffff; padding: 12px; font-size: 10pt; font-weight: bold; text-align: left; }}
                .items-table td {{ border-bottom: 1px solid #e2e8f0; padding: 12px; font-size: 10pt; color: #1e293b; }}
                
                /* Totals */
                .totals-wrap {{ width: 100%; }}
                .totals-table {{ border-collapse: collapse; margin-top: 10px; }}
                .total-label {{ font-weight: bold; font-size: 10pt; color: #475569; padding: 5px 10px; text-align: left; }}
                .total-val {{ font-weight: bold; font-size: 10pt; color: #1e293b; padding: 5px 0; text-align: right; width: 100px; }}
                .grand-total-row {{ border-top: 2px solid #1e293b; border-bottom: 2px solid #1e293b; }}
                .grand-total-text {{ font-size: 12pt; font-weight: 800; }}

                /* Footer */
                .footer-wrap {{ margin-top: 60px; border-top: 1px solid #e2e8f0; padding-top: 20px; }}
                .footer-head {{ font-weight: bold; font-size: 10pt; margin-bottom: 10px; }}
                .footer-body {{ font-size: 9pt; color: #64748b; line-height: 1.5; }}
                .machine-note {{ margin-top: 50px; text-align: center; font-size: 8pt; color: #94a3b8; font-style: italic; }}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Header -->
                <table class="header-table">
                    <tr>
                        <td width="65%" valign="top">
                            <div class="company-name">{company_name}</div>
                            <div class="detail-text"><b>GSTIN:</b> {gstin}</div>
                            <div class="detail-text"><b>Phone:</b> {phone}</div>
                            <div class="detail-text"><b>Email:</b> {email}</div>
                        </td>
                        <td width="35%" valign="top" align="right">
                             <div style="width: 250px; height: 120px; overflow: hidden; text-align: right;">
                                {logo_html.replace('class="logo-container"', 'style="display:block;"').replace('class="logo-img"', 'width="250" height="120" style="object-fit: contain;"')}
                             </div>
                        </td>
                    </tr>
                </table>

                <div class="title-section">
                    <div class="invoice-title">INVOICE</div>
                </div>

                <div class="status-bg {'status-paid-bg' if self.invoice.status.upper() == 'PAID' else ''}">
                    <span class="status-text {'status-paid-text' if self.invoice.status.upper() == 'PAID' else ''}">{self.invoice.status}</span>
                </div>

                <!-- Info Table -->
                <table class="info-table">
                    <tr>
                        <td width="60%" valign="top">
                            <div class="bill-to-label">Bill To</div>
                            <div class="bill-to-val"><b>{self.invoice.client_name or 'Walk-in Customer'}</b></div>
                            <div class="bill-to-val">{self.invoice.client_address or 'No address provided'}</div>
                            {f'<div class="bill-to-val">GSTIN: {self.invoice.client_gstin}</div>' if self.invoice.client_gstin else ''}
                            <div class="bill-to-val" style="margin-top: 10px; font-size: 9pt; color: #64748b;">Batch ID: {self.invoice.mrs.batch_id}</div>
                        </td>
                        <td width="40%" valign="top">
                            <table class="meta-table" align="right">
                                <tr>
                                    <td class="meta-label">Invoice #</td>
                                    <td class="meta-val">{self.invoice.invoice_no.split('-')[-1]}</td>
                                </tr>
                                <tr>
                                    <td class="meta-label">Date</td>
                                    <td class="meta-val">{self.invoice.created_at.strftime('%d-%m-%Y')}</td>
                                </tr>
                                <tr>
                                    <td class="meta-label">Due Date</td>
                                    <td class="meta-val">{self.invoice.due_date.strftime('%d-%m-%Y') if self.invoice.due_date else 'N/A'}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>

                <!-- Items -->
                <table class="items-table">
                    <thead>
                        <tr>
                            <th width="10%" style="text-align: center;">QTY</th>
                            <th width="50%">DESCRIPTION</th>
                            <th width="20%" style="text-align: right;">PRICE</th>
                            <th width="20%" style="text-align: right;">AMOUNT</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>

                <!-- Totals -->
                <table width="100%">
                    <tr>
                        <td width="60%"></td>
                        <td width="40%" align="right">
                            <table class="totals-table">
                                <tr>
                                    <td class="total-label">Subtotal</td>
                                    <td class="total-val">{self.invoice.total_amount:.2f}</td>
                                </tr>
                                <tr>
                                    <td class="total-label">Sales Tax ({self.invoice.gst_percentage:.1f}%)</td>
                                    <td class="total-val">{self.invoice.tax_amount:.2f}</td>
                                </tr>
                                {late_fee_html}
                                <tr class="grand-total-row">
                                    <td class="total-label grand-total-text">Total (INR)</td>
                                    <td class="total-val grand-total-text">₹{final_total:.2f}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>

                <!-- Footer -->
                <div class="footer-wrap">
                    <div class="footer-head">Terms and Conditions</div>
                    <div class="footer-body">
                        Payment is due by <b>{self.invoice.due_date.strftime('%d-%m-%Y') if self.invoice.due_date else 'N/A'}</b>.<br>
                        Please make payments to: <b>{company_name}</b>
                    </div>
                    <div class="machine-note">
                        This is a computer-generated invoice and does not require a physical signature.
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html


    def save_invoice(self):
        try:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Invoice", f"{self.invoice.invoice_no}.pdf", "PDF Files (*.pdf)"
            )
            if not path: return

            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.ScreenResolution)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setOutputFileName(path)
            printer.setPageMargins(QtCore.QMarginsF(10, 10, 10, 10), QtGui.QPageLayout.Millimeter)
            
            doc = QtGui.QTextDocument()
            doc.setHtml(self.generate_invoice_html())
            doc.print_(printer)
            
            QtWidgets.QMessageBox.information(self, "Success", f"Invoice saved successfully:\n{path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Could not save PDF: {str(e)}")

    def print_invoice(self):
        try:
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.ScreenResolution)
            dialog = QtPrintSupport.QPrintDialog(printer, self)
            if dialog.exec():
                doc = QtGui.QTextDocument()
                doc.setHtml(self.generate_invoice_html())
                doc.print_(printer)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Print failed: {str(e)}")


    def mark_as_paid(self):
        from services.invoice_service import InvoiceService
        from services.communication_service import relay
        from PySide6.QtWidgets import QMessageBox
        
        confirm = QMessageBox.question(self, "Confirm Payment", 
                                     f"Are you sure you want to mark Invoice {self.invoice.invoice_no} as PAID?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if confirm == QMessageBox.Yes:
            InvoiceService.update_invoice_status(self.invoice.id, 'PAID')
            self.invoice.status = 'PAID'
            self.btn_mark_paid.setVisible(False)
            self.view.setHtml(self.generate_invoice_html())
            relay.data_changed.emit()
            QMessageBox.information(self, "Success", "Invoice marked as PAID.")
