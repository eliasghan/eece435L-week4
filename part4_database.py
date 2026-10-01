"""SQLite persistence layer for the School Management System.

The :class:`Database` class stores students, instructors, courses and
enrollments and can convert to and from a :class:`part1_oop.School`.
"""

import csv
import os
import sqlite3
from datetime import datetime

from part1_oop import (
    Course,
    Instructor,
    School,
    Student,
    ValidationError,
    validate_age,
    validate_email,
    validate_non_empty,
)

DEFAULT_DB = "school.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS instructors (
    instructor_id TEXT PRIMARY KEY,
    name          TEXT NOT NULL,
    age           INTEGER NOT NULL CHECK (age >= 0),
    email         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name       TEXT NOT NULL,
    age        INTEGER NOT NULL CHECK (age >= 0),
    email      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    course_id     TEXT PRIMARY KEY,
    course_name   TEXT NOT NULL,
    instructor_id TEXT,
    FOREIGN KEY (instructor_id) REFERENCES instructors (instructor_id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS enrollments (
    student_id TEXT NOT NULL,
    course_id  TEXT NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students (student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses  (course_id)  ON DELETE CASCADE
);
"""


class Database:
    """SQLite backed storage for school records.

    :param path: Path of the SQLite database file, defaults to ``school.db``
    :type path: str, optional
    """
    def __init__(self, path=DEFAULT_DB):
        """Constructor method, opens the connection and creates the schema."""
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def __enter__(self):
        """Enter the context manager.

        :return: The database itself
        :rtype: Database
        """
        return self

    def __exit__(self, *exc):
        """Exit the context manager and close the connection."""
        self.close()

    def _write(self, sql, params=(), duplicate=None, foreign_key=None):
        """Execute a write statement and commit it.

        :param sql: SQL statement to execute
        :type sql: str
        :param params: Statement parameters, defaults to ()
        :type params: tuple, optional
        :param duplicate: Error message for uniqueness violations, defaults to None
        :type duplicate: str, optional
        :param foreign_key: Error message for foreign key violations, defaults to None
        :type foreign_key: str, optional
        :raises ValidationError: If an integrity constraint fails
        :return: The cursor used for the statement
        :rtype: sqlite3.Cursor
        """
        try:
            cur = self.conn.execute(sql, params)
        except sqlite3.IntegrityError as exc:
            self.conn.rollback()
            if "FOREIGN KEY" in str(exc).upper() and foreign_key:
                raise ValidationError(foreign_key)
            raise ValidationError(duplicate or str(exc))
        self.conn.commit()
        return cur

    def add_student(self, student_id, name, age, email):
        """Insert a new student.

        :param student_id: Unique student ID
        :type student_id: str
        :param name: Student name
        :type name: str
        :param age: Student age
        :type age: int
        :param email: Student email
        :type email: str
        :raises ValidationError: If data is invalid or the ID already exists
        """
        student_id = validate_non_empty(student_id, "Student ID")
        name = validate_non_empty(name, "Name")
        age = validate_age(age)
        email = validate_email(email)
        self._write(
            "INSERT INTO students (student_id, name, age, email) VALUES (?, ?, ?, ?)",
            (student_id, name, age, email),
            duplicate=f"Student ID '{student_id}' already exists.",
        )

    def update_student(self, student_id, name, age, email):
        """Update an existing student.

        :param student_id: ID of the student to update
        :type student_id: str
        :param name: New name
        :type name: str
        :param age: New age
        :type age: int
        :param email: New email
        :type email: str
        :raises ValidationError: If data is invalid or the student does not exist
        """
        name = validate_non_empty(name, "Name")
        age = validate_age(age)
        email = validate_email(email)
        cur = self._write(
            "UPDATE students SET name = ?, age = ?, email = ? WHERE student_id = ?",
            (name, age, email, student_id),
        )
        if cur.rowcount == 0:
            raise ValidationError(f"No student with ID '{student_id}'.")

    def delete_student(self, student_id):
        """Delete a student and their enrollments.

        :param student_id: ID of the student to delete
        :type student_id: str
        :raises ValidationError: If the student does not exist
        """
        cur = self._write("DELETE FROM students WHERE student_id = ?", (student_id,))
        if cur.rowcount == 0:
            raise ValidationError(f"No student with ID '{student_id}'.")

    def get_students(self):
        """Return every student ordered by ID.

        :rtype: list
        """
        return self.conn.execute(
            "SELECT * FROM students ORDER BY student_id"
        ).fetchall()

    def add_instructor(self, instructor_id, name, age, email):
        """Insert a new instructor.

        :param instructor_id: Unique instructor ID
        :type instructor_id: str
        :param name: Instructor name
        :type name: str
        :param age: Instructor age
        :type age: int
        :param email: Instructor email
        :type email: str
        :raises ValidationError: If data is invalid or the ID already exists
        """
        instructor_id = validate_non_empty(instructor_id, "Instructor ID")
        name = validate_non_empty(name, "Name")
        age = validate_age(age)
        email = validate_email(email)
        self._write(
            "INSERT INTO instructors (instructor_id, name, age, email) VALUES (?, ?, ?, ?)",
            (instructor_id, name, age, email),
            duplicate=f"Instructor ID '{instructor_id}' already exists.",
        )

    def update_instructor(self, instructor_id, name, age, email):
        """Update an existing instructor.

        :param instructor_id: ID of the instructor to update
        :type instructor_id: str
        :param name: New name
        :type name: str
        :param age: New age
        :type age: int
        :param email: New email
        :type email: str
        :raises ValidationError: If data is invalid or the instructor does not exist
        """
        name = validate_non_empty(name, "Name")
        age = validate_age(age)
        email = validate_email(email)
        cur = self._write(
            "UPDATE instructors SET name = ?, age = ?, email = ? WHERE instructor_id = ?",
            (name, age, email, instructor_id),
        )
        if cur.rowcount == 0:
            raise ValidationError(f"No instructor with ID '{instructor_id}'.")

    def delete_instructor(self, instructor_id):
        """Delete an instructor, leaving their courses without an instructor.

        :param instructor_id: ID of the instructor to delete
        :type instructor_id: str
        :raises ValidationError: If the instructor does not exist
        """
        cur = self._write(
            "DELETE FROM instructors WHERE instructor_id = ?", (instructor_id,)
        )
        if cur.rowcount == 0:
            raise ValidationError(f"No instructor with ID '{instructor_id}'.")

    def get_instructors(self):
        """Return every instructor ordered by ID.

        :rtype: list
        """
        return self.conn.execute(
            "SELECT * FROM instructors ORDER BY instructor_id"
        ).fetchall()

    def add_course(self, course_id, course_name, instructor_id=None):
        """Insert a new course.

        :param course_id: Unique course ID
        :type course_id: str
        :param course_name: Course name
        :type course_name: str
        :param instructor_id: ID of the teaching instructor, defaults to None
        :type instructor_id: str, optional
        :raises ValidationError: If data is invalid, the ID exists or the instructor is unknown
        """
        course_id = validate_non_empty(course_id, "Course ID")
        course_name = validate_non_empty(course_name, "Course name")
        instructor_id = instructor_id or None
        self._write(
            "INSERT INTO courses (course_id, course_name, instructor_id) VALUES (?, ?, ?)",
            (course_id, course_name, instructor_id),
            duplicate=f"Course ID '{course_id}' already exists.",
            foreign_key=f"No instructor with ID '{instructor_id}'.",
        )

    def update_course(self, course_id, course_name, instructor_id=None):
        """Update an existing course.

        :param course_id: ID of the course to update
        :type course_id: str
        :param course_name: New course name
        :type course_name: str
        :param instructor_id: New instructor ID, defaults to None
        :type instructor_id: str, optional
        :raises ValidationError: If data is invalid or the course or instructor does not exist
        """
        course_name = validate_non_empty(course_name, "Course name")
        instructor_id = instructor_id or None
        cur = self._write(
            "UPDATE courses SET course_name = ?, instructor_id = ? WHERE course_id = ?",
            (course_name, instructor_id, course_id),
            foreign_key=f"No instructor with ID '{instructor_id}'.",
        )
        if cur.rowcount == 0:
            raise ValidationError(f"No course with ID '{course_id}'.")

    def delete_course(self, course_id):
        """Delete a course and its enrollments.

        :param course_id: ID of the course to delete
        :type course_id: str
        :raises ValidationError: If the course does not exist
        """
        cur = self._write("DELETE FROM courses WHERE course_id = ?", (course_id,))
        if cur.rowcount == 0:
            raise ValidationError(f"No course with ID '{course_id}'.")

    def get_courses(self):
        """Return every course with its instructor name, ordered by ID.

        :rtype: list
        """
        return self.conn.execute(
            "SELECT c.course_id, c.course_name, c.instructor_id, "
            "       i.name AS instructor_name "
            "FROM courses c LEFT JOIN instructors i "
            "     ON c.instructor_id = i.instructor_id "
            "ORDER BY c.course_id"
        ).fetchall()

    def register_student(self, student_id, course_id):
        """Enroll a student in a course.

        :param student_id: Student ID
        :type student_id: str
        :param course_id: Course ID
        :type course_id: str
        :raises ValidationError: If already registered or the student or course is unknown
        """
        self._write(
            "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)",
            (student_id, course_id),
            duplicate="That student is already registered in that course.",
            foreign_key="Unknown student or course.",
        )

    def unregister_student(self, student_id, course_id):
        """Remove a student from a course.

        :param student_id: Student ID
        :type student_id: str
        :param course_id: Course ID
        :type course_id: str
        """
        self._write(
            "DELETE FROM enrollments WHERE student_id = ? AND course_id = ?",
            (student_id, course_id),
        )

    def assign_instructor(self, instructor_id, course_id):
        """Assign an instructor to a course.

        :param instructor_id: Instructor ID
        :type instructor_id: str
        :param course_id: Course ID
        :type course_id: str
        :raises ValidationError: If the instructor or course does not exist
        """
        cur = self._write(
            "UPDATE courses SET instructor_id = ? WHERE course_id = ?",
            (instructor_id, course_id),
            foreign_key=f"No instructor with ID '{instructor_id}'.",
        )
        if cur.rowcount == 0:
            raise ValidationError(f"No course with ID '{course_id}'.")

    def courses_of_student(self, student_id):
        """Return the courses a student is registered in.

        :param student_id: Student ID
        :type student_id: str
        :rtype: list
        """
        return self.conn.execute(
            "SELECT c.course_id, c.course_name FROM enrollments e "
            "JOIN courses c ON c.course_id = e.course_id "
            "WHERE e.student_id = ? ORDER BY c.course_id",
            (student_id,),
        ).fetchall()

    def courses_of_instructor(self, instructor_id):
        """Return the courses an instructor teaches.

        :param instructor_id: Instructor ID
        :type instructor_id: str
        :rtype: list
        """
        return self.conn.execute(
            "SELECT course_id, course_name FROM courses "
            "WHERE instructor_id = ? ORDER BY course_id",
            (instructor_id,),
        ).fetchall()

    def students_of_course(self, course_id):
        """Return the students enrolled in a course.

        :param course_id: Course ID
        :type course_id: str
        :rtype: list
        """
        return self.conn.execute(
            "SELECT s.student_id, s.name FROM enrollments e "
            "JOIN students s ON s.student_id = e.student_id "
            "WHERE e.course_id = ? ORDER BY s.student_id",
            (course_id,),
        ).fetchall()

    def to_school(self):
        """Build a :class:`part1_oop.School` from the database contents.

        :rtype: part1_oop.School
        """
        school = School()
        for row in self.get_instructors():
            school.add_instructor(
                Instructor(row["name"], row["age"], row["email"], row["instructor_id"])
            )
        for row in self.get_students():
            school.add_student(
                Student(row["name"], row["age"], row["email"], row["student_id"])
            )
        for row in self.get_courses():
            course = school.add_course(Course(row["course_id"], row["course_name"]))
            instructor = school.instructors.get(row["instructor_id"])
            if instructor is not None:
                instructor.assign_course(course)
        for row in self.conn.execute("SELECT * FROM enrollments").fetchall():
            student = school.students.get(row["student_id"])
            course = school.courses.get(row["course_id"])
            if student is not None and course is not None:
                student.register_course(course)
        return school

    def load_school(self, school):
        """Replace all database records with the contents of a school.

        :param school: The school to store
        :type school: part1_oop.School
        """
        with self.conn:
            self.conn.execute("DELETE FROM enrollments")
            self.conn.execute("DELETE FROM courses")
            self.conn.execute("DELETE FROM students")
            self.conn.execute("DELETE FROM instructors")
            self.conn.executemany(
                "INSERT INTO instructors (instructor_id, name, age, email) "
                "VALUES (?, ?, ?, ?)",
                [(i.instructor_id, i.name, i.age, i.email)
                 for i in school.instructors.values()],
            )
            self.conn.executemany(
                "INSERT INTO students (student_id, name, age, email) VALUES (?, ?, ?, ?)",
                [(s.student_id, s.name, s.age, s.email)
                 for s in school.students.values()],
            )
            self.conn.executemany(
                "INSERT INTO courses (course_id, course_name, instructor_id) "
                "VALUES (?, ?, ?)",
                [(c.course_id, c.course_name,
                  c.instructor.instructor_id if c.instructor else None)
                 for c in school.courses.values()],
            )
            self.conn.executemany(
                "INSERT INTO enrollments (student_id, course_id) VALUES (?, ?)",
                [(s.student_id, c.course_id)
                 for s in school.students.values()
                 for c in s.registered_courses],
            )

    def save_json(self, path):
        """Save all records to a JSON file.

        :param path: Destination file path
        :type path: str
        :return: The path that was written
        :rtype: str
        """
        return self.to_school().save_to_file(path)

    def load_json(self, path):
        """Replace all records with the contents of a JSON file.

        :param path: Source file path
        :type path: str
        :raises ValidationError: If the file is not valid JSON
        """
        self.load_school(School.load_from_file(path))

    def export_csv(self, path, table="students"):
        """Export one table to a CSV file.

        :param path: Destination file path
        :type path: str
        :param table: One of ``students``, ``instructors`` or ``courses``, defaults to ``students``
        :type table: str, optional
        :raises ValidationError: If the table name is unknown
        :return: The path that was written
        :rtype: str
        """
        if table == "students":
            header = ["student_id", "name", "age", "email", "registered_courses"]
            rows = [
                [r["student_id"], r["name"], r["age"], r["email"],
                 "; ".join(c["course_id"] for c in self.courses_of_student(r["student_id"]))]
                for r in self.get_students()
            ]
        elif table == "instructors":
            header = ["instructor_id", "name", "age", "email", "assigned_courses"]
            rows = [
                [r["instructor_id"], r["name"], r["age"], r["email"],
                 "; ".join(c["course_id"]
                           for c in self.courses_of_instructor(r["instructor_id"]))]
                for r in self.get_instructors()
            ]
        elif table == "courses":
            header = ["course_id", "course_name", "instructor", "enrolled_students"]
            rows = [
                [r["course_id"], r["course_name"], r["instructor_name"] or "",
                 "; ".join(s["student_id"] for s in self.students_of_course(r["course_id"]))]
                for r in self.get_courses()
            ]
        else:
            raise ValidationError(f"Unknown table '{table}'.")

        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(header)
            writer.writerows(rows)
        return path

    def backup(self, path=None):
        """Copy the database to a backup file.

        :param path: Destination path, defaults to a timestamped file next to the database
        :type path: str, optional
        :return: The backup file path
        :rtype: str
        """
        if path is None:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"{os.path.splitext(self.path)[0]}_backup_{stamp}.db"
        self.conn.commit()
        dest = sqlite3.connect(path)
        try:
            self.conn.backup(dest)
        finally:
            dest.close()
        return path

    def restore(self, path):
        """Restore the database from a backup file.

        :param path: Backup file path
        :type path: str
        :raises ValidationError: If the backup file does not exist
        """
        if not os.path.exists(path):
            raise ValidationError(f"Backup file '{path}' not found.")
        src = sqlite3.connect(path)
        try:
            src.backup(self.conn)
        finally:
            src.close()
        self.conn.commit()

    def clear(self):
        """Delete every record from every table."""
        with self.conn:
            self.conn.execute("DELETE FROM enrollments")
            self.conn.execute("DELETE FROM courses")
            self.conn.execute("DELETE FROM students")
            self.conn.execute("DELETE FROM instructors")


def _demo():
    """Run a small command line demonstration of the database layer."""
    path = "demo_school.db"
    if os.path.exists(path):
        os.remove(path)

    db = Database(path)
    db.add_instructor("I001", "Dr. Smith", 45, "smith@aub.edu.lb")
    db.add_student("S001", "Alice Khoury", 20, "alice@mail.aub.edu")
    db.add_student("S002", "Bob Haddad", 22, "bob@mail.aub.edu")
    db.add_course("EECE435L", "Software Tools Lab", "I001")
    db.add_course("MATH218", "Linear Algebra")
    db.register_student("S001", "EECE435L")
    db.register_student("S002", "EECE435L")
    db.register_student("S002", "MATH218")
    db.assign_instructor("I001", "MATH218")

    print("Students:", [dict(r) for r in db.get_students()])
    print("Courses :", [dict(r) for r in db.get_courses()])
    print("S002 takes:", [r["course_id"] for r in db.courses_of_student("S002")])

    for bad in (lambda: db.add_student("S003", "X", -5, "x@y.com"),
                lambda: db.add_student("S003", "X", 20, "nope"),
                lambda: db.add_student("S001", "Dup", 20, "d@y.com")):
        try:
            bad()
        except ValidationError as exc:
            print("Rejected:", exc)

    backup_path = db.backup("demo_school_backup.db")
    print("Backed up to", backup_path)
    db.delete_student("S001")
    print("After delete:", [r["student_id"] for r in db.get_students()])
    db.restore(backup_path)
    print("After restore:", [r["student_id"] for r in db.get_students()])

    db.save_json("demo_school.json")
    db.load_json("demo_school.json")
    print("JSON round trip ->", [r["student_id"] for r in db.get_students()])

    db.export_csv("demo_students.csv", "students")
    print("CSV written to demo_students.csv")

    db.close()
    for f in (path, backup_path, "demo_school.json", "demo_students.csv"):
        os.remove(f)
    print("Database demo OK")


if __name__ == "__main__":
    _demo()
