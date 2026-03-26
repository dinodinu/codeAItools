import sys
import subprocess
from PyQt5 import QtWidgets
from PyQt5.QtCore import QCoreApplication

class CaffeinateApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.caffeinate_process = None

    def start_caffeinate(self):
        """Start the caffeinate subprocess."""
        if self.caffeinate_process is None:
            self.caffeinate_process = subprocess.Popen(['caffeinate'])

    def _stop_caffeinate(self, terminate_process=True):
        """Stop the caffeinate subprocess. If terminate_process is False, the process is detached."""
        if self.caffeinate_process:
            if terminate_process:
                self.caffeinate_process.terminate()
                self.caffeinate_process = None
            else:
                # Detaching process, don't terminate it
                pass

    def closeEvent(self, event):
        """Override the close event to stop caffeinate on close."""
        self._stop_caffeinate(terminate_process=False)  # Detach caffeinate process upon closing
        event.accept()  # Accept the close event

if __name__ == '__main__':
    app = QCoreApplication(sys.argv)
    window = CaffeinateApp()
    window.show()
    sys.exit(app.exec_())