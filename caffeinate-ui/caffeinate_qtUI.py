def _stop_caffeinate(self, terminate_process=False):
    if terminate_process:
        # Code to terminate the caffeinate process
        pass
    else:
        # Code to detach the caffeinate process
        pass


def closeEvent(self, event):
    # Call the modified _stop_caffeinate method
    self._stop_caffeinate(terminate_process=False)
    event.accept()  # Accept the event to close the UI