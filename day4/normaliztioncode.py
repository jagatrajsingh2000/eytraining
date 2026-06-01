"""Day 4: Normalization example.

1NF rule:
- Each column value must be atomic. Do not store lists/multiple values in one cell.
- Each row should have a primary key.

2NF rule:
- The table must already be in 1NF.
- Every non-key column must depend on the full primary key, not only part of it.

3NF rule:
- The table must already be in 2NF.
- Non-key columns must not depend on other non-key columns.
"""

import sqlite3

import pandas as pd


Primary_key = ("student_id", "course_code", "textbook_required")
Primary_key_2nf = {
    "students": ("student_id",),
    "courses": ("course_code",),
    "enrollments": ("student_id", "course_code"),
    "course_textbooks": ("course_code", "textbook_required"),
}
Primary_key_3nf = {
    "students": ("student_id",),
    "instructors": ("instructor_id",),
    "courses": ("course_code",),
    "enrollments": ("student_id", "course_code"),
    "course_textbooks": ("course_code", "textbook_required"),
}


def create_0nf_dataframe() -> pd.DataFrame:
    """Create an unnormalized table with comma-separated textbook values."""
    data_0nf = {
        "student_id": [101, 101, 102, 103, 104],
        "student_name": ["Alice", "Alice", "Bob", "Charlie", "David"],
        "course_code": ["CS101", "MATH201", "CS101", "ENG101", "MATH201"],
        "course_name": [
            "Introduction to Programming",
            "Calculus I",
            "Introduction to Programming",
            "English Literature",
            "Calculus I",
        ],
        "instructor_id": [501, 502, 501, 503, 502],
        "instructor_name": [
            "Dr. Smith",
            "Dr. Brown",
            "Dr. Smith",
            "Prof. Wilson",
            "Dr. Brown",
        ],
        "instructor_office": ["B-201", "C-105", "B-201", "A-310", "C-105"],
        "grade": ["A", "B+", "A-", "B", "A"],
        "textbooks_required": [
            "Python Basics, Data Structures",
            "Calculus Made Easy",
            "Python Basics, Data Structures",
            "Shakespeare Reader, Grammar Guide",
            "Calculus Made Easy, Linear Algebra",
        ],
    }

    return pd.DataFrame(data_0nf)


def convert_to_1nf(df_0nf: pd.DataFrame) -> pd.DataFrame:
    """Convert the 0NF table into 1NF by making textbook values atomic."""
    df_1nf = (
        df_0nf.assign(
            textbook_required=df_0nf["textbooks_required"].str.split(r"\s*,\s*", regex=True)
        )
        .explode("textbook_required")
        .drop(columns=["textbooks_required"])
        .reset_index(drop=True)
    )

    return df_1nf


def save_1nf_to_sql(conn: sqlite3.Connection, df_1nf: pd.DataFrame) -> None:
    """Save 1NF data into SQLite with a defined primary key."""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS table_1nf")
    cursor.execute(
        """
        CREATE TABLE table_1nf (
            student_id INTEGER NOT NULL,
            student_name TEXT NOT NULL,
            course_code TEXT NOT NULL,
            course_name TEXT NOT NULL,
            instructor_id INTEGER NOT NULL,
            instructor_name TEXT NOT NULL,
            instructor_office TEXT NOT NULL,
            grade TEXT NOT NULL,
            textbook_required TEXT NOT NULL,
            PRIMARY KEY (student_id, course_code, textbook_required)
        )
        """
    )

    df_1nf.to_sql("table_1nf", conn, index=False, if_exists="append")
    conn.commit()


def convert_to_2nf(df_1nf: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Convert the 1NF table into 2NF by removing partial dependencies."""
    students = (
        df_1nf[["student_id", "student_name"]]
        .drop_duplicates()
        .sort_values("student_id")
        .reset_index(drop=True)
    )

    courses = (
        df_1nf[
            [
                "course_code",
                "course_name",
                "instructor_id",
                "instructor_name",
                "instructor_office",
            ]
        ]
        .drop_duplicates()
        .sort_values("course_code")
        .reset_index(drop=True)
    )

    enrollments = (
        df_1nf[["student_id", "course_code", "grade"]]
        .drop_duplicates()
        .sort_values(["student_id", "course_code"])
        .reset_index(drop=True)
    )

    course_textbooks = (
        df_1nf[["course_code", "textbook_required"]]
        .drop_duplicates()
        .sort_values(["course_code", "textbook_required"])
        .reset_index(drop=True)
    )

    return {
        "students": students,
        "courses": courses,
        "enrollments": enrollments,
        "course_textbooks": course_textbooks,
    }


def save_2nf_to_sql(conn: sqlite3.Connection, tables_2nf: dict[str, pd.DataFrame]) -> None:
    """Save 2NF tables into SQLite with primary and foreign keys."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.executescript(
        """
        DROP TABLE IF EXISTS course_textbooks;
        DROP TABLE IF EXISTS enrollments;
        DROP TABLE IF EXISTS courses;
        DROP TABLE IF EXISTS students;

        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY,
            student_name TEXT NOT NULL
        );

        CREATE TABLE courses (
            course_code TEXT PRIMARY KEY,
            course_name TEXT NOT NULL,
            instructor_id INTEGER NOT NULL,
            instructor_name TEXT NOT NULL,
            instructor_office TEXT NOT NULL
        );

        CREATE TABLE enrollments (
            student_id INTEGER NOT NULL,
            course_code TEXT NOT NULL,
            grade TEXT NOT NULL,
            PRIMARY KEY (student_id, course_code),
            FOREIGN KEY (student_id) REFERENCES students (student_id),
            FOREIGN KEY (course_code) REFERENCES courses (course_code)
        );

        CREATE TABLE course_textbooks (
            course_code TEXT NOT NULL,
            textbook_required TEXT NOT NULL,
            PRIMARY KEY (course_code, textbook_required),
            FOREIGN KEY (course_code) REFERENCES courses (course_code)
        );
        """
    )

    for table_name in [
        "students",
        "courses",
        "enrollments",
        "course_textbooks",
    ]:
        tables_2nf[table_name].to_sql(table_name, conn, index=False, if_exists="append")

    conn.commit()


def convert_to_3nf(tables_2nf: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Convert the 2NF tables into 3NF by removing transitive dependencies."""
    courses_2nf = tables_2nf["courses"]

    instructors = (
        courses_2nf[["instructor_id", "instructor_name", "instructor_office"]]
        .drop_duplicates()
        .sort_values("instructor_id")
        .reset_index(drop=True)
    )

    courses = (
        courses_2nf[["course_code", "course_name", "instructor_id"]]
        .drop_duplicates()
        .sort_values("course_code")
        .reset_index(drop=True)
    )

    return {
        "students": tables_2nf["students"].copy(),
        "instructors": instructors,
        "courses": courses,
        "enrollments": tables_2nf["enrollments"].copy(),
        "course_textbooks": tables_2nf["course_textbooks"].copy(),
    }


def save_3nf_to_sql(conn: sqlite3.Connection, tables_3nf: dict[str, pd.DataFrame]) -> None:
    """Save 3NF tables into SQLite with primary and foreign keys."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.executescript(
        """
        DROP TABLE IF EXISTS course_textbooks_3nf;
        DROP TABLE IF EXISTS enrollments_3nf;
        DROP TABLE IF EXISTS courses_3nf;
        DROP TABLE IF EXISTS instructors_3nf;
        DROP TABLE IF EXISTS students_3nf;

        CREATE TABLE students_3nf (
            student_id INTEGER PRIMARY KEY,
            student_name TEXT NOT NULL
        );

        CREATE TABLE instructors_3nf (
            instructor_id INTEGER PRIMARY KEY,
            instructor_name TEXT NOT NULL,
            instructor_office TEXT NOT NULL
        );

        CREATE TABLE courses_3nf (
            course_code TEXT PRIMARY KEY,
            course_name TEXT NOT NULL,
            instructor_id INTEGER NOT NULL,
            FOREIGN KEY (instructor_id) REFERENCES instructors_3nf (instructor_id)
        );

        CREATE TABLE enrollments_3nf (
            student_id INTEGER NOT NULL,
            course_code TEXT NOT NULL,
            grade TEXT NOT NULL,
            PRIMARY KEY (student_id, course_code),
            FOREIGN KEY (student_id) REFERENCES students_3nf (student_id),
            FOREIGN KEY (course_code) REFERENCES courses_3nf (course_code)
        );

        CREATE TABLE course_textbooks_3nf (
            course_code TEXT NOT NULL,
            textbook_required TEXT NOT NULL,
            PRIMARY KEY (course_code, textbook_required),
            FOREIGN KEY (course_code) REFERENCES courses_3nf (course_code)
        );
        """
    )

    table_map = {
        "students": "students_3nf",
        "instructors": "instructors_3nf",
        "courses": "courses_3nf",
        "enrollments": "enrollments_3nf",
        "course_textbooks": "course_textbooks_3nf",
    }
    for table_name, sql_table_name in table_map.items():
        tables_3nf[table_name].to_sql(
            sql_table_name, conn, index=False, if_exists="append"
        )

    conn.commit()


def main() -> None:
    conn = sqlite3.connect(":memory:")

    df_0nf = create_0nf_dataframe()
    df_1nf = convert_to_1nf(df_0nf)
    tables_2nf = convert_to_2nf(df_1nf)
    tables_3nf = convert_to_3nf(tables_2nf)
    save_1nf_to_sql(conn, df_1nf)
    save_2nf_to_sql(conn, tables_2nf)
    save_3nf_to_sql(conn, tables_3nf)

    print("Setup complete. Environment ready.")
    print("\n--- 0NF Data: has non-atomic textbook values ---")
    print(df_0nf.to_string(index=False))

    print("\n--- 1NF Data: textbook values are atomic ---")
    print(df_1nf.to_string(index=False))

    print(
        f"\nRow count increased from {len(df_0nf)} to {len(df_1nf)} "
        "because comma-separated textbook values were split into separate rows."
    )

    primary_key_info = pd.read_sql_query("PRAGMA table_info(table_1nf)", conn)
    print(f"\nPrimary_key = {Primary_key}")
    print("\n--- SQLite table schema ---")
    print(primary_key_info.to_string(index=False))

    print("\n--- 2NF Definition ---")
    print(
        "2NF means the table is already in 1NF and every non-key column depends "
        "on the complete primary key, not only part of a composite primary key."
    )

    print("\n--- 2NF Tables ---")
    for table_name, table_data in tables_2nf.items():
        print(f"\n{table_name} primary key = {Primary_key_2nf[table_name]}")
        print(table_data.to_string(index=False))

    print("\n--- 3NF Definition ---")
    print(
        "3NF means the table is already in 2NF and no non-key column depends "
        "on another non-key column. Here, instructor_name and "
        "instructor_office depend on instructor_id, so they move into a "
        "separate instructors table."
    )

    print("\n--- 3NF Tables ---")
    for table_name, table_data in tables_3nf.items():
        print(f"\n{table_name} primary key = {Primary_key_3nf[table_name]}")
        print(table_data.to_string(index=False))

    conn.close()


if __name__ == "__main__":
    main()
