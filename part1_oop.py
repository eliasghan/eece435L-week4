"""Object-oriented model of the School Management System.

Defines the validation helpers, the :class:`Person` hierarchy
(:class:`Student`, :class:`Instructor`), :class:`Course` and the
:class:`School` container that serializes everything to JSON.
"""

import json
import os
import re
from abc import ABC, abstractmethod


EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class ValidationError(ValueError):
    """Raised when user supplied data fails validation.

    Subclass of :class:`ValueError` so it can be caught generically.
    """


def validate_non_empty(value, field):
    """Ensure a value is not empty or whitespace only.

    :param value: The value to check
    :type value: object
    :param field: Human readable field name used in the error message
    :type field: str
    :raises ValidationError: If the value is ``None`` or blank
    :return: The value converted to a stripped string
    :rtype: str
    """
    if value is None or not str(value).strip():
        raise ValidationError(f"{field} cannot be empty.")
    return str(value).strip()


def validate_age(value):
    """Validate and convert an age.

    :param value: The age to validate, as an int or numeric string
    :type value: int or str
    :raises ValidationError: If the age is not a whole number or is outside 0..130
    :return: The age as an integer
    :rtype: int
    """
    try:
        age = int(value)
    except (TypeError, ValueError):
        raise ValidationError("Age must be a whole number.")
    if age < 0:
        raise ValidationError("Age cannot be negative.")
    if age > 130:
        raise ValidationError("Age must be 130 or less.")
    return age


def validate_email(value):
    """Validate an email address against a simple pattern.

    :param value: The email address to validate
    :type value: str
    :raises ValidationError: If the email is empty or malformed
    :return: The stripped email address
    :rtype: str
    """
    email = validate_non_empty(value, "Email")
    if not EMAIL_RE.match(email):
        raise ValidationError(f"'{email}' is not a valid email address.")
    return email


class Serializable(ABC):
    """Abstract base class for objects that convert to and from dictionaries."""

    @abstractmethod
    def to_dict(self):
        """Convert the object to a JSON friendly dictionary.

        :return: Dictionary representation of the object
        :rtype: dict
        """

    @classmethod
    @abstractmethod
    def from_dict(cls, data):
        """Build an object from a dictionary.

        :param data: Dictionary produced by :meth:`to_dict`
        :type data: dict
        :return: A new instance of the class
        """


class Person(Serializable):
    """Base class for every person in the school.

    :param name: Full name of the person
    :type name: str
    :param age: Age of the person, between 0 and 130
    :type age: int
    :param _email: Email address of the person
    :type _email: str
    :raises ValidationError: If any argument is invalid
    """
    def __init__(self, name, age, _email):
        """Constructor method"""
        self.name = validate_non_empty(name, "Name")
        self.age = validate_age(age)
        self._email = validate_email(_email)

    @property
    def email(self):
        """The validated email address of the person.

        :return: The email address
        :rtype: str
        """
        return self._email

    @email.setter
    def email(self, value):
        self._email = validate_email(value)

    def introduce(self):
        """Return a short self introduction.

        :return: Introduction sentence
        :rtype: str
        """
        return f"Hello, my name is {self.name}. I am {self.age} years old."

    def to_dict(self):
        """Convert the person to a dictionary.

        :return: Dictionary with ``name``, ``age`` and ``email`` keys
        :rtype: dict
        """
        return {"name": self.name, "age": self.age, "email": self._email}

    @classmethod
    def from_dict(cls, data):
        """Create a person from a dictionary.

        :param data: Dictionary with ``name``, ``age`` and ``email`` keys
        :type data: dict
        :return: A new person
        :rtype: Person
        """
        return cls(data["name"], data["age"], data["email"])

    def __repr__(self):
        """Return the developer representation of the person.

        :rtype: str
        """
        return f"{type(self).__name__}({self.name!r}, {self.age!r}, {self._email!r})"


class Student(Person):
    """A student that can register in courses.

    :param name: Full name of the student
    :type name: str
    :param age: Age of the student
    :type age: int
    :param _email: Email address of the student
    :type _email: str
    :param student_id: Unique student identifier
    :type student_id: str
    :param registered_courses: Courses the student is registered in, defaults to None
    :type registered_courses: list, optional
    """
    def __init__(self, name, age, _email, student_id, registered_courses=None):
        """Constructor method"""
        super().__init__(name, age, _email)
        self.student_id = validate_non_empty(student_id, "Student ID")
        self.registered_courses = list(registered_courses) if registered_courses else []

    def register_course(self, course):
        """Register the student in a course and enroll them in it.

        :param course: The course to register in
        :type course: :class:`Course`
        :raises ValidationError: If ``course`` is not a Course or the student is already registered
        """
        if not isinstance(course, Course):
            raise ValidationError("register_course() expects a Course object.")
        if any(c.course_id == course.course_id for c in self.registered_courses):
            raise ValidationError(
                f"{self.name} is already registered in {course.course_name}."
            )
        self.registered_courses.append(course)
        if all(s.student_id != self.student_id for s in course.enrolled_students):
            course.enrolled_students.append(self)

    def drop_course(self, course):
        """Remove the student from a course.

        :param course: The course to drop
        :type course: :class:`Course`
        """
        self.registered_courses = [
            c for c in self.registered_courses if c.course_id != course.course_id
        ]
        course.enrolled_students = [
            s for s in course.enrolled_students if s.student_id != self.student_id
        ]

    def introduce(self):
        """Return a self introduction including the student ID.

        :rtype: str
        """
        return f"{super().introduce()} I am a student, id {self.student_id}."

    def to_dict(self):
        """Convert the student to a dictionary including registered course IDs.

        :rtype: dict
        """
        data = super().to_dict()
        data["student_id"] = self.student_id
        data["registered_courses"] = [c.course_id for c in self.registered_courses]
        return data

    @classmethod
    def from_dict(cls, data):
        """Create a student from a dictionary, without its courses.

        :param data: Dictionary produced by :meth:`to_dict`
        :type data: dict
        :rtype: Student
        """
        return cls(data["name"], data["age"], data["email"], data["student_id"])


class Instructor(Person):
    """An instructor that can be assigned to courses.

    :param name: Full name of the instructor
    :type name: str
    :param age: Age of the instructor
    :type age: int
    :param _email: Email address of the instructor
    :type _email: str
    :param instructor_id: Unique instructor identifier
    :type instructor_id: str
    :param assigned_courses: Courses taught by the instructor, defaults to None
    :type assigned_courses: list, optional
    """
    def __init__(self, name, age, _email, instructor_id, assigned_courses=None):
        """Constructor method"""
        super().__init__(name, age, _email)
        self.instructor_id = validate_non_empty(instructor_id, "Instructor ID")
        self.assigned_courses = list(assigned_courses) if assigned_courses else []

    def assign_course(self, course):
        """Assign the instructor to a course, replacing any previous instructor.

        :param course: The course to teach
        :type course: :class:`Course`
        :raises ValidationError: If ``course`` is not a Course or is already assigned
        """
        if not isinstance(course, Course):
            raise ValidationError("assign_course() expects a Course object.")
        if any(c.course_id == course.course_id for c in self.assigned_courses):
            raise ValidationError(
                f"{self.name} is already assigned to {course.course_name}."
            )
        if course.instructor is not None and course.instructor is not self:
            course.instructor.unassign_course(course)
        self.assigned_courses.append(course)
        course.instructor = self

    def unassign_course(self, course):
        """Remove the instructor from a course.

        :param course: The course to unassign
        :type course: :class:`Course`
        """
        self.assigned_courses = [
            c for c in self.assigned_courses if c.course_id != course.course_id
        ]
        if course.instructor is not None and course.instructor.instructor_id == self.instructor_id:
            course.instructor = None

    def introduce(self):
        """Return a self introduction including the instructor ID.

        :rtype: str
        """
        return f"{super().introduce()} I am an instructor, id {self.instructor_id}."

    def to_dict(self):
        """Convert the instructor to a dictionary including assigned course IDs.

        :rtype: dict
        """
        data = super().to_dict()
        data["instructor_id"] = self.instructor_id
        data["assigned_courses"] = [c.course_id for c in self.assigned_courses]
        return data

    @classmethod
    def from_dict(cls, data):
        """Create an instructor from a dictionary, without its courses.

        :param data: Dictionary produced by :meth:`to_dict`
        :type data: dict
        :rtype: Instructor
        """
        return cls(data["name"], data["age"], data["email"], data["instructor_id"])


class Course(Serializable):
    """A course with an optional instructor and enrolled students.

    :param course_id: Unique course identifier
    :type course_id: str
    :param course_name: Name of the course
    :type course_name: str
    :param instructor: Instructor teaching the course, defaults to None
    :type instructor: :class:`Instructor`, optional
    :param enrolled_students: Students enrolled in the course, defaults to None
    :type enrolled_students: list, optional
    :raises ValidationError: If an argument is invalid
    """
    def __init__(self, course_id, course_name, instructor=None, enrolled_students=None):
        """Constructor method"""
        self.course_id = validate_non_empty(course_id, "Course ID")
        self.course_name = validate_non_empty(course_name, "Course name")
        if instructor is not None and not isinstance(instructor, Instructor):
            raise ValidationError("instructor must be an Instructor object or None.")
        self.instructor = instructor
        self.enrolled_students = list(enrolled_students) if enrolled_students else []

    def add_student(self, student):
        """Enroll a student in this course.

        :param student: The student to enroll
        :type student: :class:`Student`
        :raises ValidationError: If ``student`` is not a Student
        """
        if not isinstance(student, Student):
            raise ValidationError("add_student() expects a Student object.")
        student.register_course(self)

    def remove_student(self, student):
        """Remove a student from this course.

        :param student: The student to remove
        :type student: :class:`Student`
        """
        student.drop_course(self)

    def to_dict(self):
        """Convert the course to a dictionary.

        :rtype: dict
        """
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "instructor_id": self.instructor.instructor_id if self.instructor else None,
            "enrolled_students": [s.student_id for s in self.enrolled_students],
        }

    @classmethod
    def from_dict(cls, data):
        """Create a course from a dictionary, without links.

        :param data: Dictionary produced by :meth:`to_dict`
        :type data: dict
        :rtype: Course
        """
        return cls(data["course_id"], data["course_name"])

    def __repr__(self):
        """Return the developer representation of the course.

        :rtype: str
        """
        return f"Course({self.course_id!r}, {self.course_name!r})"


class School:
    """In-memory container for students, instructors and courses keyed by ID."""
    def __init__(self):
        """Constructor method"""
        self.students = {}
        self.instructors = {}
        self.courses = {}

    def add_student(self, student):
        """Add a student to the school.

        :param student: The student to add
        :type student: :class:`Student`
        :raises ValidationError: If the student ID already exists
        :return: The added student
        :rtype: Student
        """
        if student.student_id in self.students:
            raise ValidationError(f"Student ID '{student.student_id}' already exists.")
        self.students[student.student_id] = student
        return student

    def add_instructor(self, instructor):
        """Add an instructor to the school.

        :param instructor: The instructor to add
        :type instructor: :class:`Instructor`
        :raises ValidationError: If the instructor ID already exists
        :return: The added instructor
        :rtype: Instructor
        """
        if instructor.instructor_id in self.instructors:
            raise ValidationError(
                f"Instructor ID '{instructor.instructor_id}' already exists."
            )
        self.instructors[instructor.instructor_id] = instructor
        return instructor

    def add_course(self, course):
        """Add a course to the school.

        :param course: The course to add
        :type course: :class:`Course`
        :raises ValidationError: If the course ID already exists
        :return: The added course
        :rtype: Course
        """
        if course.course_id in self.courses:
            raise ValidationError(f"Course ID '{course.course_id}' already exists.")
        self.courses[course.course_id] = course
        return course

    def delete_student(self, student_id):
        """Delete a student and drop all their courses.

        :param student_id: ID of the student to delete
        :type student_id: str
        :raises ValidationError: If no such student exists
        :return: The deleted student
        :rtype: Student
        """
        student = self.students.pop(student_id, None)
        if student is None:
            raise ValidationError(f"No student with ID '{student_id}'.")
        for course in list(student.registered_courses):
            student.drop_course(course)
        return student

    def delete_instructor(self, instructor_id):
        """Delete an instructor and unassign all their courses.

        :param instructor_id: ID of the instructor to delete
        :type instructor_id: str
        :raises ValidationError: If no such instructor exists
        :return: The deleted instructor
        :rtype: Instructor
        """
        instructor = self.instructors.pop(instructor_id, None)
        if instructor is None:
            raise ValidationError(f"No instructor with ID '{instructor_id}'.")
        for course in list(instructor.assigned_courses):
            instructor.unassign_course(course)
        return instructor

    def delete_course(self, course_id):
        """Delete a course and detach its students and instructor.

        :param course_id: ID of the course to delete
        :type course_id: str
        :raises ValidationError: If no such course exists
        :return: The deleted course
        :rtype: Course
        """
        course = self.courses.pop(course_id, None)
        if course is None:
            raise ValidationError(f"No course with ID '{course_id}'.")
        for student in list(course.enrolled_students):
            student.drop_course(course)
        if course.instructor is not None:
            course.instructor.unassign_course(course)
        return course

    def search(self, term):
        """Search records by name, ID or course.

        :param term: Case-insensitive search text, an empty term matches everything
        :type term: str
        :return: Dictionary with ``students``, ``instructors`` and ``courses`` lists
        :rtype: dict
        """
        term = (term or "").strip().lower()

        def hit(*fields):
            return not term or any(term in str(f).lower() for f in fields if f is not None)

        return {
            "students": [
                s for s in self.students.values()
                if hit(s.name, s.student_id, s.email,
                       *[c.course_name for c in s.registered_courses],
                       *[c.course_id for c in s.registered_courses])
            ],
            "instructors": [
                i for i in self.instructors.values()
                if hit(i.name, i.instructor_id, i.email,
                       *[c.course_name for c in i.assigned_courses],
                       *[c.course_id for c in i.assigned_courses])
            ],
            "courses": [
                c for c in self.courses.values()
                if hit(c.course_id, c.course_name,
                       c.instructor.name if c.instructor else None)
            ],
        }

    def to_dict(self):
        """Convert the whole school to a dictionary.

        :rtype: dict
        """
        return {
            "students": [s.to_dict() for s in self.students.values()],
            "instructors": [i.to_dict() for i in self.instructors.values()],
            "courses": [c.to_dict() for c in self.courses.values()],
        }

    def save_to_file(self, path):
        """Atomically save the school to a JSON file.

        :param path: Destination file path
        :type path: str
        :return: The path that was written
        :rtype: str
        """
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2)
        os.replace(tmp, path)
        return path

    @classmethod
    def from_dict(cls, data):
        """Rebuild a school and all its links from a dictionary.

        :param data: Dictionary produced by :meth:`to_dict`
        :type data: dict
        :rtype: School
        """
        school = cls()

        for raw in data.get("courses", []):
            school.add_course(Course.from_dict(raw))
        for raw in data.get("students", []):
            school.add_student(Student.from_dict(raw))
        for raw in data.get("instructors", []):
            school.add_instructor(Instructor.from_dict(raw))

        for raw in data.get("students", []):
            student = school.students[raw["student_id"]]
            for cid in raw.get("registered_courses", []):
                course = school.courses.get(cid)
                if course is not None:
                    student.register_course(course)

        for raw in data.get("instructors", []):
            instructor = school.instructors[raw["instructor_id"]]
            for cid in raw.get("assigned_courses", []):
                course = school.courses.get(cid)
                if course is not None:
                    instructor.assign_course(course)

        for raw in data.get("courses", []):
            course = school.courses[raw["course_id"]]
            iid = raw.get("instructor_id")
            if iid and course.instructor is None:
                instructor = school.instructors.get(iid)
                if instructor is not None:
                    instructor.assign_course(course)
            for sid in raw.get("enrolled_students", []):
                student = school.students.get(sid)
                if student is not None and all(
                    c.course_id != course.course_id for c in student.registered_courses
                ):
                    student.register_course(course)

        return school

    @classmethod
    def load_from_file(cls, path):
        """Load a school from a JSON file.

        :param path: Source file path
        :type path: str
        :raises ValidationError: If the file is not valid JSON
        :return: The loaded school, or an empty one if the file does not exist
        :rtype: School
        """
        if not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as fh:
            try:
                data = json.load(fh)
            except json.JSONDecodeError as exc:
                raise ValidationError(f"'{path}' is not valid JSON: {exc}")
        return cls.from_dict(data)


def _demo():
    """Run a small command line demonstration of the model."""
    school = School()

    alice = school.add_student(Student("Alice Khoury", 20, "alice@mail.aub.edu", "S001"))
    bob = school.add_student(Student("Bob Haddad", 22, "bob@mail.aub.edu", "S002"))
    smith = school.add_instructor(
        Instructor("Dr. Smith", 45, "smith@aub.edu.lb", "I001")
    )

    eece435 = school.add_course(Course("EECE435L", "Software Tools Lab"))
    math218 = school.add_course(Course("MATH218", "Linear Algebra"))

    smith.assign_course(eece435)
    alice.register_course(eece435)
    eece435.add_student(bob)
    bob.register_course(math218)

    for person in (alice, bob, smith):
        print(person.introduce())

    for bad in (lambda: Student("X", -1, "x@y.com", "S9"),
                lambda: Student("X", 20, "not-an-email", "S9"),
                lambda: Student("", 20, "x@y.com", "S9")):
        try:
            bad()
        except ValidationError as exc:
            print("Rejected:", exc)

    path = "part1_demo.json"
    school.save_to_file(path)
    reloaded = School.load_from_file(path)
    print(f"\nReloaded {len(reloaded.students)} students, "
          f"{len(reloaded.instructors)} instructors, "
          f"{len(reloaded.courses)} courses from {path}")
    print("Alice's courses after reload:",
          [c.course_name for c in reloaded.students["S001"].registered_courses])
    print("EECE435L instructor after reload:",
          reloaded.courses["EECE435L"].instructor.name)
    assert reloaded.to_dict() == school.to_dict(), "round trip mismatch"
    print("Round trip OK")

    print("\nSearch 'linear':",
          [c.course_name for c in reloaded.search("linear")["courses"]])


if __name__ == "__main__":
    _demo()
