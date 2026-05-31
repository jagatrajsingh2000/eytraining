import pandas as pd
import numpy as np

# 1. Create a sample DataFrame with some missing values (NaN)
data = {
    'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eva', 'Frank'],
    'Age': [25, np.nan, 30, 25, 22, np.nan],
    'Salary': [50000, 60000, np.nan, 80000, np.nan, 70000],
    'Department': ['HR', 'IT', 'IT', 'Marketing', np.nan, 'HR'],
    'Temporary_Col': [1, 2, 3, 4, 5, 6]
}

df = pd.DataFrame(data)
print("Original DataFrame:")
print(df)
print("-" * 60)

# 2. Drop rows (dropna)
# Drop any row that contains at least one NaN value
df_dropped_rows = df.dropna()
print("1. Dropped rows with any missing values:")
print(df_dropped_rows)
print("-" * 60)

# 3. Fill missing values with Mean
# Calculate mean of 'Age' column and fill its missing values
mean_age = df['Age'].mean()
df_fill_mean = df.copy()
df_fill_mean['Age'] = df_fill_mean['Age'].fillna(mean_age)
print(f"2. Filled missing 'Age' values with Mean ({mean_age:.2f}):")
print(df_fill_mean)
print("-" * 60)

# 4. Fill missing values with Median
# Calculate median of 'Salary' column and fill its missing values
median_salary = df['Salary'].median()
df_fill_median = df.copy()
df_fill_median['Salary'] = df_fill_median['Salary'].fillna(median_salary)
print(f"3. Filled missing 'Salary' values with Median ({median_salary}):")
print(df_fill_median)
print("-" * 60)

# 5. Fill missing values with Mode (most frequent value)
# Calculate mode of 'Department' column (mode() returns a Series, so we take index 0)
mode_dept = df['Department'].mode()[0]
df_fill_mode = df.copy()
df_fill_mode['Department'] = df_fill_mode['Department'].fillna(mode_dept)
print(f"4. Filled missing 'Department' values with Mode ('{mode_dept}'):")
print(df_fill_mode)
print("-" * 60)

# 6. Drop column
# Drop 'Temporary_Col' from the DataFrame
df_dropped_col = df.drop(columns=['Temporary_Col'])
print("5. Dropped 'Temporary_Col' column:")
print(df_dropped_col)
print("-" * 60)
