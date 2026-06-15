import os
import sys
import uuid
from threading import Thread

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
)
from werkzeug.serving import make_server

os.environ.setdefault("DUMMY_API_BASE", "http://127.0.0.1:5001/api")

from dummy_customer_api import app as api_app
from agent import run_agent


class ApiThread(Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.server = make_server("127.0.0.1", 5001, api_app)

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


class Worker(QThread):
    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, text: str, config: dict):
        super().__init__()
        self.text = text
        self.config = config

    def run(self):
        try:
            self.done.emit(run_agent(self.text, self.config))
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.config = {"configurable": {"thread_id": str(uuid.uuid4())}}
        self.worker = None

        self.setWindowTitle("Order Agent")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        layout.addWidget(self.chat)

        row = QHBoxLayout()

        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask about orders...")
        self.input.returnPressed.connect(self.send)
        row.addWidget(self.input)

        self.button = QPushButton("Send")
        self.button.clicked.connect(self.send)
        row.addWidget(self.button)

        layout.addLayout(row)

    def send(self):
        text = self.input.text().strip()
        if not text:
            return

        self.chat.append(f"You: {text}")
        self.input.clear()
        self.set_enabled(False)

        self.worker = Worker(text, self.config)
        self.worker.done.connect(self.show_result)
        self.worker.failed.connect(self.show_error)
        self.worker.finished.connect(lambda: self.set_enabled(True))
        self.worker.start()

    def show_result(self, text: str):
        self.chat.append(f"\nAgent:\n{text}\n")

    def show_error(self, error: str):
        self.chat.append(f"\nError: {error}\n")

    def set_enabled(self, enabled: bool):
        self.input.setEnabled(enabled)
        self.button.setEnabled(enabled)


def main():
    api = ApiThread()
    api.start()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    try:
        sys.exit(app.exec())
    finally:
        api.stop()


if __name__ == "__main__":
    main()
