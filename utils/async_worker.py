from PySide6.QtCore import QThread, Signal
from utils.logger import app_logger

class QueryWorker(QThread):
    """
    A generic QThread worker that executes a function in the background
    and emits the result or an error message back to the main UI thread.
    """
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            app_logger.error(f"Background Query Failed: {str(e)}")
            self.error.emit(str(e))
