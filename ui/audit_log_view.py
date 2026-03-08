from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QComboBox, QDateEdit, QPushButton, QFrame,
                             QScrollArea)
from PySide6.QtCore import Qt, QDate
from services.audit_service import AuditService
from utils.export_service import ExportService
from utils.async_worker import QueryWorker
from services.auth_service import AuthService
from ui.components.status_badge import StatusBadge
import json


class AuditLogView(QWidget):
    """Premium view for viewing system audit logs with pill badges and modern layout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Header Section
        header_row = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        title = QLabel("AUDIT INTELLIGENCE")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #1e293b; letter-spacing: 0.5px;")
        subtitle = QLabel("Comprehensive traceability for compliance and security")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 500;")
        header_text_layout.addWidget(title)
        header_text_layout.addWidget(subtitle)
        header_row.addLayout(header_text_layout)
        header_row.addStretch()
        
        # Stats Cards in Header
        self.total_card = self._create_stat_card("Total Events", "0", "indigo")
        self.today_card = self._create_stat_card("Today", "0", "emerald")
        self.users_card = self._create_stat_card("Active Users", "0", "amber")
        header_row.addWidget(self.total_card)
        header_row.addWidget(self.today_card)
        header_row.addWidget(self.users_card)
        layout.addLayout(header_row)

        # Filters Bar (Glassmorphism inspired)
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: none;
                border-radius: 12px;
            }
        """)
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(20, 16, 20, 16)
        filter_layout.setSpacing(16)

        # Filter widgets with labels above
        def add_filter_group(label_text, widget):
            vbox = QVBoxLayout()
            vbox.setSpacing(6) # Increased for better label breathing room
            lbl = QLabel(label_text.upper())
            lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748b; letter-spacing: 0.5px; padding-left: 2px;")
            vbox.addWidget(lbl)
            vbox.addWidget(widget)
            widget.setFixedHeight(38)
            filter_layout.addLayout(vbox)

        self.action_filter = QComboBox()
        self.action_filter.addItem("ALL")
        self.action_filter.setMinimumWidth(180)
        self.action_filter.setMinimumHeight(38)
        add_filter_group("Filter Action", self.action_filter)

        self.user_filter = QComboBox()
        self.user_filter.addItem("ALL")
        self.user_filter.setMinimumWidth(150)
        self.user_filter.setMinimumHeight(38)
        add_filter_group("Performed By", self.user_filter)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setMinimumHeight(38)
        add_filter_group("From Date", self.date_from)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setMinimumHeight(38)
        add_filter_group("To Date", self.date_to)

        btn_apply = QPushButton("REFRESH TRAIL")
        btn_apply.setProperty("class", "PrimaryButton")
        btn_apply.setCursor(Qt.PointingHandCursor)
        btn_apply.setFixedHeight(38)
        btn_apply.setFixedWidth(140)
        btn_apply.clicked.connect(self.load_data)
        
        btn_export = QPushButton("⬇ EXPORT")
        btn_export.setProperty("class", "SecondaryButton")
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.setFixedHeight(38)
        btn_export.setFixedWidth(100)
        btn_export.clicked.connect(lambda: ExportService.export_table_to_csv(self.table, self, "audit_logs.csv"))
        
        btn_vbox = QVBoxLayout()
        btn_vbox.setContentsMargins(0, 18, 0, 0)
        
        btn_hbox = QHBoxLayout()
        btn_hbox.addWidget(btn_apply)
        btn_hbox.addWidget(btn_export)
        
        btn_vbox.addLayout(btn_hbox)
        filter_layout.addLayout(btn_vbox)

        layout.addWidget(filter_frame)

        # Modern Table for Logs
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["TIMESTAMP", "IDENTITY", "SYSTEM ACTION", "EVENT PAYLOAD"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.table.setColumnWidth(0, 160)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 140)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.table.setColumnWidth(2, 170)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                border: none;
                border-radius: 12px;
                background-color: white;
                gridline-color: #f1f5f9;
            }
            QTableWidget::item { padding: 12px; }
            QHeaderView::section {
                background-color: #f8fafc;
                padding: 12px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                color: #475569;
                font-weight: 800;
                font-size: 10px;
                letter-spacing: 0.5px;
            }
        """)
        layout.addWidget(self.table)

        # Context Menu
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        self._populate_filters()


    def _create_stat_card(self, title, value, accent_color='indigo'):
        colors = {
            'indigo': '#6366f1',
            'emerald': '#10b981',
            'amber': '#f59e0b',
        }
        accent = colors.get(accent_color, '#6366f1')
        
        card = QFrame()
        card.setFixedSize(140, 75)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #ffffff;
                border: none;
                border-radius: 12px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(2)

        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet("font-size: 9px; font-weight: 800; color: #64748b; letter-spacing: 0.5px;")
        card_layout.addWidget(lbl_title)

        lbl_value = QLabel(value)
        lbl_value.setObjectName(f"stat_{title.lower().replace(' ', '_')}")
        lbl_value.setStyleSheet(f"font-size: 24px; font-weight: 900; color: {accent};")
        card_layout.addWidget(lbl_value, 0, Qt.AlignBottom)

        return card

    def _populate_filters(self):
        try:
            actions = AuditService.get_action_types()
            for action in actions:
                self.action_filter.addItem(action)
            users = AuthService.get_all_users()
            for user in users:
                self.user_filter.addItem(user.username)
        except Exception:
            pass

    def load_data(self):
        self.table.setRowCount(0)
        
        action = self.action_filter.currentText()
        user = self.user_filter.currentText()
        date_from = self.date_from.date().toPython()
        date_to = self.date_to.date().toPython()
        
        self.worker = QueryWorker(
            AuditService.get_logs,
            action_filter=action,
            user_filter=user,
            date_from=date_from,
            date_to=date_to
        )
        self.worker.finished.connect(self._on_data_loaded)
        self.worker.error.connect(self._on_data_error)
        self.worker.start()

    def _on_data_error(self, err_msg):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Data Load Error", f"Failed to load logs:\n{err_msg}")

    def _on_data_loaded(self, logs):
        self.table.setRowCount(len(logs))
        today_count = 0
        user_set = set()

        for i, log in enumerate(logs):
            self.table.setRowHeight(i, 52)

            # Timestamp
            ts = log.timestamp.strftime("%d %b, %H:%M") if log.timestamp else "—"
            ts_item = QTableWidgetItem(ts)
            ts_item.setForeground(Qt.gray)
            self.table.setItem(i, 0, ts_item)

            # User
            username = log.user.username if log.user else "SYSTEM"
            user_item = QTableWidgetItem(f"@{username.lower()}")
            user_item.setFont(__import__('PySide6.QtGui').QtGui.QFont("Courier", 9, weight=700))
            self.table.setItem(i, 1, user_item)
            user_set.add(username)

            # Action (Pill Badge)
            action_text = log.action.replace('_', ' ').title()
            status = 'neutral'
            if any(k in log.action for k in ['DELETE', 'REJECTED', 'INSUFFICIENT']):
                status = 'critical'
            elif any(k in log.action for k in ['CREATE', 'APPROVED', 'INWARD', 'PAID']):
                status = 'success'
            elif any(k in log.action for k in ['UPDATE', 'ISSUE']):
                status = 'warning'
            
            badge = StatusBadge(action_text, status)
            self.table.setCellWidget(i, 2, badge)

            # Details
            details_text = "—"
            if log.details:
                try:
                    d = json.loads(log.details) if isinstance(log.details, str) else log.details
                    details_text = ", ".join(f"{k}: {v}" for k, v in d.items())
                except:
                    details_text = str(log.details)
            
            det_item = QTableWidgetItem(details_text)
            det_item.setToolTip(details_text)
            self.table.setItem(i, 3, det_item)

            if log.timestamp and log.timestamp.date() == __import__('datetime').date.today():
                today_count += 1

        # Push updates to labels (manual search to avoid id conflicts)
        self._update_stat_label("stat_total_events", str(len(logs)))
        self._update_stat_label("stat_today", str(today_count))
        self._update_stat_label("stat_active_users", str(len(user_set)))

    def _update_stat_label(self, object_name, text):
        label = self.findChild(QLabel, object_name)
        if label:
            label.setText(text)

    def show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 4px; }
            QMenu::item { padding: 8px 24px; border-radius: 4px; color: #1e293b; font-size: 11px; font-weight: 500; }
            QMenu::item:selected { background-color: #f1f5f9; color: #6366f1; }
        """)
        
        act_copy = menu.addAction("Copy Payload Info")
        act_details = menu.addAction("View Event JSON")
        
        action = menu.exec(self.table.mapToGlobal(pos))
        
        if action == act_copy:
            payload_item = self.table.item(item.row(), 3)
            if payload_item:
                QApplication.clipboard().setText(payload_item.text())
        elif action == act_details:
            payload_item = self.table.item(item.row(), 3)
            if payload_item:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Event Payload", payload_item.text())

