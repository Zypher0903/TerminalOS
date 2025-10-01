from PyQt6.QtWidgets import QWidget, QStackedWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from core.auth import LoginRegisterScreen
from core.terminal import TerminalScreen
from PyQt6.QtGui import QFont

class LoadingScreen(QWidget):
    loading_done = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedSize(400, 150)
        self.setStyleSheet("""
            background-color: #121212; 
            color: white; 
            font-family: Consolas, monospace;
            border-radius: 10px;
        """)

        layout = QVBoxLayout()
        self.label = QLabel("Loading TerminalOS...")
        self.label.setFont(QFont("Consolas", 18))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setStyleSheet(""" 
            QProgressBar {
                border: 2px solid #555;
                border-radius: 10px;
                text-align: center;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #00BCD4;
                border-radius: 10px;
            }
        """)

        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_progress)
        self.value = 0

    def start(self):
        self.value = 0
        self.progress.setValue(self.value)
        self.show()
        self.timer.start(25)

    def advance_progress(self):
        self.value += 3
        self.progress.setValue(self.value)
        if self.value >= 100:
            self.timer.stop()
            self.loading_done.emit()
            self.close()


class BootLoader(QStackedWidget):
    def __init__(self):
        super().__init__()

        self.loading_screen = LoadingScreen()
        self.login_screen = LoginRegisterScreen()
        self.terminal_screen = None  # kreira se dinamički

        self.addWidget(self.login_screen)
        self.setWindowTitle("BetterC OS")
        self.resize(800, 600)

        self.loading_screen.loading_done.connect(self.show_login)
        self.login_screen.login_success.connect(self.on_login_success)

        self.loading_screen.start()

    def show_login(self):
        self.show()
        self.setCurrentWidget(self.login_screen)

    def on_login_success(self, username, users):
        from core.utils import save_users
        self.terminal_screen = TerminalScreen(username, users)
        self.addWidget(self.terminal_screen)
        self.setCurrentWidget(self.terminal_screen)
        self.login_screen.hide()
