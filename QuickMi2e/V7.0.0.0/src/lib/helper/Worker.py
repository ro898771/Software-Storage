"""Worker thread for progress bar operations."""

from PySide6.QtCore import QThread, Signal


class ProgressBarWorker(QThread):
    """Worker thread for managing progress bar updates."""

    # Define signals
    progress_updated = Signal(int)  # Emits current progress value (0-100)
    finished_message = Signal(str)  # Emits final completion message
    normal_updated = Signal()  # Emits normal update signal

    def __init__(self, message, parent=None):
        """
        Initialize the progress bar worker.

        Args:
            message: Completion message to display
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        self.message = message

    def run(self):
        """Execute the worker thread task."""
        try:
            for x in range(101):
                # Simulate work being done
                self.msleep(10)  # Sleep for 10 milliseconds

                # Emit the signal to update the progress bar
                self.progress_updated.emit(x)

            # Once complete, emit the final message
            self.finished_message.emit(f"\n{self.message}")

        except Exception as e:
            # Handle error appropriately
            print(f"Error in worker thread: {e}")