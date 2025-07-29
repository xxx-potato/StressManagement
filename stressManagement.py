import sys
import sqlite3
from datetime import datetime
import random
import builtins
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox,
                             QMessageBox, QStackedWidget, QFormLayout, QDialog, QTableWidget,
                             QTableWidgetItem, QScrollArea, QProgressBar, QListWidget, QListWidgetItem,
                             QCalendarWidget, QDialogButtonBox, QSpinBox, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QDate, QLocale
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


# Database setup
def init_db():
    try:
        conn = sqlite3.connect('mbsr_data.db')
        c = conn.cursor()

        # Enable foreign key support
        c.execute("PRAGMA foreign_keys = ON")

        # Create exercises table
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exercises'")
        if not c.fetchone():
            c.execute('''CREATE TABLE exercises (
                         id INTEGER PRIMARY KEY AUTOINCREMENT,
                         name TEXT,
                         description TEXT,
                         video_url TEXT,
                         stress_level_min INTEGER,
                         stress_level_max INTEGER)''')

        # Check and add missing columns in exercises table
        c.execute("PRAGMA table_info(exercises)")
        columns = {row[1] for row in c.fetchall()}
        if 'stress_level_min' not in columns:
            c.execute("ALTER TABLE exercises ADD COLUMN stress_level_min INTEGER")
        if 'stress_level_max' not in columns:
            c.execute("ALTER TABLE exercises ADD COLUMN stress_level_max INTEGER")

        # Clear existing exercises
        c.execute("DELETE FROM exercises")

        # Insert exercises
        c.execute(
            "INSERT INTO exercises (name, description, video_url, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?, ?)",
            ("Mindful Breathing 1", "Focus on slow inhales and exhales for 5 minutes to promote relaxation.", "", 1, 3))
        c.execute(
            "INSERT INTO exercises (name, description, video_url, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?, ?)",
            ("Mindful Breathing 2", "Count breaths from 1 to 10, then repeat, enhancing focus and calm.", "", 4, 6))
        c.execute(
            "INSERT INTO exercises (name, description, video_url, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?, ?)",
            (
            "Body Scan", "A guided practice to progressively relax each part of the body from head to toe.", "", 7, 10))
        c.execute(
            "INSERT INTO exercises (name, description, video_url, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?, ?)",
            ("Walking Meditation", "Mindful walking for 10 minutes to improve awareness and reduce stress.", "", 3, 5))
        c.execute(
            "INSERT INTO exercises (name, description, video_url, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?, ?)",
            ("Loving-Kindness Meditation", "Cultivate compassion by sending positive thoughts to yourself and others.",
             "", 2, 4))
        c.execute(
            "INSERT INTO exercises (name, description, video_url, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?, ?)",
            ("Gentle Stretching", "Simple stretching to release physical tension and calm the mind.", "", 1, 10))

        # Create users table
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     username TEXT UNIQUE,
                     password TEXT,
                     is_admin INTEGER DEFAULT 0)''')

        # Create stress_levels table with foreign key
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

        # Create community_posts table with foreign key
        c.execute('''CREATE TABLE IF NOT EXISTS community_posts (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     user_id INTEGER,
                     content TEXT,
                     date TEXT,
                     comments TEXT DEFAULT '',
                     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE)''')

        # Add duration_percentage column if missing
        c.execute("PRAGMA table_info(stress_levels)")
        columns = {row[1] for row in c.fetchall()}
        if 'duration_percentage' not in columns:
            c.execute("ALTER TABLE stress_levels ADD COLUMN duration_percentage REAL DEFAULT 0.0")

        conn.commit()
    except sqlite3.Error as e:
        QMessageBox.critical(None, "Database Error", f"Database initialization failed: {str(e)}")
    finally:
        conn.close()


# Matplotlib canvas for pressure change diagram
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure()
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


# User Details Dialog
class UserDetailsDialog(QDialog):
    def __init__(self, user_id, username, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.setWindowTitle(f"User Details: {username}")
        self.layout = QVBoxLayout()

        # Stress diagram
        self.canvas = MplCanvas(self)
        self.update_stress_diagram()
        self.layout.addWidget(self.canvas)

        # Session table
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(6)
        self.session_table.setHorizontalHeaderLabels(
            ["Date", "Exercise", "Stress Before", "Stress After", "Completion %", "Notes"])
        self.layout.addWidget(self.session_table)
        self.update_session_table()

        # Delete user button
        delete_btn = QPushButton("Delete User")
        delete_btn.clicked.connect(self.delete_user)
        self.layout.addWidget(delete_btn)

        self.setLayout(self.layout)

    def update_stress_diagram(self):
        try:
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
        except sqlite3.Error as e:
            self.canvas.axes.clear()
            self.canvas.axes.text(0.5, 0.5, f"Error: {str(e)}",
                                  horizontalalignment='center',
                                  verticalalignment='center',
                                  transform=self.canvas.axes.transAxes)
            self.canvas.draw()

    def update_session_table(self):
        try:
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
        except sqlite3.Error as e:
            self.session_table.setRowCount(1)
            self.session_table.setItem(0, 0, QTableWidgetItem(f"Error: {str(e)}"))

    def delete_user(self):
        try:
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
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete user: {str(e)}")


# Exercise Edit Dialog
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


# Login Dialog
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
        try:
            if not self.username.text() or not self.password.text():
                QMessageBox.warning(self, "Error", "Username and password cannot be empty")
                return
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            if self.username.text() == "manager" and self.password.text() == "manager":
                self.user_id = 0  # Special ID for manager
                self.is_admin = True
                self.accept()
            else:
                c.execute("SELECT id, is_admin FROM users WHERE username=? AND password=?",
                          (self.username.text(), self.password.text()))
                user = c.fetchone()
                if user:
                    self.user_id, self.is_admin = user
                    self.accept()
                else:
                    QMessageBox.warning(self, "Error", "Invalid username or password")
            conn.close()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Login failed: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")

    def handle_register(self):
        try:
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
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "Registration successful! Please login.")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Username already exists")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Registration failed: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")


# Main Application Window
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

        # Navigation bar
        self.nav_layout = QHBoxLayout()
        if self.is_admin:
            nav_button_texts = ["Manage User", "Manage Exercise", "Manage Community"]
        else:
            nav_button_texts = ["Home", "View Dashboard", "Get Reward", "Exercises List", "Community",
                                "register, login / Hi name"]
        for text in nav_button_texts:
            button = QPushButton(text)
            button.clicked.connect(lambda checked, b=text: self.navigate(b))
            self.nav_layout.addWidget(button)
            self.nav_buttons.append(button)
        main_layout.addLayout(self.nav_layout)

        # Pages
        self.page_stack = QStackedWidget()
        self.home_page = self.create_home_page()
        self.dashboard_page = self.create_dashboard_page()
        self.exercise_list_page = self.create_exercise_list_page()
        self.exercise_assessment_page = self.create_exercise_assessment_page()
        self.exercise_recommendation_page = self.create_exercise_recommendation_page()
        self.exercise_completion_page = self.create_exercise_completion_page()
        self.community_page = self.create_community_page()
        self.reward_page = self.create_reward_page()
        self.login_page = self.create_login_page()
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
        self.page_stack.addWidget(self.login_page)
        self.page_stack.addWidget(self.manage_user_page)
        self.page_stack.addWidget(self.manage_exercise_page)
        self.page_stack.addWidget(self.manage_community_page)

        main_layout.addWidget(self.page_stack)
        self.page_stack.setCurrentWidget(self.manage_user_page if self.is_admin else self.home_page)

    def navigate(self, page):
        try:
            if self.user_id is None and page != "register, login / Hi name":
                QMessageBox.warning(self, "Login Required", "Please login to access this feature")
                self.page_stack.setCurrentWidget(self.login_page)
                return
            if page == "Home":
                self.page_stack.setCurrentWidget(self.home_page)
                self.update_pressure_diagram()
            elif page == "View Dashboard":
                self.page_stack.setCurrentWidget(self.dashboard_page)
                QTimer.singleShot(100, self.update_dashboard)
            elif page == "Get Reward":
                self.page_stack.setCurrentWidget(self.reward_page)
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
            elif page == "register, login / Hi name":
                if self.user_id is None:
                    self.show_login_dialog()
                else:
                    self.logout()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Navigation failed: {str(e)}")

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.canvas = MplCanvas(self)
        self.update_pressure_diagram()
        layout.addWidget(self.canvas)

        text_label = QLabel(
            "You've already made great progress, and that's fantastic! Keep pushing forward, and the future you will be even prouder!")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)

        lets_go_btn = QPushButton("Let's Go!")
        lets_go_btn.clicked.connect(self.start_exercise)
        layout.addWidget(lets_go_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        quote_label = QLabel(self.get_motivational_quote())
        quote_label.setStyleSheet("border: 1px solid gray; padding: 10px;")
        layout.addWidget(quote_label)

        comment_label = QLabel(self.get_sample_comment())
        comment_label.setStyleSheet("border: 1px solid gray; padding: 10px;")
        layout.addWidget(comment_label)

        page.setLayout(layout)
        return page

    def start_exercise(self):
        try:
            if self.user_id is None:
                QMessageBox.warning(self, "Login Required", "Please login to access exercises")
                if not self.show_login_dialog():
                    self.page_stack.setCurrentWidget(self.home_page)
                    return
            self.page_stack.setCurrentWidget(self.exercise_assessment_page)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start exercise: {str(e)}")

    def create_dashboard_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        # Calendar and reset button
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

        # Date display label
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
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        try:
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute("SELECT name, description FROM exercises")
            exercises = c.fetchall()
            conn.close()

            for exercise in exercises:
                exercise_label = QLabel(f"Exercise: {exercise[0]}")
                desc_label = QLabel(f"Description: {exercise[1]}")
                content_layout.addWidget(exercise_label)
                content_layout.addWidget(desc_label)
                content_layout.addWidget(QLabel("---"))
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load exercises: {str(e)}")

        content_layout.addStretch()
        scroll_area.setWidget(content_widget)
        scroll_area.setWidgetResizable(True)
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
        layout.addWidget(self.recommendation_label)

        self.exercise_content = QTextEdit()
        self.exercise_content.setReadOnly(True)
        layout.addWidget(self.exercise_content)
        self.exercise_content.hide()

        self.timer_label = QLabel("Time remaining: 5:00")
        self.timer_progress = QProgressBar()
        self.timer_progress.setMaximum(300)
        self.timer_progress.setValue(0)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.timer_progress)
        self.timer_label.hide()
        self.timer_progress.hide()

        buttons_layout = QHBoxLayout()
        finish_btn = QPushButton("Finish")
        finish_btn.clicked.connect(lambda: self.end_exercise(complete=True))
        buttons_layout.addWidget(finish_btn)
        end_early_btn = QPushButton("End Early")
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
        try:
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute("SELECT id, username FROM users WHERE username != 'manager'")
            users = c.fetchall()
            self.user_table.setRowCount(len(users))
            for i, (user_id, username) in enumerate(users):
                c.execute("SELECT AVG(duration_percentage) FROM stress_levels WHERE user_id=?", (user_id,))
                avg_completion = c.fetchone()[0]
                self.user_table.setItem(i, 0, QTableWidgetItem(username))
                self.user_table.setItem(i, 1, QTableWidgetItem(str(builtins.round(float(avg_completion), 1)) if avg_completion else "0.0"))
                self.user_table.setProperty("user_id", user_id)
            conn.close()
        except sqlite3.Error as e:
            self.user_table.setRowCount(1)
            self.user_table.setItem(0, 0, QTableWidgetItem(f"Error: {str(e)}"))

    def show_user_details(self, user_id, username):
        try:
            dialog = UserDetailsDialog(user_id, username, self)
            dialog.exec()
            self.update_manage_user()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to show user details: {str(e)}")

    def add_exercise(self):
        try:
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
                    "INSERT INTO exercises (name, description, video_url, stress_level_min, stress_level_max) VALUES (?, ?, ?, ?, ?)",
                    (name, description, "", min_level, max_level))
                conn.commit()
                conn.close()
                self.update_manage_exercise()
                QMessageBox.information(self, "Success", "Exercise added successfully")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add exercise: {str(e)}")

    def edit_exercise(self, row, column):
        try:
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
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to edit/delete exercise: {str(e)}")

    def update_manage_exercise(self):
        try:
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute("SELECT name, description, stress_level_min, stress_level_max FROM exercises")
            exercises = c.fetchall()
            conn.close()
            self.exercise_table.setRowCount(len(exercises))
            for i, exercise in enumerate(exercises):
                for j, value in enumerate(exercise):
                    self.exercise_table.setItem(i, j, QTableWidgetItem(str(value)))
        except sqlite3.Error as e:
            self.exercise_table.setRowCount(1)
            self.exercise_table.setItem(0, 0, QTableWidgetItem(f"Error: {str(e)}"))

    def update_manage_community(self):
        try:
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
        except sqlite3.Error as e:
            self.community_list.addItem(QListWidgetItem(f"Failed to load posts: {str(e)}"))

    def delete_post(self, item):
        try:
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
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete post: {str(e)}")

    def assess_stress(self):
        try:
            if self.user_id is None:
                QMessageBox.warning(self, "Login Required", "Please login to access exercises")
                if not self.show_login_dialog():
                    self.page_stack.setCurrentWidget(self.home_page)
                    return
            self.stress_before_level = int(self.stress_before_combo.currentText())
            QMessageBox.information(self, "Success", f"Stress level {self.stress_before_level} recorded")
            self.page_stack.setCurrentWidget(self.exercise_recommendation_page)
            self.recommend_exercise()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to assess stress: {str(e)}")

    def recommend_exercise(self):
        try:
            if self.user_id is None:
                QMessageBox.warning(self, "Login Required", "Please login to access exercises")
                if not self.show_login_dialog():
                    self.page_stack.setCurrentWidget(self.home_page)
                    return

            if self.stress_before_level is None:
                self.recommendation_label.setText(
                    "No stress level assessed. Please go back and assess your stress level.")
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
                self.exercise_content.setText(selected_exercise[1])
                self.exercise_content.show()
                self.finish_btn.show()
                self.end_early_btn.show()
                self.timer_count = 300
                self.timer = QTimer()
                self.timer.timeout.connect(self.update_timer)
                self.timer.start(1000)
                self.timer_label.show()
                self.timer_progress.show()
            else:
                self.recommendation_label.setText("No exercises available in the database. Please contact support.")
                self.exercise_content.hide()
                self.finish_btn.hide()
                self.end_early_btn.hide()
                self.timer_label.hide()
                self.timer_progress.hide()
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load exercises: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")

    def update_timer(self):
        try:
            self.timer_count -= 1
            minutes = self.timer_count // 60
            seconds = self.timer_count % 60
            self.timer_label.setText(f"Time remaining: {minutes}:{seconds:02d}")
            self.timer_progress.setValue(300 - self.timer_count)
            if self.timer_count <= 0:
                self.timer.stop()
                QMessageBox.information(self, "Time's Up", "Exercise duration completed!")
                self.end_exercise(complete=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Timer update failed: {str(e)}")

    def end_exercise(self, complete=True):
        try:
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()
            duration_percentage = min((300 - self.timer_count) / 300 * 100, 100.0) if self.timer_count > 0 else 0.0
            if not complete:
                QMessageBox.information(self, "Exercise Ended",
                                        f"Exercise ended early. Completion: {duration_percentage:.1f}%")
            self.page_stack.setCurrentWidget(self.exercise_completion_page)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to end exercise: {str(e)}")

    def submit_exercise(self):
        try:
            if self.user_id is None:
                QMessageBox.warning(self, "Login Required", "Please login to submit")
                if not self.show_login_dialog():
                    self.page_stack.setCurrentWidget(self.home_page)
                    return

            if self.current_exercise is None:
                QMessageBox.warning(self, "Error", "No exercise selected. Please start a new exercise.")
                self.page_stack.setCurrentWidget(self.exercise_assessment_page)
                return

            duration_percentage = min((300 - self.timer_count) / 300 * 100, 100.0) if self.timer_count > 0 else 0.0
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute(
                "INSERT INTO stress_levels (user_id, date, stress_before, stress_after, exercise_type, notes, duration_percentage) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (self.user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                 self.stress_before_level,
                 int(self.stress_after_combo.currentText()),
                 self.current_exercise,
                 self.notes_input.toPlainText(),
                 duration_percentage))
            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success",
                                    f"Exercise completed and data saved! Completion: {duration_percentage:.1f}%")
            self.notes_input.clear()
            QTimer.singleShot(100, self.update_dashboard)
            QTimer.singleShot(200, self.update_pressure_diagram)
            self.page_stack.setCurrentWidget(self.home_page)
            self.stress_before_level = None
            self.current_exercise = None
            self.timer_count = 0
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to save exercise data: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")

    def create_community_page(self):
        page = QWidget()
        layout = QVBoxLayout()

        anonymous_label = QLabel("Posts are shared anonymously")
        anonymous_label.setStyleSheet("font-weight: bold; color: #555;")
        layout.addWidget(anonymous_label)

        self.post_input = QTextEdit()
        self.post_input.setPlaceholderText("Share your experience anonymously...")
        layout.addWidget(self.post_input)

        post_btn = QPushButton("Post")
        post_btn.clicked.connect(self.share_post)
        layout.addWidget(post_btn)

        self.posts_list = QListWidget()
        self.posts_list.itemDoubleClicked.connect(self.show_comment_dialog)
        layout.addWidget(self.posts_list)

        page.setLayout(layout)
        self.update_posts()
        return page

    def create_reward_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        label = QLabel("Congratulations! You've earned a reward!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        page.setLayout(layout)
        return page

    def create_login_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        login_dialog = LoginDialog()
        layout.addWidget(login_dialog)
        page.setLayout(layout)
        return page

    def show_login_dialog(self):
        try:
            login_dialog = LoginDialog()
            if login_dialog.exec():
                self.user_id = login_dialog.user_id
                self.is_admin = login_dialog.is_admin
                self.username = login_dialog.username.text() if login_dialog.username.text() else "Manager"

                # 更新导航栏
                self.update_navigation_bar()

                # 如果是管理员，直接切换到 Manage User 页面
                if self.is_admin:
                    self.page_stack.setCurrentWidget(self.manage_user_page)
                else:
                    self.page_stack.setCurrentWidget(self.home_page)

                QTimer.singleShot(100, self.update_pressure_diagram)
                QTimer.singleShot(200, self.update_dashboard)
                return True
            return False
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Login dialog failed: {str(e)}")
            return False

    def update_navigation_bar(self):
        # 清除旧的导航栏按钮
        for i in reversed(range(self.nav_layout.count())):
            widget = self.nav_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 清空 nav_buttons 列表
        self.nav_buttons.clear()

        # 根据用户角色添加新按钮
        if self.is_admin:
            nav_button_texts = ["Manage User", "Manage Exercise", "Manage Community"]
        else:
            nav_button_texts = ["Home", "View Dashboard", "Get Reward", "Exercises List", "Community",
                                f"Hi {self.username}"]

        # 创建新按钮并添加到布局
        for text in nav_button_texts:
            button = QPushButton(text)
            button.clicked.connect(lambda checked, b=text: self.navigate(b))
            self.nav_layout.addWidget(button)
            self.nav_buttons.append(button)
    def logout(self):
        try:
            self.user_id = None
            self.is_admin = False
            self.username = "Guest"
            self.stress_before_level = None
            self.current_exercise = None
            self.timer_count = 0
            self.init_ui()  # Reinitialize UI for guest view
            QTimer.singleShot(100, self.update_ui_after_login)
            QTimer.singleShot(200, self.update_pressure_diagram)
            QTimer.singleShot(300, self.update_dashboard)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Logout failed: {str(e)}")

    def update_ui_after_login(self):
        try:
            if self.is_admin:
                nav_button_texts = ["Manage User", "Manage Exercise", "Manage Community"]
            else:
                nav_button_texts = ["Home", "View Dashboard", "Get Reward", "Exercises List", "Community",
                                    f"Hi {self.username}"]
            for i, button in enumerate(self.nav_buttons):
                button.setText(nav_button_texts[i])
                button.clicked.disconnect()
                button.clicked.connect(lambda checked, b=nav_button_texts[i]: self.navigate(b))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update UI: {str(e)}")

    def get_motivational_quote(self):
        quotes = [
            "Every deep breath is a step toward calm—relax, you are stronger than you think!",
            "Mindfulness is the key to inner peace. Take a moment for yourself.",
            "With each breath, you grow stronger and more resilient."
        ]
        return random.choice(quotes)

    def get_sample_comment(self):
        comments = [
            "After using this software for a few weeks, I've noticed a real difference in how I handle stress. The guided exercises, like the MBSR feature, have given me practical tools to unwind, especially during hectic days.",
            "This app has been a game-changer! The breathing exercises help me stay focused and calm."
        ]
        return random.choice(comments) + "\nSee More\n1 week ago"

    def plot_stress_diagram(self, canvas, title, data):
        try:
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
                    canvas.axes.plot(dates, stress_before, label="Before", marker='o', color='blue')
                    canvas.axes.plot(dates, stress_after, label="After", marker='o', color='green')
                    canvas.axes.plot(dates, percentages, label="Completion %", marker='s', linestyle='--',
                                     color='orange')
                    canvas.axes.legend()
                    canvas.axes.set_title(title)
                    canvas.axes.set_xlabel("Date")
                    canvas.axes.set_ylabel("Value")
                    canvas.axes.tick_params(axis='x', rotation=45)
                else:
                    canvas.axes.text(0.5, 0.5, "No data available",
                                     horizontalalignment='center',
                                     verticalalignment='center',
                                     transform=canvas.axes.transAxes)
                    canvas.axes.set_title(title)
            canvas.draw()
        except Exception as e:
            canvas.axes.clear()
            canvas.axes.text(0.5, 0.5, f"Error: {str(e)}",
                             horizontalalignment='center',
                             verticalalignment='center',
                             transform=canvas.axes.transAxes)
            canvas.draw()

    def update_pressure_diagram(self):
        try:
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute(
                "SELECT date, exercise_type, stress_before, stress_after, duration_percentage, notes FROM stress_levels WHERE user_id=? ORDER BY date",
                (self.user_id,))
            data = c.fetchall()
            conn.close()
            self.plot_stress_diagram(self.canvas, "Pressure Change Diagram", data)
        except sqlite3.Error as e:
            self.plot_stress_diagram(self.canvas, "Error in Pressure Change Diagram", [])

    def update_dashboard(self, selected_date=None):
        try:
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
        except Exception as e:
            self.progress_label.setText(f"Error: {str(e)}")
            self.date_label.setText("Error loading records")
            self.canvas_dashboard.hide()
            self.session_table.setRowCount(0)

    def update_dashboard_by_date(self):
        selected_date = self.calendar.selectedDate()
        self.update_dashboard(selected_date)

    def share_post(self):
        try:
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
            QMessageBox.information(self, "Success", "Post shared anonymously!")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to share post: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")

    def show_comment_dialog(self, item):
        try:
            if self.user_id is None:
                QMessageBox.warning(self, "Login Required", "Please login to comment")
                if not self.show_login_dialog():
                    self.page_stack.setCurrentWidget(self.home_page)
                    return
            from PyQt6.QtWidgets import QInputDialog
            post_id = item.data(Qt.ItemDataRole.UserRole)
            comment, ok = QInputDialog.getText(self, "Add Comment", "Enter your comment:")
            if ok and comment:
                conn = sqlite3.connect('mbsr_data.db')
                c = conn.cursor()
                c.execute("SELECT comments FROM community_posts WHERE id=?", (post_id,))
                current_comments = c.fetchone()[0] or ""
                new_comments = current_comments + f"\nAnonymous ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}): {comment}"
                c.execute("UPDATE community_posts SET comments=? WHERE id=?", (new_comments, post_id))
                conn.commit()
                conn.close()
                self.update_posts()
                QMessageBox.information(self, "Success", "Comment added!")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add comment: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error: {str(e)}")

    def update_posts(self):
        try:
            self.posts_list.clear()
            conn = sqlite3.connect('mbsr_data.db')
            c = conn.cursor()
            c.execute("SELECT id, content, date, comments FROM community_posts ORDER BY date DESC")
            posts = c.fetchall()
            conn.close()
            for post in posts:
                display_text = f"Post ({post[2]}):\n{post[1]}\nComments:\n{post[3] or 'No comments yet'}"
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, post[0])
                self.posts_list.addItem(item)
        except sqlite3.Error as e:
            self.posts_list.addItem(QListWidgetItem(f"Failed to load posts: {str(e)}"))
        except Exception as e:
            self.posts_list.addItem(QListWidgetItem(f"Error: {str(e)}"))


def main():
    try:
        app = QApplication(sys.argv)
        init_db()
        window = MBSRApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()