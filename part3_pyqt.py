"""PyQt5 graphical interface for the School Management System.

Provides forms to add, update and delete students, instructors and courses,
tables listing all records with live search, and a File menu for JSON,
CSV and database backup operations.
"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from part1_oop import ValidationError
from part4_database import DEFAULT_DB, Database


class SchoolWindow(QMainWindow):
    """Main window of the PyQt5 School Management System.

    :param db_path: Path of the SQLite database file, defaults to ``school.db``
    :type db_path: str, optional
    """
    def __init__(self, db_path=DEFAULT_DB):
        """Constructor method, builds the interface and loads the records."""
        super().__init__()
        self.setWindowTitle("School Management System")
        self.resize(1180, 740)

        self.db = Database(db_path)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.addWidget(self._build_forms(), 0)
        layout.addWidget(self._build_records(), 1)

        self._build_menu()
        self.statusBar().showMessage(f"Connected to {os.path.abspath(db_path)}")
        self.refresh_all()

    def _build_menu(self):
        """Create the File menu and its actions."""
        filemenu = self.menuBar().addMenu("&File")
        filemenu.addAction("New (clear all records)", self.new_file)
        filemenu.addSeparator()
        filemenu.addAction("Save data to JSON...", self.save_json)
        filemenu.addAction("Load data from JSON...", self.load_json)
        filemenu.addSeparator()
        filemenu.addAction("Export current tab to CSV...", self.export_csv)
        filemenu.addSeparator()
        filemenu.addAction("Backup database...", self.backup_db)
        filemenu.addAction("Restore database...", self.restore_db)
        filemenu.addSeparator()
        filemenu.addAction("Exit", self.close)

    def _build_forms(self):
        """Build the left panel with the student, instructor and course forms.

        :return: The panel widget
        :rtype: QWidget
        """
        panel = QWidget()
        panel.setFixedWidth(340)
        layout = QVBoxLayout(panel)

        student_box = QGroupBox("Student")
        student_form = QFormLayout(student_box)
        self.s_id = QLineEdit()
        self.s_name = QLineEdit()
        self.s_age = QLineEdit()
        self.s_age.setValidator(QIntValidator(0, 130, self))
        self.s_email = QLineEdit()
        self.s_email.setPlaceholderText("name@domain.com")
        student_form.addRow("Student ID", self.s_id)
        student_form.addRow("Name", self.s_name)
        student_form.addRow("Age", self.s_age)
        student_form.addRow("Email", self.s_email)

        student_buttons = QHBoxLayout()
        for text, slot in (("Add", self.add_student),
                           ("Update", self.update_student),
                           ("Clear", self.clear_student_form)):
            button = QPushButton(text)
            button.clicked.connect(slot)
            student_buttons.addWidget(button)
        student_form.addRow(student_buttons)

        self.s_course_box = QComboBox()
        student_form.addRow(QLabel("Register in course"))
        student_form.addRow(self.s_course_box)
        registration = QHBoxLayout()
        register_button = QPushButton("Register")
        register_button.clicked.connect(self.register_course)
        drop_button = QPushButton("Drop")
        drop_button.clicked.connect(self.drop_course)
        registration.addWidget(register_button)
        registration.addWidget(drop_button)
        student_form.addRow(registration)
        layout.addWidget(student_box)

        instructor_box = QGroupBox("Instructor")
        instructor_form = QFormLayout(instructor_box)
        self.i_id = QLineEdit()
        self.i_name = QLineEdit()
        self.i_age = QLineEdit()
        self.i_age.setValidator(QIntValidator(0, 130, self))
        self.i_email = QLineEdit()
        self.i_email.setPlaceholderText("name@domain.com")
        instructor_form.addRow("Instructor ID", self.i_id)
        instructor_form.addRow("Name", self.i_name)
        instructor_form.addRow("Age", self.i_age)
        instructor_form.addRow("Email", self.i_email)

        instructor_buttons = QHBoxLayout()
        for text, slot in (("Add", self.add_instructor),
                           ("Update", self.update_instructor),
                           ("Clear", self.clear_instructor_form)):
            button = QPushButton(text)
            button.clicked.connect(slot)
            instructor_buttons.addWidget(button)
        instructor_form.addRow(instructor_buttons)

        self.i_course_box = QComboBox()
        instructor_form.addRow(QLabel("Assign to course"))
        instructor_form.addRow(self.i_course_box)
        assign_button = QPushButton("Assign course")
        assign_button.clicked.connect(self.assign_course)
        instructor_form.addRow(assign_button)
        layout.addWidget(instructor_box)

        course_box = QGroupBox("Course")
        course_form = QFormLayout(course_box)
        self.c_id = QLineEdit()
        self.c_name = QLineEdit()
        self.c_instructor_box = QComboBox()
        course_form.addRow("Course ID", self.c_id)
        course_form.addRow("Course name", self.c_name)
        course_form.addRow("Instructor", self.c_instructor_box)

        course_buttons = QHBoxLayout()
        for text, slot in (("Add", self.add_course),
                           ("Update", self.update_course),
                           ("Clear", self.clear_course_form)):
            button = QPushButton(text)
            button.clicked.connect(slot)
            course_buttons.addWidget(button)
        course_form.addRow(course_buttons)
        layout.addWidget(course_box)

        layout.addStretch(1)
        return panel

    def _build_records(self):
        """Build the right panel with the search bar, record tables and actions.

        :return: The panel widget
        :rtype: QWidget
        """
        panel = QWidget()
        layout = QVBoxLayout(panel)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search (name / ID / course):"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("type to filter every table")
        self.search_edit.textChanged.connect(self.refresh_tables)
        search_row.addWidget(self.search_edit, 1)
        clear_search = QPushButton("Clear")
        clear_search.clicked.connect(self.search_edit.clear)
        search_row.addWidget(clear_search)
        layout.addLayout(search_row)

        self.tabs = QTabWidget()
        self.student_table = self._table(
            ["Student ID", "Name", "Age", "Email", "Registered courses"])
        self.instructor_table = self._table(
            ["Instructor ID", "Name", "Age", "Email", "Assigned courses"])
        self.course_table = self._table(
            ["Course ID", "Course name", "Instructor", "Enrolled students"])
        self.tabs.addTab(self.student_table, "Students")
        self.tabs.addTab(self.instructor_table, "Instructors")
        self.tabs.addTab(self.course_table, "Courses")
        layout.addWidget(self.tabs, 1)

        actions = QHBoxLayout()
        for text, slot in (("Edit selected (load into form)", self.edit_selected),
                           ("Delete selected", self.delete_selected),
                           ("Refresh", self.refresh_all)):
            button = QPushButton(text)
            button.clicked.connect(slot)
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)
        return panel

    def _table(self, headers):
        """Create a read-only, sortable, single row selection table.

        :param headers: Column header labels
        :type headers: list
        :return: The configured table
        :rtype: QTableWidget
        """
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        table.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
        return table

    def refresh_all(self):
        """Reload every table and dropdown from the database."""
        self.refresh_tables()
        self.refresh_dropdowns()

    def refresh_dropdowns(self):
        """Reload the course and instructor dropdowns, keeping the current selection."""
        courses = [f"{r['course_id']} - {r['course_name']}" for r in self.db.get_courses()]
        for box in (self.s_course_box, self.i_course_box):
            current = box.currentText()
            box.blockSignals(True)
            box.clear()
            box.addItems(courses)
            index = box.findText(current)
            box.setCurrentIndex(index if index >= 0 else -1)
            box.blockSignals(False)

        instructors = [""] + [f"{r['instructor_id']} - {r['name']}"
                              for r in self.db.get_instructors()]
        current = self.c_instructor_box.currentText()
        self.c_instructor_box.blockSignals(True)
        self.c_instructor_box.clear()
        self.c_instructor_box.addItems(instructors)
        index = self.c_instructor_box.findText(current)
        self.c_instructor_box.setCurrentIndex(max(index, 0))
        self.c_instructor_box.blockSignals(False)

    def refresh_tables(self):
        """Reload the tables, filtered by the current search text."""
        term = self.search_edit.text().strip().lower()

        def matches(*fields):
            return not term or any(term in str(f).lower()
                                   for f in fields if f is not None)

        student_rows = []
        for row in self.db.get_students():
            taken = self.db.courses_of_student(row["student_id"])
            courses = ", ".join(c["course_id"] for c in taken)
            titles = " ".join(c["course_name"] for c in taken)
            if matches(row["student_id"], row["name"], row["email"], courses, titles):
                student_rows.append([row["student_id"], row["name"], str(row["age"]),
                                     row["email"], courses])
        self._fill(self.student_table, student_rows)

        instructor_rows = []
        for row in self.db.get_instructors():
            taught = self.db.courses_of_instructor(row["instructor_id"])
            courses = ", ".join(c["course_id"] for c in taught)
            titles = " ".join(c["course_name"] for c in taught)
            if matches(row["instructor_id"], row["name"], row["email"], courses, titles):
                instructor_rows.append([row["instructor_id"], row["name"],
                                        str(row["age"]), row["email"], courses])
        self._fill(self.instructor_table, instructor_rows)

        course_rows = []
        for row in self.db.get_courses():
            students = ", ".join(s["student_id"]
                                 for s in self.db.students_of_course(row["course_id"]))
            if matches(row["course_id"], row["course_name"],
                       row["instructor_name"], students):
                course_rows.append([row["course_id"], row["course_name"],
                                    row["instructor_name"] or "-", students])
        self._fill(self.course_table, course_rows)

    @staticmethod
    def _fill(table, rows):
        """Fill a table with rows of text values.

        :param table: The table to fill
        :type table: QTableWidget
        :param rows: Rows of string values
        :type rows: list
        """
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for r, values in enumerate(rows):
            for c, value in enumerate(values):
                table.setItem(r, c, QTableWidgetItem(value))
        table.setSortingEnabled(True)

    def _guarded(self, action, success):
        """Run an action, reporting validation errors in a dialog.

        :param action: Callable performing the database change
        :type action: callable
        :param success: Status bar message shown on success
        :type success: str
        :return: ``True`` if the action succeeded, ``False`` otherwise
        :rtype: bool
        """
        try:
            action()
        except ValidationError as exc:
            QMessageBox.critical(self, "Invalid input", str(exc))
            return False
        self.refresh_all()
        self.statusBar().showMessage(success)
        return True

    @staticmethod
    def _id_from_combo(box):
        """Extract the record ID from a ``"ID - Name"`` dropdown entry.

        :param box: The dropdown
        :type box: QComboBox
        :return: The ID, or an empty string if nothing is selected
        :rtype: str
        """
        text = box.currentText()
        return text.split(" - ", 1)[0].strip() if text else ""

    def _current_table(self):
        """Return the name of the table in the active tab.

        :rtype: str
        """
        return ("students", "instructors", "courses")[self.tabs.currentIndex()]

    def _current_widget(self):
        """Return the table widget in the active tab.

        :rtype: QTableWidget
        """
        return (self.student_table, self.instructor_table,
                self.course_table)[self.tabs.currentIndex()]

    def _selected_row(self):
        """Return the values of the selected row in the active table.

        :return: The row values, or ``None`` if no row is selected
        :rtype: list or None
        """
        table = self._current_widget()
        rows = table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.information(
                self, "Nothing selected",
                f"Select a row in the {self._current_table()} table first.")
            return None
        index = rows[0].row()
        return [table.item(index, c).text() for c in range(table.columnCount())]

    def add_student(self):
        """Add a student from the student form."""
        self._guarded(
            lambda: self.db.add_student(self.s_id.text(), self.s_name.text(),
                                        self.s_age.text(), self.s_email.text()),
            f"Student '{self.s_id.text().strip()}' added.")

    def update_student(self):
        """Update the student identified in the student form."""
        self._guarded(
            lambda: self.db.update_student(self.s_id.text().strip(), self.s_name.text(),
                                           self.s_age.text(), self.s_email.text()),
            f"Student '{self.s_id.text().strip()}' updated.")

    def clear_student_form(self):
        """Clear every field of the student form."""
        for edit in (self.s_id, self.s_name, self.s_age, self.s_email):
            edit.clear()

    def register_course(self):
        """Register the student in the course selected in the dropdown."""
        student_id = self.s_id.text().strip()
        course_id = self._id_from_combo(self.s_course_box)
        if not student_id or not course_id:
            QMessageBox.information(
                self, "Missing data",
                "Enter or select a student ID and pick a course first.")
            return
        self._guarded(lambda: self.db.register_student(student_id, course_id),
                      f"{student_id} registered in {course_id}.")

    def drop_course(self):
        """Drop the course selected in the dropdown for the student."""
        student_id = self.s_id.text().strip()
        course_id = self._id_from_combo(self.s_course_box)
        if not student_id or not course_id:
            QMessageBox.information(self, "Missing data",
                                    "Select a student and a course first.")
            return
        self._guarded(lambda: self.db.unregister_student(student_id, course_id),
                      f"{student_id} dropped {course_id}.")

    def add_instructor(self):
        """Add an instructor from the instructor form."""
        self._guarded(
            lambda: self.db.add_instructor(self.i_id.text(), self.i_name.text(),
                                           self.i_age.text(), self.i_email.text()),
            f"Instructor '{self.i_id.text().strip()}' added.")

    def update_instructor(self):
        """Update the instructor identified in the instructor form."""
        self._guarded(
            lambda: self.db.update_instructor(self.i_id.text().strip(),
                                              self.i_name.text(), self.i_age.text(),
                                              self.i_email.text()),
            f"Instructor '{self.i_id.text().strip()}' updated.")

    def clear_instructor_form(self):
        """Clear every field of the instructor form."""
        for edit in (self.i_id, self.i_name, self.i_age, self.i_email):
            edit.clear()

    def assign_course(self):
        """Assign the instructor to the course selected in the dropdown."""
        instructor_id = self.i_id.text().strip()
        course_id = self._id_from_combo(self.i_course_box)
        if not instructor_id or not course_id:
            QMessageBox.information(self, "Missing data",
                                    "Select an instructor and a course first.")
            return
        self._guarded(lambda: self.db.assign_instructor(instructor_id, course_id),
                      f"{instructor_id} now teaches {course_id}.")

    def add_course(self):
        """Add a course from the course form."""
        instructor_id = self._id_from_combo(self.c_instructor_box) or None
        self._guarded(
            lambda: self.db.add_course(self.c_id.text(), self.c_name.text(),
                                       instructor_id),
            f"Course '{self.c_id.text().strip()}' added.")

    def update_course(self):
        """Update the course identified in the course form."""
        instructor_id = self._id_from_combo(self.c_instructor_box) or None
        self._guarded(
            lambda: self.db.update_course(self.c_id.text().strip(),
                                          self.c_name.text(), instructor_id),
            f"Course '{self.c_id.text().strip()}' updated.")

    def clear_course_form(self):
        """Clear every field of the course form."""
        self.c_id.clear()
        self.c_name.clear()
        self.c_instructor_box.setCurrentIndex(0)

    def edit_selected(self):
        """Load the selected table row into the matching form for editing."""
        values = self._selected_row()
        if values is None:
            return
        table = self._current_table()

        if table == "students":
            self.s_id.setText(values[0])
            self.s_name.setText(values[1])
            self.s_age.setText(values[2])
            self.s_email.setText(values[3])
        elif table == "instructors":
            self.i_id.setText(values[0])
            self.i_name.setText(values[1])
            self.i_age.setText(values[2])
            self.i_email.setText(values[3])
        else:
            self.c_id.setText(values[0])
            self.c_name.setText(values[1])
            row = next((r for r in self.db.get_courses()
                        if r["course_id"] == values[0]), None)
            if row is not None and row["instructor_id"]:
                index = self.c_instructor_box.findText(
                    f"{row['instructor_id']} - {row['instructor_name']}")
                self.c_instructor_box.setCurrentIndex(max(index, 0))
            else:
                self.c_instructor_box.setCurrentIndex(0)
        self.statusBar().showMessage(
            f"Loaded {values[0]} into the form. Edit, then press Update.")

    def delete_selected(self):
        """Delete the selected record after confirmation."""
        values = self._selected_row()
        if values is None:
            return
        table = self._current_table()
        record_id = values[0]
        answer = QMessageBox.question(
            self, "Confirm delete", f"Delete {table[:-1]} '{record_id}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        deleter = {"students": self.db.delete_student,
                   "instructors": self.db.delete_instructor,
                   "courses": self.db.delete_course}[table]
        self._guarded(lambda: deleter(record_id), f"Deleted {record_id}.")

    def new_file(self):
        """Delete every record after confirmation."""
        answer = QMessageBox.question(
            self, "New", "Delete every record in the database? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.db.clear()
            self.refresh_all()
            self.statusBar().showMessage("All records cleared.")

    def save_json(self):
        """Ask for a file name and save all records to JSON."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save data", "school_data.json", "JSON files (*.json);;All files (*)")
        if not path:
            return
        self.db.save_json(path)
        self.statusBar().showMessage(f"Saved to {path}")

    def load_json(self):
        """Ask for a JSON file and replace all records with its contents."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Load data", "", "JSON files (*.json);;All files (*)")
        if not path:
            return
        answer = QMessageBox.question(
            self, "Load",
            "Loading replaces every record currently in the database. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            self.db.load_json(path)
        except ValidationError as exc:
            QMessageBox.critical(self, "Could not load", str(exc))
            return
        self.refresh_all()
        self.statusBar().showMessage(f"Loaded from {path}")

    def export_csv(self):
        """Ask for a file name and export the active table to CSV."""
        table = self._current_table()
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export {table} to CSV", f"{table}.csv",
            "CSV files (*.csv);;All files (*)")
        if not path:
            return
        self.db.export_csv(path, table)
        self.statusBar().showMessage(f"Exported {table} to {path}")

    def backup_db(self):
        """Ask for a file name and back up the database."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Backup database", "school_backup.db",
            "SQLite database (*.db);;All files (*)")
        if not path:
            return
        self.db.backup(path)
        self.statusBar().showMessage(f"Database backed up to {path}")

    def restore_db(self):
        """Ask for a backup file and restore the database from it."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Restore database", "", "SQLite database (*.db);;All files (*)")
        if not path:
            return
        answer = QMessageBox.question(
            self, "Restore", "Restoring replaces the current database. Continue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            self.db.restore(path)
        except ValidationError as exc:
            QMessageBox.critical(self, "Could not restore", str(exc))
            return
        self.refresh_all()
        self.statusBar().showMessage(f"Database restored from {path}")

    def closeEvent(self, event):
        """Close the database connection when the window closes.

        :param event: The close event
        :type event: QCloseEvent
        """
        self.db.close()
        super().closeEvent(event)


def main():
    """Start the PyQt5 application and show the main window."""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app = QApplication(sys.argv)
    window = SchoolWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
