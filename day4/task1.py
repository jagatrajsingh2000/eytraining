# RUN THIS CELL TO SETUP THE CHALLENGE DATA

import pandas as pd
import sqlite3

conn_challenge = sqlite3.connect(":memory:")

challenge_data = {
    "Visit_ID": [5001, 5001, 5002, 5003],
    "Student_ID": [101, 101, 102, 104],
    "Student_Name": ["Alice", "Alice", "Bob", "David"],
    "Doctor_ID": ["DOC_XYZ", "DOC_XYZ", "DOC_ABC", "DOC_XYZ"],
    "Doctor_Name": ["Dr. Evans", "Dr. Evans", "Dr. Green", "Dr. Evans"],
    "Doctor_Clinic": ["General Medicine", "General Medicine", "Sports Med", "General Medicine"],
    "Prescriptions": ["Amoxicillin, Ibuprofen", "Amoxicillin, Ibuprofen", "Bandages", "Vitamin D"]
}

df_challenge = pd.DataFrame(challenge_data)

df_challenge.to_sql(
    "Patient_Visits_0NF",
    conn_challenge,
    index=False,
    if_exists="replace"
)

print("--- Challenge Dataset (0NF) ---")
print(df_challenge.to_string(index=False))


# Task 1: Identify the Flaws

# 1. This table violates 1NF because the Prescriptions column contains
#    multiple values in one cell, for example: "Amoxicillin, Ibuprofen".
#    Culprit column: Prescriptions

# 2. If Visit_ID is the primary key:
#    Student_Name violates 2NF because Student_Name depends on Student_ID,
#    not directly on Visit_ID.
#
#    Doctor_Clinic violates 3NF because Doctor_Clinic depends on Doctor_ID,
#    not directly on Visit_ID.
#
#    Dependency:
#    Visit_ID -> Doctor_ID -> Doctor_Clinic

# 3. If Doctor_ID determines Doctor_Clinic, but Doctor_ID is not a primary key,
#    then BCNF is violated.
#    Reason: In BCNF, every determinant must be a candidate key.


# Task 2: Normalize into 1NF

df_1nf = df_challenge.copy()

# Split non-atomic values into lists
df_1nf["Prescriptions"] = df_1nf["Prescriptions"].str.split(", ")

# Create one row per prescription
df_1nf = df_1nf.explode("Prescriptions").reset_index(drop=True)

df_1nf.to_sql(
    "Patient_Visits_1NF",
    conn_challenge,
    index=False,
    if_exists="replace"
)

print("--- Normalized Dataset (1NF) ---")
print(df_1nf.to_string(index=False))
