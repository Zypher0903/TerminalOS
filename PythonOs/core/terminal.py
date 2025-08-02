from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton,
    QInputDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor, QFont, QKeyEvent
from core.utils import save_users
import random
import time
import pyfiglet  # za ASCII art generisanje (pip install pyfiglet)
import requests  # <-- dodato za joke API
import subprocess
import sys


class TerminalScreen(QWidget):
    def __init__(self, username: str, users: dict):
        super().__init__()

        # --- User and session data ---
        self.username = username
        self.users = users
        self.data = self.users.get(username, {})
        self.language = self.data.get("language", 0)  # 0 - English, 1 - Serbian
        self.history = self.data.get("history", [])
        self.notes = self.data.get("notes", [])

        # --- Command and UI state ---
        self.command_history = []
        self.history_index = -1
        self.neofetch_anim_running = False
        self.current_line = 0
        self.ascii_anim_running = False
        self.ascii_anim_index = 0

        self.setWindowTitle(f"BetterC Terminal - {self.username}")
        self.resize(800, 600)

        # --- ASCII arts for neofetch animation ---
        self.ascii_art = [
            "   ******   ",
            " *        * ",
            "*  ****   * ",
            "* *       * ",
            "* *       * ",
            "*  ****   * ",
            " *        * ",
            "   ******   "
        ]

        # --- Setup UI ---
        self._setup_ui()

        # --- Initial banner and welcome ---
        self.print_ascii_banner()
        self.print_info(self._lang("Welcome, {user}!", "Dobrodošli, {user}!", user=self.username))
        self.print_info(self._lang("Type 'help' for commands.", "Ukucajte 'help' za komande."))

        # --- Activity log file ---
        self._log_file_path = f"{self.username}_activity.log"
        self._log(f"User {self.username} logged in.")

    def _setup_ui(self) -> None:
        """Initialize UI widgets and layout"""
        self.layout = QVBoxLayout(self)

        # Output QTextEdit (readonly terminal output)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(
            "background-color: black; color: white; font-family: Consolas, monospace; font-size: 14px;"
        )
        self.layout.addWidget(self.output)

        # Input QLineEdit (command input)
        self.input = QLineEdit()
        self.input.setStyleSheet(
            "background-color: black; color: white; font-family: Consolas, monospace; font-size: 14px;"
        )
        self.input.returnPressed.connect(self.process_command)
        self.input.installEventFilter(self)
        self.layout.addWidget(self.input)

        # Send button
        self.btn_send = QPushButton(self._lang("Send", "Pošalji"))
        self.btn_send.setStyleSheet(
            "background-color: #222; color: white; font-family: Consolas, monospace; font-size: 14px;"
        )
        self.btn_send.clicked.connect(self.process_command)
        self.layout.addWidget(self.btn_send)

        self.setLayout(self.layout)

    def _lang(self, en_text: str, sr_text: str, **kwargs) -> str:
        """Return language-dependent text with optional formatting"""
        text = en_text if self.language == 0 else sr_text
        if kwargs:
            return text.format(**kwargs)
        return text

    def _log(self, message: str) -> None:
        """Append log message to file with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self._log_file_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")

    def eventFilter(self, obj, event) -> bool:
        """Handle Up/Down keys to navigate command history"""
        if obj == self.input and event.type() == QKeyEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Up:
                if self.command_history and self.history_index > 0:
                    self.history_index -= 1
                    self.input.setText(self.command_history[self.history_index])
                return True
            elif event.key() == Qt.Key.Key_Down:
                if self.command_history and self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.input.setText(self.command_history[self.history_index])
                else:
                    self.history_index = len(self.command_history)
                    self.input.clear()
                return True
        return super().eventFilter(obj, event)

    def print_line(self, text: str, color: str = "white", bold: bool = False) -> None:
        """Print text with optional color and bold style"""
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)

        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text + "\n", fmt)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def print_prompt(self, text: str) -> None:
        self.print_line(f"> {text}", color="#00FFFF", bold=True)

    def print_error(self, text: str) -> None:
        self.print_line(text, color="red", bold=True)

    def print_info(self, text: str) -> None:
        self.print_line(text, color="lime", bold=False)

    def print_ascii_banner(self) -> None:
        banner = [
            " ____        _        _   ____   ____   ",
            "| __ )  __ _| |_ __ _| | |___ \\ |___ \\  ",
            "|  _ \\ / _` | __/ _` | |   __) |  __) | ",
            "| |_) | (_| | || (_| | |  / __/  / __/  ",
            "|____/ \\__,_|\\__\\__,_|_| |_____| |_____|",
            "                                        "
        ]
        for line in banner:
            self.print_line(line, color="#00FFFF", bold=True)

    def process_command(self) -> None:
        cmd = self.input.text().strip()
        if not cmd:
            return
        self.command_history.append(cmd)
        self.history_index = len(self.command_history)
        self.input.clear()

        cmd_lower = cmd.lower()
        if self.neofetch_anim_running or self.ascii_anim_running:
            self.neofetch_anim_running = False
            self.ascii_anim_running = False

        self.print_prompt(cmd)
        self._log(f"Command entered: {cmd}")

        # Add your new commands here!
        commands = {
            "help": self.show_help,
            "neofetch": self.start_neofetch_animation,
            "ascii": self.generate_ascii_text,
            "ascii_anim": self.start_ascii_animation,
            "en": lambda: self._set_language(0),
            "sr": lambda: self._set_language(1),
            "password": self.generate_password,
            "calc": self.run_calculator,
            "time": self.show_time,
            "note": self.note_manager,
            "logout": self.logout,
            "quit": self.quit_program,
            "exit": self.quit_program,
            "clear": self.clear_output,
            "random_joke": self.random_joke,
            "fortune": self.show_fortune,
            "color": self.color,         # <-- add this
            "colora": self.colora,       # <-- add this (implement colora method)
            "cquit": self.cquit,         # <-- add this (implement cquit method)
            "hack": self.hack,           # <-- add this (implement hack method)
            "hackfbi": self.hackfbi,     # <-- already implemented above
        }

        func = commands.get(cmd_lower)
        if func:
            func()
        else:
            # pip_install and other dynamic commands
            self.handle_command(cmd_lower)

        self.save_user_data()

    def _set_language(self, lang_id: int) -> None:
        self.language = lang_id
        self.print_info(self._lang("Language set to English.", "Jezik postavljen na srpski."))

    def save_user_data(self) -> None:
        self.users[self.username]["language"] = self.language
        self.users[self.username]["history"] = self.history[-1000:]
        self.users[self.username]["notes"] = self.notes
        save_users(self.users)
        self._log("User data saved.")

    def show_help(self) -> None:
        if self.language == 0:
            cmds = [
                "calc         - calculator",
                "time         - live clock",
                "neofetch     - show logo animation",
                "ascii        - generate ASCII text art",
                "ascii_anim   - simple ASCII animation",
                "password     - generate random password",
                "note         - simple note manager",
                "clear        - clear terminal output",
                "random_joke  - show random joke",
                "fortune      - show a fortune cookie message",
                "logout       - logout current user",
                "en           - set English language",
                "sr           - set Serbian language",
                "pip_install <package> - install Python package",
                "quit/exit    - exit program"
            ]
        else:
            cmds = [
                "calc         - kalkulator",
                "time         - živ časovnik",
                "neofetch     - prikaz logo animacije",
                "ascii        - generiši ASCII tekst",
                "ascii_anim   - jednostavna ASCII animacija",
                "password     - generiše slučajnu lozinku",
                "note         - menadžer beleški",
                "clear        - očisti terminal",
                "random_joke  - prikaz nasumičnog šala",
                "fortune      - prikaži poruku iz fortune cookie",
                "logout       - odjava korisnika",
                "en           - postavi engleski jezik",
                "sr           - postavi srpski jezik",
                "pip_install <package> - instaliraj Python paket",
                "quit/exit    - izlaz iz programa"
            ]
        self.print_info("=== Commands ===" if self.language == 0 else "=== Komande ===")
        for c in cmds:
            self.print_info(c)

    # --- Neofetch animation ---
    def start_neofetch_animation(self) -> None:
        if self.neofetch_anim_running:
            self.print_info(self._lang("Animation already running.", "Animacija je već pokrenuta."))
            return
        self.neofetch_anim_running = True
        self.current_line = 0
        self.output.clear()
        self.animate_ascii_light()

    def animate_ascii_light(self) -> None:
        if not self.neofetch_anim_running:
            return
        self.output.clear()
        fmt_normal = QTextCharFormat()
        fmt_normal.setForeground(QColor("grey"))
        fmt_bright = QTextCharFormat()
        fmt_bright.setForeground(QColor("cyan"))
        fmt_bright.setFontWeight(QFont.Weight.Bold)

        cursor = self.output.textCursor()
        for i, line in enumerate(self.ascii_art):
            cursor.movePosition(QTextCursor.MoveOperation.End)
            if i == self.current_line:
                cursor.insertText(line + "\n", fmt_bright)
            else:
                cursor.insertText(line + "\n", fmt_normal)

        self.current_line = (self.current_line + 1) % len(self.ascii_art)
        QTimer.singleShot(150, self.animate_ascii_light)

    # --- ASCII Text generator (pyfiglet) ---
    def generate_ascii_text(self) -> None:
        text, ok = QInputDialog.getText(self, "ASCII Text", self._lang("Enter text to convert to ASCII art:", "Unesite tekst za ASCII umetnost:"))
        if not ok or not text.strip():
            self.print_info(self._lang("ASCII generation cancelled.", "Generisanje ASCII umetnosti otkazano."))
            return

        try:
            ascii_art = pyfiglet.figlet_format(text)
            self.print_info(self._lang("Generated ASCII art:", "Generisana ASCII umetnost:"))
            for line in ascii_art.splitlines():
                self.print_line(line, color="yellow")
        except Exception as e:
            self.print_error(self._lang(f"Error generating ASCII art: {e}", f"Greška prilikom generisanja ASCII umetnosti: {e}"))
    def hackfbi(self) -> None:
        for i in range(10):
            self.print_line(f"Hacking FBI... {i+1}/10", color="red", bold=True)
            QApplication.processEvents()
            time.sleep(1) 
        self.print_line("Text color reset to default.", color="white", bold=False)
        self.print_info(self._lang("FBI hacked successfully!", "FBI uspešno hakovan!"))
    def color (self) -> None:
        self.print_line("This is green text.", color="green", bold=True)
        self.print_line("Text color reset to default.", color="white", bold=False)
        self.print_info(self._lang("Color demonstration complete.", "Demonstracija boja završena."))

        
    def colora(self):
        self.print_line("This is red text.", color="red", bold=True)
        self.print_line("Text color reset to default.", color="white", bold=False)
        self.print_info(self._lang("Red color demonstration complete.", "Demonstracija crvene boje završena."))

    def cquit(self):
        self.print_line("Text color reset to default.", color="white", bold=False)
        self.print_info(self._lang("Color reset complete.", "Boja resetovana."))

    def hack(self):
        for i in range(10):
            self.print_line(f"Matrix hack... {i+1}/10", color="green", bold=True)
            QApplication.processEvents()
            time.sleep(0.1)
        self.print_line("Text color reset to default.", color="white", bold=False)
        self.print_info(self._lang("Matrix hack complete!", "Matrix hack završen!"))
    # --- Simple ASCII animation ---
    def start_ascii_animation(self) -> None:
        if self.ascii_anim_running:
            self.print_info(self._lang("ASCII animation already running.", "ASCII animacija je već pokrenuta."))
            return

        self.ascii_anim_frames = [
            "(>^_^)>",
            "<(^_^<)",
            "^(^_^)^",
            "v(^_^)v",
            "(^_^)"
        ]
        self.ascii_anim_running = True
        self.ascii_anim_index = 0
        self.output.clear()
        self.animate_ascii_frames()

    def animate_ascii_frames(self) -> None:
        if not self.ascii_anim_running:
            return
        self.output.clear()
        frame = self.ascii_anim_frames[self.ascii_anim_index]
        self.print_line(frame, color="cyan", bold=True)
        self.ascii_anim_index = (self.ascii_anim_index + 1) % len(self.ascii_anim_frames)
        QTimer.singleShot(300, self.animate_ascii_frames)

    # --- Password generator ---
    def generate_password(self) -> None:
        charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        length, ok = self.get_input_number(
            self._lang("Enter password length (1-100):", "Unesite dužinu lozinke (1-100):")
        )
        if not ok:
            self.print_info(self._lang("Password generation cancelled.", "Generisanje lozinke otkazano."))
            return
        if length <= 0 or length > 100:
            self.print_error(self._lang("Invalid length!", "Nevažeća dužina!"))
            return
        password = ''.join(random.choice(charset) for _ in range(length))
        self.print_info(self._lang(f"Generated password: {password}", f"Generisana lozinka: {password}"))

    def get_input_number(self, prompt: str) -> tuple[int, bool]:
        return QInputDialog.getInt(self, "Input", prompt, min=1, max=100)

    # --- Calculator ---
    def run_calculator(self) -> None:
        self.print_info(self._lang("Entering calculator mode.", "Ulazim u režim kalkulatora."))
        while True:
            opts = {
                'en': "Options: n(+) m(-) e(*) d(/) h(history) q(quit)",
                'sr': "Opcije: n(+) m(-) e(*) d(/) h(istorija) q(izlaz)"
            }
            option, ok = QInputDialog.getText(self, "Calculator", opts['en'] if self.language == 0 else opts['sr'])
            if not ok:
                break
            option = option.lower()
            if option == 'q':
                self.print_info(self._lang("Leaving calculator...", "Izlazim iz kalkulatora..."))
                break
            elif option == 'h':
                if len(self.history) == 0:
                    self.print_info(self._lang("No history saved yet.", "Još uvek nema sačuvane istorije."))
                else:
                    self.print_info(self._lang("Calculation History:", "Istorija kalkulacija:"))
                    for i, val in enumerate(self.history[-10:], start=1):
                        self.print_line(f"{i}) {val}")
                continue
            elif option not in ['n', 'm', 'e', 'd']:
                self.print_error(self._lang("Invalid option! Try again.", "Nevažeća opcija! Pokušajte ponovo."))
                continue

            a, ok1 = QInputDialog.getInt(self, "Calculator", self._lang("Enter first number:", "Unesite prvi broj:"))
            if not ok1:
                break
            b, ok2 = QInputDialog.getInt(self, "Calculator", self._lang("Enter second number:", "Unesite drugi broj:"))
            if not ok2:
                break

            try:
                if option == 'n':  # addition
                    result = a + b
                    self.print_info(self._lang(f"Sum: {result}", f"Zbir: {result}"))
                elif option == 'm':  # subtraction
                    result = a - b
                    self.print_info(self._lang(f"Result: {result}", f"Rezultat: {result}"))
                elif option == 'e':  # multiplication
                    result = a * b
                    self.print_info(self._lang(f"Product: {result}", f"Proizvod: {result}"))
                elif option == 'd':  # division
                    if b == 0:
                        self.print_error(self._lang("Error: Division by zero!", "Greška: Deljenje nulom!"))
                        continue
                    result = a // b
                    self.print_info(self._lang(f"Quotient: {result}", f"Količnik: {result}"))
                else:
                    continue

                self.history.append(result)
            except Exception as e:
                self.print_error(self._lang(f"Calculation error: {e}", f"Greška prilikom računanja: {e}"))

    # --- Live clock ---
    def show_time(self) -> None:
        self.print_info(self._lang("Press Enter to stop the clock.", "Pritisnite Enter za zaustavljanje časovnika."))

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        # Reconnect returnPressed for stopping time only once
        self.input.returnPressed.disconnect()
        self.input.returnPressed.connect(self.stop_time)

    def update_time(self) -> None:
        current_time = time.strftime("%H:%M:%S")
        self.print_line(current_time, color="yellow", bold=True)

    def stop_time(self) -> None:
        if hasattr(self, "timer"):
            self.timer.stop()
            self.print_info(self._lang("Clock stopped.", "Časovnik zaustavljen."))
            self.input.returnPressed.disconnect()
            self.input.returnPressed.connect(self.process_command)

    # --- Notes Manager ---
    def note_manager(self) -> None:
        prompt = self._lang(
            "Note Manager: (write/read/delete/exit)",
            "Menadžer beleški: (write/read/delete/exit)"
        )

        while True:
            choice, ok = QInputDialog.getText(self, "Notes", prompt)
            if not ok:
                break
            choice = choice.lower()

            if choice == "write":
                self._note_write()
            elif choice == "read":
                self._note_read()
            elif choice == "delete":
                self._note_delete()
            elif choice == "exit":
                self.print_info(self._lang("Exiting notes manager.", "Izlazim iz menadžera beleški."))
                break
            else:
                self.print_error(self._lang("Unknown option.", "Nepoznata opcija."))

    def _note_write(self) -> None:
        note, ok = QInputDialog.getMultiLineText(self, "Write Note", self._lang("Enter note text:", "Unesite tekst beleške:"))
        if ok and note.strip():
            self.notes.append(note.strip())
            self.print_info(self._lang("Note saved.", "Beleška sačuvana."))
        else:
            self.print_info(self._lang("No note saved.", "Beleška nije sačuvana."))

    def _note_read(self) -> None:
        if not self.notes:
            self.print_info(self._lang("No notes available.", "Nema dostupnih beleški."))
            return
        self.print_info(self._lang("Your notes:", "Vaše beleške:"))
        for i, note in enumerate(self.notes, start=1):
            self.print_line(f"{i}) {note}")

    def _note_delete(self) -> None:
        if not self.notes:
            self.print_info(self._lang("No notes to delete.", "Nema beleški za brisanje."))
            return
        index, ok = QInputDialog.getInt(
            self, "Delete Note",
            self._lang(f"Enter note number to delete (1-{len(self.notes)}):",
                       f"Unesite broj beleške za brisanje (1-{len(self.notes)}):"),
            min=1, max=len(self.notes)
        )
        if ok:
            deleted = self.notes.pop(index - 1)
            self.print_info(self._lang(f"Deleted note: {deleted}", f"Obrisana beleška: {deleted}"))
        else:
            self.print_info(self._lang("Delete cancelled.", "Brisanje otkazano."))

    # --- Logout ---
    def logout(self) -> None:
        self._log(f"User {self.username} logged out.")
        self.print_info(self._lang("Logging out...", "Odjavljivanje..."))
        self.close()

    # --- Quit program ---
    def quit_program(self) -> None:
        self._log(f"User {self.username} exited program.")
        self.print_info(self._lang("Exiting program...", "Izlaz iz programa..."))
        self.close()

    # --- Clear terminal output ---
    def clear_output(self) -> None:
        self.output.clear()
        self.print_info(self._lang("Terminal cleared.", "Terminal očišćen."))

    # --- Random joke (fetch from icanhazdadjoke.com API) ---
    def random_joke(self) -> None:
        try:
            headers = {'Accept': 'application/json', 'User-Agent': 'BetterC Terminal'}
            response = requests.get("https://icanhazdadjoke.com/", headers=headers, timeout=5)
            if response.status_code == 200:
                joke_json = response.json()
                joke = joke_json.get("joke", None)
                if joke:
                    self.print_info(joke)
                else:
                    self.print_info(self._lang("No joke found.", "Nema pronađene šale."))
            else:
                self.print_info(self._lang("Failed to fetch joke.", "Nije uspelo preuzimanje šale."))
        except Exception as e:
            self.print_error(self._lang(f"Error fetching joke: {e}", f"Greška prilikom preuzimanja šale: {e}"))

    # --- Fortune cookie messages ---
    def show_fortune(self) -> None:
        fortunes_en = [
            "You will have a pleasant surprise.",
            "A thrilling time is in your immediate future.",
            "Your hard work will soon pay off.",
            "New opportunities are around the corner."
        ]
        fortunes_sr = [
            "Čeka vas prijatno iznenađenje.",
            "Uskoro vas očekuje uzbudljivo vreme.",
            "Vaš trud će uskoro biti nagrađen.",
            "Nove prilike su iza ugla."
        ]
        fortune = random.choice(fortunes_en if self.language == 0 else fortunes_sr)
        self.print_info(f"Fortune: {fortune}")

    def handle_command(self, cmd):
        try:
            if cmd.startswith("pip_install "):
                package = cmd.split(" ", 1)[1]
                self.print_info(f"Installing package: {package} ...")
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", package],
                        capture_output=True, text=True
                    )
                    self.print_info(result.stdout)
                    if result.stderr:
                        self.print_error(result.stderr)
                except Exception as e:
                    self.print_error(f"Error: {e}")
            elif cmd == "help":
                self.show_help()
            else:
                self.print_error(self._lang(
                    "Unknown command. Type 'help' for available commands.",
                    "Nepoznata komanda. Ukucajte 'help' za dostupne komande."
                ))
        except Exception as e:
            self.print_error(f"Internal error: {e}")

