"""Day 4: Normalization using pandas only.

1NF:
- Each column value must be atomic.
- Each row should have a primary key.

2NF:
- The data must already be in 1NF.
- Every non-key column must depend on the full primary key.

3NF:
- The data must already be in 2NF.
- Non-key columns must not depend on other non-key columns.
"""

import pandas as pd


Primary_key_1nf = ("student_id", "course_code", "textbook_required")
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
    """Create messy 0NF data with multiple textbooks in one cell."""
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
    """Create 1NF by splitting multi-value textbook cells into separate rows."""
    return (
        df_0nf.assign(
            textbook_required=df_0nf["textbooks_required"].str.split(r"\s*,\s*", regex=True)
        )
        .explode("textbook_required")
        .drop(columns=["textbooks_required"])
        .reset_index(drop=True)
    )


def convert_to_2nf(df_1nf: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Create 2NF tables by removing partial dependencies."""
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


def convert_to_3nf(tables_2nf: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Create 3NF tables by removing transitive dependencies."""
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


def print_table(title: str, data: pd.DataFrame) -> None:
    """Print a dataframe with a readable title."""
    print(f"\n--- {title} ---")
    print(data.to_string(index=False))


def main() -> None:
    df_0nf = create_0nf_dataframe()
    df_1nf = convert_to_1nf(df_0nf)
    tables_2nf = convert_to_2nf(df_1nf)
    tables_3nf = convert_to_3nf(tables_2nf)

    print_table("0NF Data: non-atomic textbook values", df_0nf)

    print("\n1NF Definition:")
    print("1NF means every cell has one atomic value and each row has a primary key.")
    print(f"Primary_key_1nf = {Primary_key_1nf}")
    print_table("1NF Data: textbook values are atomic", df_1nf)

    print(
        f"\nRow count increased from {len(df_0nf)} to {len(df_1nf)} "
        "because textbook lists were split into separate rows."
    )

    print("\n2NF Definition:")
    print(
        "2NF means the data is already in 1NF and every non-key column depends "
        "on the full primary key, not only part of it."
    )
    print("\n--- 2NF Tables ---")
    for table_name, table_data in tables_2nf.items():
        print(f"\n{table_name} primary key = {Primary_key_2nf[table_name]}")
        print(table_data.to_string(index=False))

    print("\n3NF Definition:")
    print(
        "3NF means the data is already in 2NF and no non-key column depends "
        "on another non-key column."
    )
    print(
        "Here, instructor_name and instructor_office depend on instructor_id, "
        "so they move into the instructors table."
    )
    print("\n--- 3NF Tables ---")
    for table_name, table_data in tables_3nf.items():
        print(f"\n{table_name} primary key = {Primary_key_3nf[table_name]}")
        print(table_data.to_string(index=False))


if __name__ == "__main__":
    main()
