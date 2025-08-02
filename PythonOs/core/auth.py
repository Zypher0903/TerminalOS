from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
from core.utils import load_users, save_users

class LoginRegisterScreen(QWidget):
    login_success = pyqtSignal(str, dict)  # emit username and users dict on success

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login / Register")
        self.setFixedSize(400, 300)

        self.users = load_users()

        layout = QVBoxLayout()
        self.info_label = QLabel("Please Login or Register")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.info_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Login")
        self.btn_register = QPushButton("Register")
        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_register)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

        self.btn_login.clicked.connect(self.try_login)
        self.btn_register.clicked.connect(self.try_register)

    def try_login(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text()
        if user in self.users and self.users[user]['password'] == pwd:
            self.info_label.setText(f"Welcome back, {user}!")
            self.login_success.emit(user, self.users)
        else:
            self.info_label.setText("Invalid username or password!")
            self.info_label.setStyleSheet("color: red; font-size: 16px;")

    def try_register(self):
        user = self.username_input.text().strip()
        pwd = self.password_input.text()
        if not user or not pwd:
            self.info_label.setText("Please enter username and password.")
            self.info_label.setStyleSheet("color: red; font-size: 16px;")
            return
        if user in self.users:
            self.info_label.setText("Username already exists!")
            self.info_label.setStyleSheet("color: red; font-size: 16px;")
            return
        self.users[user] = {
            "password": pwd,
            "language": 0,
            "history": [],
            "notes": []
        }
        save_users(self.users)
        self.info_label.setText(f"User {user} registered! Please login.")
        self.info_label.setStyleSheet("color: green; font-size: 16px;")
