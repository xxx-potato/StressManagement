import sys
import sqlite3
from datetime import datetime, timedelta
import random
import builtins
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
                             QMessageBox, QStackedWidget, QFormLayout, QDialog, QTableWidget,
                             QTableWidgetItem, QScrollArea, QProgressBar, QListWidget, QListWidgetItem,
                             QCalendarWidget, QDialogButtonBox, QSpinBox, QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QTimer, QDate, QLocale
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = sqlite3.connect('mbsr_data.db')
    yield conn
    conn.close()

def init_db():
    conn = sqlite3.connect('mbsr_data.db')
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exercises'")
    if not c.fetchone():
        c.execute('''CREATE TABLE exercises (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT,
                     description TEXT,
                     stress_level_min INTEGER,
                     stress_level_max INTEGER)''')
    c.execute("PRAGMA table_info(exercises)")
    columns = {row[1] for row in c.fetchall()}
    if 'video_url' in columns:
        c.execute("CREATE TABLE exercises_temp AS SELECT id, name, description, stress_level_min, stress_level_max FROM exercises")
        c.execute("DROP TABLE exercises")
        c.execute('''CREATE TABLE exercises (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT,
                     description TEXT,
                     stress_level_min INTEGER,
                     stress_level_max INTEGER)''')
        c.execute("INSERT INTO exercises (id, name, description, stress_level_min, stress_level_max) SELECT id, name, description, stress_level_min, stress_level_max FROM exercises_temp")
        c.execute("DROP TABLE exercises_temp")
    c.execute("DELETE FROM exercises")
    c.execute(
        "INSERT INTO exercises (name, description, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?)",
        ("Mindful Breathing 1",
         "This is a foundational mindfulness exercise focusing on slow, deep breathing to promote relaxation. Sit comfortably, close your eyes if comfortable, and inhale deeply through your nose for a count of 4, hold for 4, then exhale slowly for 6. Repeat this cycle for 5 minutes, allowing your mind to settle and your body to release tension. Ideal for beginners or moments of mild stress.",
         1, 3))
    c.execute(
        "INSERT INTO exercises (name, description, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?)",
        ("Mindful Breathing 2",
         "An advanced breathing exercise to enhance focus and calm. Begin by sitting quietly, then count each breath from 1 to 10 as you inhale and exhale, restarting at 1 once you reach 10. If your mind wanders, gently return to 1. Practice for 10 minutes, noticing the rhythm of your breath. Suitable for moderate stress levels or to deepen concentration.",
         4, 6))
    c.execute(
        "INSERT INTO exercises (name, description, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?)",
        ("Body Scan",
         "A guided meditation to release physical and mental tension. Lie down or sit comfortably, and slowly bring your attention to each part of your body, starting from your toes and moving up to your head. Notice any sensations without judgment, spending about 1-2 minutes per area. This 15-20 minute practice is perfect for high stress or chronic tension relief.",
         7, 10))
    c.execute(
        "INSERT INTO exercises (name, description, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?)",
        ("Walking Meditation",
         "A moving mindfulness practice to connect with your body and surroundings. Walk slowly for 10 minutes in a quiet space, focusing on the sensation of each step—lifting, moving, and placing your foot. Coordinate your breath with your steps (e.g., inhale for 3 steps, exhale for 3). Great for moderate stress or when you need a break from sitting.",
         3, 5))
    c.execute(
        "INSERT INTO exercises (name, description, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?)",
        ("Loving-Kindness Meditation",
         "A heart-centered practice to cultivate compassion. Sit comfortably and silently repeat phrases like 'May I be happy, may I be healthy' for yourself, then extend them to others. Spend 10-15 minutes, starting with loved ones and gradually including neutral or difficult people. Ideal for emotional stress or fostering positivity.",
         2, 4))
    c.execute(
        "INSERT INTO exercises (name, description, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?)",
        ("Gentle Stretching",
         "A physical exercise to release tension and improve flexibility. Perform a series of gentle stretches—neck rolls, shoulder shrugs, side bends, and leg stretches—for 10-15 minutes. Move slowly, breathing deeply into each stretch. This is excellent for all stress levels, especially when combined with mindful breathing.",
         1, 10))
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT,
                 is_admin INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stress_levels (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 date TEXT,
                 stress_before INTEGER,
                 stress_after INTEGER,
                 exercise_type TEXT,
                 notes TEXT,
                 duration_percentage REAL DEFAULT 0.0,
                 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS community_posts (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 content TEXT,
                 date TEXT,
                 comments TEXT DEFAULT '',
                 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS login_history (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 login_date TEXT,
                 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS rewards (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 reward_name TEXT,
                 reward_description TEXT,
                 earned INTEGER DEFAULT 0,
                 earn_date TEXT,
                 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')
    c.execute("PRAGMA table_info(stress_levels)")
    columns = {row[1] for row in c.fetchall()}
    if 'duration_percentage' not in columns:
        c.execute("ALTER TABLE stress_levels ADD COLUMN duration_percentage REAL DEFAULT 0.0")
    conn.commit()
    conn.close()

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class UserDetailsDialog(QDialog):
    def __init__(self, user_id, username, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle(f"User Details: {username}")
        self.layout = QVBoxLayout()
        self.canvas = MplCanvas(self)
        self.update_stress_diagram()
        self.layout.addWidget(self.canvas)
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(6)
        self.session_table.setHorizontalHeaderLabels(
            ["Date", "Exercise", "Stress Before", "Stress After", "Completion %", "Notes"])
        self.layout.addWidget(self.session_table)
        self.update_session_table()
        delete_btn = QPushButton("Delete User")
        delete_btn.clicked.connect(self.delete_user)
        self.layout.addWidget(delete_btn)
        self.setLayout(self.layout)

    def update_stress_diagram(self):
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute(
            "SELECT date, exercise_type, stress_before, stress_after, duration_percentage, notes FROM stress_levels WHERE user_id=? ORDER BY date",
            (self.user_id,))
        data = c.fetchall()
        conn.close()
        self.canvas.axes.clear()
        if data:
            dates = [row[0] for row in data]
            stress_before = [row[2] for row in data]
            stress_after = [row[3] for row in data]
            percentages = [row[4] for row in data]
            self.canvas.axes.plot(dates, stress_before, label="Before", marker='o', color='blue')
            self.canvas.axes.plot(dates, stress_after, label="After", marker='o', color='green')
            self.canvas.axes.plot(dates, percentages, label="Completion %", marker='s', linestyle='--',
                                  color='orange')
            self.canvas.axes.legend()
            self.canvas.axes.set_title("User Stress Level and Completion % Trends")
            self.canvas.axes.set_xlabel("Date")
            self.canvas.axes.set_ylabel("Value")
            self.canvas.axes.tick_params(axis='x', rotation=45)
        else:
            self.canvas.axes.text(0.5, 0.5, "No data available",
                                  horizontalalignment='center',
                                  verticalalignment='center',
                                  transform=self.canvas.axes.transAxes)
            self.canvas.axes.set_title("User Stress Level and Completion % Trends")
        self.canvas.draw()

    def update_session_table(self):
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute(
            "SELECT date, exercise_type, stress_before, stress_after, duration_percentage, notes FROM stress_levels WHERE user_id=? ORDER BY date",
            (self.user_id,))
        data = c.fetchall()
        conn.close()
        self.session_table.setRowCount(len(data))
        if not data:
            self.session_table.setRowCount(1)
            self.session_table.setItem(0, 0, QTableWidgetItem("No records for this user"))
        else:
            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    if j == 4 and value is not None:
                        self.session_table.setItem(i, j, QTableWidgetItem(str(builtins.round(float(value), 1))))
                    else:
                        self.session_table.setItem(i, j, QTableWidgetItem(str(value) if value is not None else ""))

    def delete_user(self):
        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Are you sure you want to delete this user? This will also delete their stress records and community posts.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute("DELETE FROM users WHERE id=?", (self.user_id,))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "User deleted successfully")
            self.accept()

class ExerciseEditDialog(QDialog):
    def __init__(self, exercise_id=None, name="", description="", min_level=1, max_level=10, parent=None):
        super().__init__(parent)
        self.exercise_id = exercise_id
        self.setWindowTitle("Add/Edit Exercise")
        layout = QFormLayout()
        self.name_input = QLineEdit(name)
        self.description_input = QTextEdit(description)
        self.min_level_input = QSpinBox()
        self.min_level_input.setRange(1, 10)
        self.min_level_input.setValue(min_level)
        self.max_level_input = QSpinBox()
        self.max_level_input.setRange(1, 10)
        self.max_level_input.setValue(max_level)
        layout.addRow("Name:", self.name_input)
        layout.addRow("Description:", self.description_input)
        layout.addRow("Min Stress Level:", self.min_level_input)
        layout.addRow("Max Stress Level:", self.max_level_input)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        layout = QFormLayout()
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        login_btn = QPushButton("Login")
        register_btn = QPushButton("Register")
        login_btn.clicked.connect(self.handle_login)
        register_btn.clicked.connect(self.handle_register)
        layout.addRow("Username:", self.username)
        layout.addRow("Password:", self.password)
        layout.addWidget(login_btn)
        layout.addWidget(register_btn)
        self.setLayout(layout)

    def handle_login(self):
        if not self.username.text() or not self.password.text():
            QMessageBox.warning(self, "Error", "Username and password cannot be empty")
            return
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        if self.username.text() == "manager" and self.password.text() == "manager":
            self.user_id = 0
            self.is_admin = True
            conn.close()
            self.accept()
            return
        c.execute("SELECT id, is_admin FROM users WHERE username=? AND password=?",
                  (self.username.text(), self.password.text()))
        user = c.fetchone()
        if user:
            self.user_id, self.is_admin = user
            c.execute("INSERT INTO login_history (user_id, login_date) VALUES (?, ?)",
                      (self.user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")
            conn.close()

    def handle_register(self):
        if not self.username.text() or not self.password.text():
            QMessageBox.warning(self, "Error", "Username and password cannot be empty")
            return
        if self.username.text() == "manager":
            QMessageBox.warning(self, "Error", "Username 'manager' is reserved")
            return
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                  (self.username.text(), self.password.text()))
        user_id = c.lastrowid
        rewards = [
            ("Three Day Login", "Log in for three consecutive days"),
            ("Three Day Exercise", "Complete exercises for three consecutive days"),
            ("Ten Exercises Completed", "Complete 10 exercises in total"),
            ("First Community Post", "Share your first community post"),
            ("Stress Reduction Master", "Reduce stress level in three consecutive exercises"),
            ("Perfect Week", "Complete at least one exercise each day for a week"),
            ("Mindful Master", "Complete 50 Mindful Breathing exercises")
        ]
        for name, desc in rewards:
            c.execute("INSERT INTO rewards (user_id, reward_name, reward_description, earned) VALUES (?, ?, ?, ?)",
                      (user_id, name, desc, 0))
        conn.commit()
        conn.close()
        QMessageBox.information(self, "Success", "Registration successful! Please login.")

class MBSRApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.user_id = None
        self.is_admin = False
        self.username = "Guest"
        self.stress_before_level = None
        self.current_exercise = None
        self.timer_count = 0
        self.nav_buttons = []
        self.setWindowTitle("StressRelief")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        self.nav_layout = QHBoxLayout()
        if self.is_admin:
            nav_button_texts = ["Manage User", "Manage Exercise", "Manage Community"]
        else:
            nav_button_texts = ["Home", "View Dashboard", "Get Reward", "Exercises List", "Community",
                                f"Hi {self.username}"]
        for text in nav_button_texts:
            button = QPushButton(text)
            button.clicked.connect(lambda checked, b=text: self.navigate(b))
            self.nav_layout.addWidget(button)
            self.nav_buttons.append(button)
        main_layout.addLayout(self.nav_layout)
        self.page_stack = QStackedWidget()
        self.home_page = self.create_home_page()
        self.dashboard_page = self.create_dashboard_page()
        self.exercise_list_page = self.create_exercise_list_page()
        self.exercise_assessment_page = self.create_exercise_assessment_page()
        self.exercise_recommendation_page = self.create_exercise_recommendation_page()
        self.exercise_completion_page = self.create_exercise_completion_page()
        self.community_page = self.create_community_page()
        self.reward_page = self.create_reward_page()
        self.manage_user_page = self.create_manage_user_page()
        self.manage_exercise_page = self.create_manage_exercise_page()
        self.manage_community_page = self.create_manage_community_page()
        self.page_stack.addWidget(self.home_page)
        self.page_stack.addWidget(self.dashboard_page)
        self.page_stack.addWidget(self.exercise_list_page)
        self.page_stack.addWidget(self.exercise_assessment_page)
        self.page_stack.addWidget(self.exercise_recommendation_page)
        self.page_stack.addWidget(self.exercise_completion_page)
        self.page_stack.addWidget(self.community_page)
        self.page_stack.addWidget(self.reward_page)
        self.page_stack.addWidget(self.manage_user_page)
        self.page_stack.addWidget(self.manage_exercise_page)
        self.page_stack.addWidget(self.manage_community_page)
        main_layout.addWidget(self.page_stack)
        self.page_stack.setCurrentWidget(self.manage_user_page if self.is_admin else self.home_page)

    def navigate(self, page):
        if self.user_id is None and page != "register, login / Hi name" and page != f"Hi {self.username}":
            QMessageBox.warning(self, "Login Required", "Please login to access this feature")
            self.show_login_dialog()
            return
        if page == "Home":
            self.page_stack.setCurrentWidget(self.home_page)
            self.update_pressure_diagram()
        elif page == "View Dashboard":
            self.page_stack.setCurrentWidget(self.dashboard_page)
            QTimer.singleShot(100, self.update_dashboard)
        elif page == "Get Reward":
            self.page_stack.setCurrentWidget(self.reward_page)
            self.update_reward_page()
        elif page == "Exercises List":
            self.page_stack.setCurrentWidget(self.exercise_list_page)
        elif page == "Community":
            self.page_stack.setCurrentWidget(self.community_page)
            self.update_posts()
        elif page == "Manage User":
            self.page_stack.setCurrentWidget(self.manage_user_page)
            self.update_manage_user()
        elif page == "Manage Exercise":
            self.page_stack.setCurrentWidget(self.manage_exercise_page)
            self.update_manage_exercise()
        elif page == "Manage Community":
            self.page_stack.setCurrentWidget(self.manage_community_page)
            self.update_manage_community()
        elif page == "register, login / Hi name" or page == f"Hi {self.username}":
            if self.user_id is None:
                self.show_login_dialog()
            else:
                self.logout()

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.canvas = MplCanvas(self)
        self.update_pressure_diagram()
        layout.addWidget(self.canvas)
        lets_go_btn = QPushButton("Let's Go!")
        lets_go_btn.clicked.connect(self.start_exercise)
        layout.addWidget(lets_go_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        quote_label = QLabel(self.get_motivational_quote())
        quote_label.setStyleSheet("border: 1px solid gray; padding: 10px; color: #E0E0E0; background-color: #222;")
        quote_label.setWordWrap(True)
        layout.addWidget(quote_label)
        comment_label = QLabel(self.get_sample_comment())
        comment_label.setStyleSheet("border: 1px solid gray; padding: 10px; color: #E0E0E0; background-color: #222; cursor: pointer;")
        comment_label.setWordWrap(True)
        comment_label.mousePressEvent = lambda event: self.navigate("Community")
        layout.addWidget(comment_label)
        page.setLayout(layout)
        return page

    def start_exercise(self):
        if self.user_id is None:
            QMessageBox.warning(self, "Login Required", "Please login to access exercises")
            if not self.show_login_dialog():
                self.page_stack.setCurrentWidget(self.home_page)
                return
        self.page_stack.setCurrentWidget(self.exercise_assessment_page)

    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        calendar_layout = QHBoxLayout()
        self.calendar = QCalendarWidget()
        self.calendar.setMaximumDate(QDate.currentDate())
        self.calendar.setLocale(QLocale(QLocale.Language.English, QLocale.Country.UnitedStates))
        self.calendar.selectionChanged.connect(self.update_dashboard_by_date)
        calendar_layout.addWidget(self.calendar)
        reset_btn = QPushButton("Show All Records")
        reset_btn.clicked.connect(lambda: self.update_dashboard(selected_date=None))
        calendar_layout.addWidget(reset_btn)
        layout.addLayout(calendar_layout)
        self.date_label = QLabel("Showing all records")
        layout.addWidget(self.date_label)
        self.progress_label = QLabel("Completed Exercises: 0")
        layout.addWidget(self.progress_label)
        self.canvas_dashboard = MplCanvas(self)
        layout.addWidget(self.canvas_dashboard)
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(6)
        self.session_table.setHorizontalHeaderLabels(
            ["Date", "Exercise", "Stress Before", "Stress After", "Completion %", "Notes"])
        layout.addWidget(self.session_table)
        page.setLayout(layout)
        self.update_dashboard()
        return page

    def create_exercise_list_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        scroll_area = QScrollArea(page)
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(15)
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("SELECT name, description FROM exercises")
        exercises = c.fetchall()
        conn.close()
        for exercise in exercises:
            exercise_frame = QFrame()
            exercise_frame.setStyleSheet("""
                background-color: #222;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px;
                margin: 5px;
            """)
            exercise_layout = QVBoxLayout()
            exercise_label = QLabel(f"Exercise: {exercise[0]}")
            exercise_label.setStyleSheet("font-size: 14px; color: #E0E0E0; font-weight: bold;")
            exercise_label.setWordWrap(True)
            exercise_label.setMinimumWidth(300)
            exercise_layout.addWidget(exercise_label)
            desc_label = QLabel(f"Description: {exercise[1]}")
            desc_label.setStyleSheet("font-size: 12px; color: #B0B0B0;")
            desc_label.setWordWrap(True)
            desc_label.setMinimumWidth(300)
            exercise_layout.addWidget(desc_label)
            exercise_frame.setLayout(exercise_layout)
            content_layout.addWidget(exercise_frame)
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet("color: #444;")
            content_layout.addWidget(separator)
        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        scroll_area.setStyleSheet("border: none; background-color: #000;")
        layout.addWidget(scroll_area)
        page.setLayout(layout)
        return page

    def create_exercise_assessment_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        stress_label = QLabel("Please assess your current stress level (1-10):")
        self.stress_before_combo = QComboBox()
        self.stress_before_combo.addItems([str(i) for i in range(1, 11)])
        assess_btn = QPushButton("Assess")
        assess_btn.clicked.connect(self.assess_stress)
        layout.addWidget(stress_label)
        layout.addWidget(self.stress_before_combo)
        layout.addWidget(assess_btn)
        page.setLayout(layout)
        return page

    def create_exercise_recommendation_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.recommendation_label = QLabel(
            "Please assess your stress level on the previous page to see a recommendation.")
        self.recommendation_label.setStyleSheet("font-size: 14px; color: #E0E0E0; margin-bottom: 10px;")
        self.recommendation_label.setWordWrap(True)
        layout.addWidget(self.recommendation_label)
        self.exercise_content = QTextEdit()
        self.exercise_content.setReadOnly(True)
        self.exercise_content.setMinimumHeight(200)
        self.exercise_content.setStyleSheet("""
            font-size: 14px;
            padding: 10px;
            border: 1px solid #444;
            border-radius: 5px;
            background-color: #222;
            color: #E0E0E0;
        """)
        layout.addWidget(self.exercise_content)
        self.exercise_content.hide()
        self.timer_label = QLabel("Time remaining: 5:00")
        self.timer_label.setStyleSheet("font-size: 14px; color: #E0E0E0;")
        self.timer_label.setWordWrap(True)
        layout.addWidget(self.timer_label)
        self.timer_progress = QProgressBar()
        self.timer_progress.setMaximum(300)
        self.timer_progress.setValue(0)
        layout.addWidget(self.timer_progress)
        self.timer_label.hide()
        self.timer_progress.hide()
        buttons_layout = QHBoxLayout()
        finish_btn = QPushButton("Finish")
        finish_btn.setStyleSheet("""
            font-size: 14px;
            padding: 8px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
        """)
        finish_btn.clicked.connect(lambda: self.end_exercise(complete=True))
        buttons_layout.addWidget(finish_btn)
        end_early_btn = QPushButton("End Early")
        end_early_btn.setStyleSheet("""
            font-size: 14px;
            padding: 8px;
            background-color: #FF4444;
            color: white;
            border: none;
            border-radius: 5px;
        """)
        end_early_btn.clicked.connect(lambda: self.end_exercise(complete=False))
        buttons_layout.addWidget(end_early_btn)
        layout.addLayout(buttons_layout)
        finish_btn.hide()
        end_early_btn.hide()
        self.finish_btn = finish_btn
        self.end_early_btn = end_early_btn
        page.setLayout(layout)
        if self.stress_before_level:
            self.recommend_exercise()
        return page

    def create_exercise_completion_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        stress_after_label = QLabel("Please assess your stress level after the exercise (1-10):")
        self.stress_after_combo = QComboBox()
        self.stress_after_combo.addItems([str(i) for i in range(1, 11)])
        layout.addWidget(stress_after_label)
        layout.addWidget(self.stress_after_combo)
        notes_label = QLabel("Notes (record your feelings):")
        self.notes_input = QTextEdit()
        layout.addWidget(notes_label)
        layout.addWidget(self.notes_input)
        submit_btn = QPushButton("Submit")
        submit_btn.clicked.connect(self.submit_exercise)
        layout.addWidget(submit_btn)
        page.setLayout(layout)
        return page

    def create_reward_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        title_label = QLabel("Your Rewards")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)
        grid_layout = QGridLayout()
        self.reward_widgets = []
        rewards = [
            ("Three Day Login", "Log in for three consecutive days"),
            ("Three Day Exercise", "Complete exercises for three consecutive days"),
            ("Ten Exercises Completed", "Complete 10 exercises in total"),
            ("First Community Post", "Share your first community post"),
            ("Stress Reduction Master", "Reduce stress level in three consecutive exercises"),
            ("Perfect Week", "Complete at least one exercise each day for a week"),
            ("Mindful Master", "Complete 50 Mindful Breathing exercises")
        ]
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        for i, (reward_name, reward_description) in enumerate(rewards):
            c.execute("SELECT earned, earn_date FROM rewards WHERE user_id=? AND reward_name=?",
                      (self.user_id, reward_name))
            result = c.fetchone()
            earned = result[0] if result else 0
            earn_date = result[1] if result and result[1] else "Not earned yet"
            reward_widget = QWidget()
            reward_layout = QVBoxLayout()
            icon_label = QLabel("🏅" if earned else "🔘")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet(f"font-size: 30px; color: {'green' if earned else 'gray'};")
            reward_layout.addWidget(icon_label)
            name_label = QLabel(reward_name)
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label.setStyleSheet(f"font-weight: bold; color: {'black' if earned else 'gray'};")
            reward_layout.addWidget(name_label)
            desc_label = QLabel(reward_description)
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(f"color: {'black' if earned else 'gray'};")
            reward_layout.addWidget(desc_label)
            date_label = QLabel(f"Earned: {earn_date}")
            date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            date_label.setStyleSheet(f"color: {'black' if earned else 'gray'};")
            reward_layout.addWidget(date_label)
            reward_widget.setLayout(reward_layout)
            reward_widget.setStyleSheet(f"border: 1px solid {'green' if earned else 'gray'}; padding: 10px;")
            grid_layout.addWidget(reward_widget, i // 2, i % 2)
            self.reward_widgets.append((reward_widget, reward_name))
        conn.close()
        layout.addLayout(grid_layout)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def update_reward_page(self):
        if self.user_id is None:
            for widget, _ in self.reward_widgets:
                widget.setStyleSheet("border: 1px solid gray; padding: 10px;")
                for child in widget.findChildren(QLabel):
                    child.setStyleSheet("color: gray;")
            return
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        for widget, reward_name in self.reward_widgets:
            c.execute("SELECT earned, earn_date FROM rewards WHERE user_id=? AND reward_name=?",
                      (self.user_id, reward_name))
            result = c.fetchone()
            earned = result[0] if result else 0
            earn_date = result[1] if result and result[1] else "Not earned yet"
            widget.setStyleSheet(f"border: 1px solid {'green' if earned else 'gray'}; padding: 10px;")
            labels = widget.findChildren(QLabel)
            labels[0].setText("🏅" if earned else "🔘")
            labels[0].setStyleSheet(f"font-size: 30px; color: {'white' if earned else 'gray'};")
            labels[1].setStyleSheet(f"font-weight: bold; color: {'white' if earned else 'gray'};")
            labels[2].setStyleSheet(f"color: {'white' if earned else 'gray'};")
            labels[3].setText(f"Earned: {earn_date}")
            labels[3].setStyleSheet(f"color: {'white' if earned else 'gray'};")
        conn.close()

    def check_and_award_rewards(self):
        if self.user_id is None:
            return
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        today = datetime.now().date()
        past_three_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
        c.execute("SELECT DISTINCT login_date FROM login_history WHERE user_id=? AND " + " OR ".join(["login_date LIKE ?" for _ in past_three_days]),
                  (self.user_id, *[f"{day}%" for day in past_three_days]))
        login_dates = [row[0].split()[0] for row in c.fetchall() if row]
        if all(day in login_dates for day in past_three_days):
            c.execute("SELECT earned FROM rewards WHERE user_id=? AND reward_name='Three Day Login'", (self.user_id,))
            earned = c.fetchone()
            if earned and earned[0] == 0:
                c.execute("UPDATE rewards SET earned=1, earn_date=? WHERE user_id=? AND reward_name=?",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user_id, "Three Day Login"))
                QMessageBox.information(self, "Reward Earned!", "Congratulations! You've earned the 'Three Day Login' medal for logging in three consecutive days!")
        c.execute("SELECT DISTINCT date FROM stress_levels WHERE user_id=? AND " + " OR ".join(["date LIKE ?" for _ in past_three_days]),
                  (self.user_id, *[f"{day}%" for day in past_three_days]))
        exercise_dates = [row[0].split()[0] for row in c.fetchall() if row]
        if all(day in exercise_dates for day in past_three_days):
            c.execute("SELECT earned FROM rewards WHERE user_id=? AND reward_name='Three Day Exercise'", (self.user_id,))
            earned = c.fetchone()
            if earned and earned[0] == 0:
                c.execute("UPDATE rewards SET earned=1, earn_date=? WHERE user_id=? AND reward_name=?",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user_id, "Three Day Exercise"))
                QMessageBox.information(self, "Reward Earned!", "Congratulations! You've earned the 'Three Day Exercise' medal for completing exercises three consecutive days!")
        c.execute("SELECT COUNT(*) FROM stress_levels WHERE user_id=?", (self.user_id,))
        exercise_count = c.fetchone()
        if exercise_count and exercise_count[0] >= 10:
            c.execute("SELECT earned FROM rewards WHERE user_id=? AND reward_name='Ten Exercises Completed'", (self.user_id,))
            earned = c.fetchone()
            if earned and earned[0] == 0:
                c.execute("UPDATE rewards SET earned=1, earn_date=? WHERE user_id=? AND reward_name=?",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user_id, "Ten Exercises Completed"))
                QMessageBox.information(self, "Reward Earned!", "Congratulations! You've earned the 'Ten Exercises Completed' medal for completing 10 exercises!")
        c.execute("SELECT COUNT(*) FROM community_posts WHERE user_id=?", (self.user_id,))
        post_count = c.fetchone()
        if post_count and post_count[0] >= 1:
            c.execute("SELECT earned FROM rewards WHERE user_id=? AND reward_name='First Community Post'", (self.user_id,))
            earned = c.fetchone()
            if earned and earned[0] == 0:
                c.execute("UPDATE rewards SET earned=1, earn_date=? WHERE user_id=? AND reward_name=?",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user_id, "First Community Post"))
                QMessageBox.information(self, "Reward Earned!", "Congratulations! You've earned the 'First Community Post' medal for sharing your first post!")
        c.execute("SELECT stress_before, stress_after FROM stress_levels WHERE user_id=? ORDER BY date DESC LIMIT 3",
                  (self.user_id,))
        recent_sessions = c.fetchall()
        if recent_sessions and len(recent_sessions) >= 3 and all(session[1] < session[0] for session in recent_sessions if session):
            c.execute("SELECT earned FROM rewards WHERE user_id=? AND reward_name='Stress Reduction Master'", (self.user_id,))
            earned = c.fetchone()
            if earned and earned[0] == 0:
                c.execute("UPDATE rewards SET earned=1, earn_date=? WHERE user_id=? AND reward_name=?",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user_id, "Stress Reduction Master"))
                QMessageBox.information(self, "Reward Earned!", "Congratulations! You've earned the 'Stress Reduction Master' medal for reducing stress in three consecutive exercises!")
        past_seven_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        c.execute("SELECT DISTINCT date FROM stress_levels WHERE user_id=? AND " + " OR ".join(["date LIKE ?" for _ in past_seven_days]),
                  (self.user_id, *[f"{day}%" for day in past_seven_days]))
        week_exercise_dates = [row[0].split()[0] for row in c.fetchall() if row]
        if all(day in week_exercise_dates for day in past_seven_days):
            c.execute("SELECT earned FROM rewards WHERE user_id=? AND reward_name='Perfect Week'", (self.user_id,))
            earned = c.fetchone()
            if earned and earned[0] == 0:
                c.execute("UPDATE rewards SET earned=1, earn_date=? WHERE user_id=? AND reward_name=?",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user_id, "Perfect Week"))
                QMessageBox.information(self, "Reward Earned!", "Congratulations! You've earned the 'Perfect Week' medal for exercising every day for a week!")
        c.execute("SELECT COUNT(*) FROM stress_levels WHERE user_id=? AND exercise_type IN ('Mindful Breathing 1', 'Mindful Breathing 2')",
                  (self.user_id,))
        mindful_count = c.fetchone()
        if mindful_count and mindful_count[0] >= 50:
            c.execute("SELECT earned FROM rewards WHERE user_id=? AND reward_name='Mindful Master'", (self.user_id,))
            earned = c.fetchone()
            if earned and earned[0] == 0:
                c.execute("UPDATE rewards SET earned=1, earn_date=? WHERE user_id=? AND reward_name=?",
                          (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.user_id, "Mindful Master"))
                QMessageBox.information(self, "Reward Earned!", "Congratulations! You've earned the 'Mindful Master' medal for completing 50 Mindful Breathing exercises!")
        conn.commit()
        conn.close()
        self.update_reward_page()

    def create_manage_user_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(2)
        self.user_table.setHorizontalHeaderLabels(["Username", "Average Completion %"])
        self.user_table.cellClicked.connect(self.show_user_details)
        layout.addWidget(self.user_table)
        page.setLayout(layout)
        self.update_manage_user()
        return page

    def create_manage_exercise_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        add_btn = QPushButton("Add Exercise")
        add_btn.clicked.connect(self.add_exercise)
        layout.addWidget(add_btn)
        self.exercise_table = QTableWidget()
        self.exercise_table.setColumnCount(4)
        self.exercise_table.setHorizontalHeaderLabels(["Name", "Description", "Min Stress Level", "Max Stress Level"])
        self.exercise_table.cellClicked.connect(self.edit_exercise)
        layout.addWidget(self.exercise_table)
        page.setLayout(layout)
        self.update_manage_exercise()
        return page

    def create_manage_community_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        self.community_list = QListWidget()
        self.community_list.itemDoubleClicked.connect(self.delete_post)
        layout.addWidget(self.community_list)
        page.setLayout(layout)
        self.update_manage_community()
        return page

    def update_manage_user(self):
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("SELECT id, username FROM users WHERE username != 'manager'")
        users = c.fetchall()
        self.user_table.setRowCount(len(users))
        for i, (user_id, username) in enumerate(users):
            c.execute("SELECT AVG(duration_percentage) FROM stress_levels WHERE user_id=?", (user_id,))
            avg_completion = c.fetchone()
            self.user_table.setItem(i, 0, QTableWidgetItem(username))
            self.user_table.setItem(i, 1, QTableWidgetItem(str(builtins.round(float(avg_completion[0]), 1)) if avg_completion and avg_completion[0] is not None else "0.0"))
            self.user_table.setProperty("user_id", user_id)
        conn.close()

    def show_user_details(self, row, column):
        username = self.user_table.item(row, 0).text()
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        user_id = c.fetchone()
        user_id = user_id[0]
        conn.close()
        dialog = UserDetailsDialog(user_id, username, self)
        dialog.exec()
        self.update_manage_user()

    def add_exercise(self):
        dialog = ExerciseEditDialog()
        if dialog.exec():
            name = dialog.name_input.text().strip()
            description = dialog.description_input.toPlainText().strip()
            min_level = dialog.min_level_input.value()
            max_level = dialog.max_level_input.value()
            if not name or not description:
                QMessageBox.warning(self, "Error", "Name and description cannot be empty")
                return
            if min_level > max_level:
                QMessageBox.warning(self, "Error", "Min stress level cannot be greater than max stress level")
                return
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute(
                "INSERT INTO exercises (name, description, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?)",
                (name, description, min_level, max_level))
            conn.commit()
            conn.close()
            self.update_manage_exercise()
            QMessageBox.information(self, "Success", "Exercise added successfully")

    def edit_exercise(self, row, column):
        name = self.exercise_table.item(row, 0).text()
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("SELECT id, name, description, stress_level_min, stress_level_max FROM exercises WHERE name=?",
                  (name,))
        exercise = c.fetchone()
        conn.close()
        if exercise:
            dialog = ExerciseEditDialog(exercise[0], exercise[1], exercise[2], exercise[3], exercise[4])
            if dialog.exec():
                new_name = dialog.name_input.text().strip()
                description = dialog.description_input.toPlainText().strip()
                min_level = dialog.min_level_input.value()
                max_level = dialog.max_level_input.value()
                if not new_name or not description:
                    QMessageBox.warning(self, "Error", "Name and description cannot be empty")
                    return
                if min_level > max_level:
                    QMessageBox.warning(self, "Error", "Min stress level cannot be greater than max stress level")
                    return
                conn = sqlite3.connect('mbsr_data.db')
                c = conn.cursor()
                c.execute(
                    "UPDATE exercises SET name=?, description=?, stress_level_min=?, stress_level_max=? WHERE id=?",
                    (new_name, description, min_level, max_level, exercise[0]))
                conn.commit()
                conn.close()
                self.update_manage_exercise()
                QMessageBox.information(self, "Success", "Exercise updated successfully")
            else:
                reply = QMessageBox.question(self, "Confirm Delete", "Do you want to delete this exercise?",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    conn = sqlite3.connect('mbsr_data.db')
                    c = conn.cursor()
                    c.execute("DELETE FROM exercises WHERE id=?", (exercise[0],))
                    conn.commit()
                    conn.close()
                    self.update_manage_exercise()
                    QMessageBox.information(self, "Success", "Exercise deleted successfully")

    def update_manage_exercise(self):
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("SELECT name, description, stress_level_min, stress_level_max FROM exercises")
        exercises = c.fetchall()
        conn.close()
        self.exercise_table.setRowCount(len(exercises))
        for i, exercise in enumerate(exercises):
            for j, value in enumerate(exercise):
                self.exercise_table.setItem(i, j, QTableWidgetItem(str(value)))

    def update_manage_community(self):
        self.community_list.clear()
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("SELECT id, content, date, comments FROM community_posts ORDER BY date DESC")
        posts = c.fetchall()
        conn.close()
        for post in posts:
            display_text = f"Post ({post[2]}):\n{post[1]}\nComments:\n{post[3] or 'No comments yet'}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, post[0])
            self.community_list.addItem(item)

    def delete_post(self, item):
        post_id = item.data(Qt.ItemDataRole.UserRole)
        reply = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this post?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute("DELETE FROM community_posts WHERE id=?", (post_id,))
            conn.commit()
            conn.close()
            self.update_manage_community()
            QMessageBox.information(self, "Success", "Post deleted successfully")

    def assess_stress(self):
        if self.user_id is None:
            QMessageBox.warning(self, "Login Required", "Please login to access exercises")
            if not self.show_login_dialog():
                self.page_stack.setCurrentWidget(self.home_page)
                return
        self.stress_before_level = int(self.stress_before_combo.currentText())
        QMessageBox.information(self, "Success", f"Stress level {self.stress_before_level} recorded")
        self.page_stack.setCurrentWidget(self.exercise_recommendation_page)
        self.recommend_exercise()

    def recommend_exercise(self):
        if self.user_id is None:
            QMessageBox.warning(self, "Login Required", "Please login to access exercises")
            if not self.show_login_dialog():
                self.page_stack.setCurrentWidget(self.home_page)
                return
        if self.stress_before_level is None:
            self.recommendation_label.setText(
                "No stress level assessed. Please go back and assess your stress level.")
            self.recommendation_label.setWordWrap(True)
            self.exercise_content.hide()
            self.finish_btn.hide()
            self.end_early_btn.hide()
            self.timer_label.hide()
            self.timer_progress.hide()
            return
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("SELECT name, description FROM exercises WHERE ? BETWEEN stress_level_min AND stress_level_max",
                  (self.stress_before_level,))
        exercises = c.fetchall()
        if not exercises:
            c.execute(
                "SELECT name, description FROM exercises WHERE stress_level_min <= 3 AND stress_level_max >= 3")
            exercises = c.fetchall()
        conn.close()
        if exercises:
            selected_exercise = random.choice(exercises)
            self.current_exercise = selected_exercise[0]
            self.recommendation_label.setText(
                f"Recommended Exercise: {selected_exercise[0]}\nDescription: {selected_exercise[1]}")
            self.recommendation_label.setWordWrap(True)
            self.exercise_content.setText(selected_exercise[1])
            self.exercise_content.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
            self.exercise_content.show()
            self.finish_btn.show()
            self.end_early_btn.show()
            duration_seconds = self.get_exercise_duration(self.current_exercise)
            self.timer_count = duration_seconds
            self.timer_progress.setMaximum(duration_seconds)
            self.timer_progress.setValue(0)
            self.timer = QTimer()
            self.timer.timeout.connect(self.update_timer)
            self.timer.start(1000)
            self.timer_label.show()
            self.timer_progress.show()
            self.update_timer()
        else:
            self.recommendation_label.setText("No exercises available in the database. Please contact support.")
            self.recommendation_label.setWordWrap(True)
            self.exercise_content.hide()
            self.finish_btn.hide()
            self.end_early_btn.hide()
            self.timer_label.hide()
            self.timer_progress.hide()

    def get_exercise_duration(self, exercise_name):
        durations = {
            "Mindful Breathing 1": 5 * 60,
            "Mindful Breathing 2": 10 * 60,
            "Body Scan": 15 * 60,
            "Walking Meditation": 10 * 60,
            "Loving-Kindness Meditation": 12 * 60,
            "Gentle Stretching": 12 * 60
        }
        return durations.get(exercise_name, 5 * 60)

    def update_timer(self):
        self.timer_count -= 1
        minutes = self.timer_count // 60
        seconds = self.timer_count % 60
        self.timer_label.setText(f"Time remaining: {minutes}:{seconds:02d}")
        self.timer_progress.setValue(self.timer_progress.maximum() - self.timer_count)
        if self.timer_count <= 0:
            self.timer.stop()
            QMessageBox.information(self, "Time's Up", "Exercise duration completed!")
            self.end_exercise(complete=True)

    def end_exercise(self, complete=True):
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
        duration_seconds = self.get_exercise_duration(self.current_exercise)
        duration_percentage = min((duration_seconds - self.timer_count) / duration_seconds * 100,
                                  100.0) if self.timer_count > 0 else 0.0
        if not complete:
            QMessageBox.information(self, "Exercise Ended",
                                    f"Exercise ended early. Completion: {duration_percentage:.1f}%")
        self.page_stack.setCurrentWidget(self.exercise_completion_page)

    def submit_exercise(self):
        if self.user_id is None:
            QMessageBox.warning(self, "Login Required", "Please login to submit")
            if not self.show_login_dialog():
                self.page_stack.setCurrentWidget(self.home_page)
                return
        if self.current_exercise is None:
            QMessageBox.warning(self, "Error", "No exercise selected. Please start a new exercise.")
            self.page_stack.setCurrentWidget(self.exercise_assessment_page)
            return
        duration_seconds = self.get_exercise_duration(self.current_exercise)
        duration_percentage = min((duration_seconds - self.timer_count) / duration_seconds * 100,
                                  100.0) if self.timer_count > 0 else 0.0
        stress_after = int(self.stress_after_combo.currentText())
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO stress_levels (user_id, date, stress_before, stress_after, exercise_type, notes, duration_percentage) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 self.stress_before_level,
                 stress_after,
                 self.current_exercise,
                 self.notes_input.toPlainText(),
                 duration_percentage))
            conn.commit()
        QMessageBox.information(self, "Success",
                                f"Exercise completed and data saved! Completion: {duration_percentage:.1f}%")
        self.notes_input.clear()
        self.check_and_award_rewards()
        QTimer.singleShot(100, self.update_dashboard)
        QTimer.singleShot(200, self.update_pressure_diagram)
        self.page_stack.setCurrentWidget(self.home_page)
        self.stress_before_level = None
        self.current_exercise = None
        self.timer_count = 0
        if hasattr(self, 'timer'):
            del self.timer

    def create_community_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        anonymous_label = QLabel("Posts are shared anonymously")
        anonymous_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #E0E0E0; margin-bottom: 10px;")
        layout.addWidget(anonymous_label)
        self.post_input = QTextEdit()
        self.post_input.setPlaceholderText("Share your experience anonymously...")
        self.post_input.setMinimumHeight(150)
        self.post_input.setStyleSheet("""
            font-size: 14px;
            padding: 10px;
            border: 1px solid #444;
            border-radius: 5px;
            background-color: #222;
            color: #E0E0E0;
        """)
        layout.addWidget(self.post_input, stretch=1)
        post_btn = QPushButton("Post")
        post_btn.setStyleSheet("""
            font-size: 14px;
            padding: 8px;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
        """)
        post_btn.clicked.connect(self.share_post)
        layout.addWidget(post_btn)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.posts_container = QWidget()
        self.posts_layout = QVBoxLayout(self.posts_container)
        self.posts_layout.setSpacing(15)
        self.posts_layout.addStretch()
        scroll_area.setWidget(self.posts_container)
        scroll_area.setStyleSheet("border: none; background-color: #000;")
        layout.addWidget(scroll_area, stretch=2)
        page.setLayout(layout)
        self.update_posts()
        return page

    def share_post(self):
        if self.user_id is None:
            QMessageBox.warning(self, "Login Required", "Please login to post")
            if not self.show_login_dialog():
                self.page_stack.setCurrentWidget(self.home_page)
                return
        content = self.post_input.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Error", "Post content cannot be empty")
            return
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO community_posts (user_id, content, date) VALUES (?, ?, ?)",
                  (self.user_id, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        self.post_input.clear()
        self.update_posts()
        self.check_and_award_rewards()
        QMessageBox.information(self, "Success", "Post shared anonymously!")

    def show_login_dialog(self):
        login_dialog = LoginDialog()
        if login_dialog.exec():
            self.user_id = login_dialog.user_id
            self.is_admin = login_dialog.is_admin
            self.username = login_dialog.username.text() if login_dialog.username.text() else "Manager"
            self.update_navigation_bar()
            self.check_and_award_rewards()
            if self.is_admin:
                self.page_stack.setCurrentWidget(self.manage_user_page)
                self.update_manage_user()
            else:
                self.page_stack.setCurrentWidget(self.home_page)
                self.update_pressure_diagram()
            QTimer.singleShot(100, self.update_pressure_diagram)
            QTimer.singleShot(200, self.update_dashboard)
            return True
        return False

    def update_navigation_bar(self):
        for i in reversed(range(self.nav_layout.count())):
            widget = self.nav_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        self.nav_buttons.clear()
        if self.is_admin:
            nav_button_texts = ["Manage User", "Manage Exercise", "Manage Community"]
        else:
            nav_button_texts = ["Home", "View Dashboard", "Get Reward", "Exercises List", "Community",
                                f"Hi {self.username}"]
        for text in nav_button_texts:
            button = QPushButton(text)
            button.clicked.connect(lambda checked, b=text: self.navigate(b))
            self.nav_layout.addWidget(button)
            self.nav_buttons.append(button)

    def logout(self):
        self.user_id = None
        self.is_admin = False
        self.username = "Guest"
        self.stress_before_level = None
        self.current_exercise = None
        self.timer_count = 0
        self.init_ui()
        QTimer.singleShot(100, self.update_ui_after_login)
        QTimer.singleShot(200, self.update_pressure_diagram)
        QTimer.singleShot(300, self.update_dashboard)

    def update_ui_after_login(self):
        if self.is_admin:
            nav_button_texts = ["Manage User", "Manage Exercise", "Manage Community"]
        else:
            nav_button_texts = ["Home", "View Dashboard", "Get Reward", "Exercises List", "Community",
                                f"Hi {self.username}"]
        for i, button in enumerate(self.nav_buttons):
            button.setText(nav_button_texts[i])
            button.clicked.disconnect()
            button.clicked.connect(lambda checked, b=nav_button_texts[i]: self.navigate(b))

    def get_motivational_quote(self):
        quotes = [
            "Every deep breath is a step toward calm—relax, you are stronger than you think!",
            "Mindfulness is the key to inner peace. Take a moment for yourself.",
            "With each breath, you grow stronger and more resilient."
        ]
        return random.choice(quotes)

    def get_sample_comment(self):
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT id, content, date, comments FROM community_posts")
            posts = c.fetchall()
            if not posts:
                return "No community posts available yet. Be the first to share your experience!"
            max_comments = -1
            selected_post = None
            for post in posts:
                comments = post[3] or ""
                comment_count = comments.count("\n") + 1 if comments else 0
                if comment_count > max_comments:
                    max_comments = comment_count
                    selected_post = post
            if selected_post:
                return f"{selected_post[1]}\nSee More\n{selected_post[2].split()[0]}"
            else:
                return "No community posts with comments yet. Share your thoughts!"

    def plot_stress_diagram(self, canvas, title, data):
        canvas.axes.clear()
        if self.user_id is None and not self.is_admin:
            canvas.axes.text(0.5, 0.5, "Please login to view your stress data",
                             horizontalalignment='center',
                             verticalalignment='center',
                             transform=canvas.axes.transAxes)
            canvas.axes.set_title(title)
        else:
            if data:
                dates = [row[0] for row in data]
                stress_before = [row[2] for row in data]
                stress_after = [row[3] for row in data]
                percentages = [row[4] for row in data]
                ax1 = canvas.axes
                ax2 = ax1.twinx()
                ax1.plot(dates, stress_before, label="Before", marker='o', color='blue')
                ax1.plot(dates, stress_after, label="After", marker='o', color='green')
                ax1.set_ylim(0, 10)
                ax1.set_ylabel("Stress Level (0-10)")
                ax1.tick_params(axis='y', labelcolor='black')
                ax1.legend(loc='upper left')
                ax2.plot(dates, percentages, label="Completion %", marker='s', linestyle='--', color='orange')
                ax2.set_ylim(0, 110)
                ax2.set_ylabel("Completion % (0-100)")
                ax2.tick_params(axis='y', labelcolor='black')
                ax2.legend(loc='upper right')
                canvas.axes.set_title(title)
                canvas.axes.set_xlabel("Date")
                canvas.axes.tick_params(axis='x', rotation=45)
            else:
                canvas.axes.text(0.5, 0.5, "No data available",
                                 horizontalalignment='center',
                                 verticalalignment='center',
                                 transform=canvas.axes.transAxes)
                canvas.axes.set_title(title)
        canvas.draw()

    def update_pressure_diagram(self):
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute(
            "SELECT date, exercise_type, stress_before, stress_after, duration_percentage, notes FROM stress_levels WHERE user_id=? ORDER BY date",
            (self.user_id,))
        data = c.fetchall()
        conn.close()
        self.plot_stress_diagram(self.canvas, "Pressure Change Diagram", data)

    def update_dashboard(self, selected_date=None):
        if self.user_id is None:
            self.progress_label.setText("Please login to view your progress")
            self.date_label.setText("Please login to view records")
            self.canvas_dashboard.hide()
            self.session_table.setRowCount(0)
            return
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        if selected_date:
            query_date = selected_date.toString("yyyy-MM-dd")
            c.execute(
                "SELECT date, exercise_type, stress_before, stress_after, duration_percentage, notes FROM stress_levels WHERE user_id=? AND date LIKE ? ORDER BY date",
                (self.user_id, f"{query_date}%"))
            self.date_label.setText(f"Showing records for {query_date}")
            self.canvas_dashboard.hide()
        else:
            c.execute(
                "SELECT date, exercise_type, stress_before, stress_after, duration_percentage, notes FROM stress_levels WHERE user_id=? ORDER BY date",
                (self.user_id,))
            self.date_label.setText("Showing all records")
            self.canvas_dashboard.show()
        data = c.fetchall()
        conn.close()
        self.progress_label.setText(f"Completed Exercises: {len(data)}")
        if not selected_date:
            self.plot_stress_diagram(self.canvas_dashboard, "Stress Level and Completion % Trends", data)
        self.session_table.setRowCount(len(data))
        if not data and selected_date:
            self.session_table.setRowCount(1)
            self.session_table.setItem(0, 0, QTableWidgetItem("No records for this date"))
        else:
            for i, row in enumerate(data):
                for j, value in enumerate(row):
                    if j == 4 and value is not None:
                        self.session_table.setItem(i, j, QTableWidgetItem(str(builtins.round(float(value), 1))))
                    else:
                        self.session_table.setItem(i, j, QTableWidgetItem(str(value) if value is not None else ""))

    def update_dashboard_by_date(self):
        selected_date = self.calendar.selectedDate()
        self.update_dashboard(selected_date)

    def show_comment_dialog(self, frame):
        if self.user_id is None:
            QMessageBox.warning(self, "Login Required", "Please login to comment")
            if not self.show_login_dialog():
                self.page_stack.setCurrentWidget(self.home_page)
                return
        from PyQt6.QtWidgets import QInputDialog
        post_id = frame.property("post_id")
        comment, ok = QInputDialog.getText(self, "Add Comment", "Enter your comment:")
        if ok and comment:
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute("SELECT comments FROM community_posts WHERE id=?", (post_id,))
            current_comments = c.fetchone()
            new_comments = current_comments[
                               0] + f"\nAnonymous ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): {comment}" if current_comments and \
                                                                                                                  current_comments[
                                                                                                                      0] else f"Anonymous ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): {comment}"
            c.execute("UPDATE community_posts SET comments=? WHERE id=?", (new_comments, post_id))
            conn.commit()
            conn.close()
            self.update_posts()
            QMessageBox.information(self, "Success", "Comment added!")

    def update_posts(self):
        for i in reversed(range(self.posts_layout.count())):
            widget = self.posts_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()
        c.execute("SELECT id, content, date, comments FROM community_posts ORDER BY date DESC")
        posts = c.fetchall()
        conn.close()
        for post in posts:
            post_frame = QFrame()
            post_frame.setStyleSheet("""
                background-color: #222;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            """)
            post_layout = QVBoxLayout()
            content_label = QLabel(f"Post ({post[2]}):\n{post[1]}")
            content_label.setStyleSheet("""
                font-size: 14px;
                color: #E0E0E0;
                font-weight: bold;
                margin-bottom: 10px;
            """)
            content_label.setWordWrap(True)
            post_layout.addWidget(content_label)
            comments_label = QLabel(f"Comments:\n{post[3] or 'No comments yet'}")
            comments_label.setStyleSheet("""
                font-size: 12px;
                color: #B0B0B0;
                font-style: italic;
            """)
            comments_label.setWordWrap(True)
            post_layout.addWidget(comments_label)
            post_frame.setLayout(post_layout)
            post_frame.setProperty("post_id", post[0])
            post_frame.mouseDoubleClickEvent = lambda event, frame=post_frame: self.show_comment_dialog(frame)
            self.posts_layout.insertWidget(0, post_frame)
        self.posts_layout.addStretch()

def main():
    app = QApplication(sys.argv)
    init_db()
    window = MBSRApp()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
