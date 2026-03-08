import logging
import logging.handlers
import sys
from pathlib import Path
from PySide6.QtWidgets import QMessageBox

def setup_logger():
    # Create logs directory
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "app.log"
    
    logger = logging.getLogger("AppLogger")
    logger.setLevel(logging.INFO)
    
    # 5 MB per file, keep 3 backups
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    # Avoid adding multiple handlers if setup is called multiple times
    if not logger.handlers:
        logger.addHandler(handler)
        
    return logger

app_logger = setup_logger()

def global_exception_handler(exctype, value, tb):
    import traceback
    
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    app_logger.critical(f"Uncaught exception:\n{error_msg}")
    
    # Show user-friendly error dialog
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Critical)
    msg_box.setWindowTitle("Application Error")
    msg_box.setText("An unexpected error occurred.")
    msg_box.setInformativeText("The application encountered a critical error. The error details have been logged.")
    msg_box.setDetailedText(error_msg)
    msg_box.exec()
    
    # Still call the default sys handler
    sys.__excepthook__(exctype, value, tb)
