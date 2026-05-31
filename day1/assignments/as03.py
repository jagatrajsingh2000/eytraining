import seaborn as sns
import ssl

# Solve potential SSL cert issues
ssl._create_default_https_context = ssl._create_unverified_context

# Load the Titanic dataset
print("Loading Titanic dataset from seaborn...")
titanic_original = sns.load_dataset('titanic')
print(f"Original Titanic dataset shape: {titanic_original.shape}\n")
print("-" * 60)

# 1. Drop rows which have missing values (with before and after shape)
# Make a copy first
df_drop_rows = titanic_original.copy()
shape_before_rows = df_drop_rows.shape
df_drop_rows_clean = df_drop_rows.dropna()
shape_after_rows = df_drop_rows_clean.shape

print("1. Dropping rows with any missing values:")
print(f"   Shape before dropping rows: {shape_before_rows}")
print(f"   Shape after dropping rows:  {shape_after_rows}")
print("-" * 60)

# 2. Drop only specific columns (e.g., 'alive', 'alone')
df_drop_cols = titanic_original.copy()
columns_to_drop = ['alive', 'alone']
df_drop_cols_clean = df_drop_cols.drop(columns=columns_to_drop)

print(f"2. Dropping specific columns {columns_to_drop}:")
print(f"   Original columns: {list(df_drop_cols.columns[:8])} ...")
print(f"   Modified columns: {list(df_drop_cols_clean.columns[:8])} ...")
print("-" * 60)

# 3. Fill missing values for 'age' with its mean
df_fill_age = titanic_original.copy()
mean_age = df_fill_age['age'].mean()
missing_age_before = df_fill_age['age'].isna().sum()

df_fill_age['age'] = df_fill_age['age'].fillna(mean_age)
missing_age_after = df_fill_age['age'].isna().sum()

print("3. Filling missing 'age' values with the mean:")
print(f"   Calculated mean age: {mean_age:.2f}")
print(f"   Missing 'age' values before: {missing_age_before}")
print(f"   Missing 'age' values after:  {missing_age_after}")
print("-" * 60)

# 4. Drop 'deck' column (too many missing values)
df_drop_deck = titanic_original.copy()
missing_deck = df_drop_deck['deck'].isna().sum()
total_rows = len(df_drop_deck)

df_drop_deck_clean = df_drop_deck.drop(columns=['deck'])

print("4. Dropping 'deck' column (too many missing values):")
print(f"   Missing 'deck' values: {missing_deck} out of {total_rows} total rows")
print(f"   Is 'deck' in original dataset? {'deck' in df_drop_deck.columns}")
print(f"   Is 'deck' in modified dataset? {'deck' in df_drop_deck_clean.columns}")
print("-" * 60)

# Verify original dataset is untouched
print("Verification: The original dataset shape is still:", titanic_original.shape)
print("-" * 60)

# 5. Find all male passengers who paid a fare above 200
male_high_fare = titanic_original[(titanic_original['sex'] == 'male') & (titanic_original['fare'] > 200)]
print("5. Male passengers who paid a fare above 200:")
print(male_high_fare[['sex', 'fare', 'class', 'age']])
print(f"   Total count: {len(male_high_fare)}")
print("-" * 60)

# 6. Using .loc, extract rows 100 to 109 and the last 3 columns
last_three_columns = list(titanic_original.columns[-3:])
extracted_data = titanic_original.loc[100:109, last_three_columns]

print(f"6. Extracted rows 100 to 109 and the last 3 columns {last_three_columns}:")
print(extracted_data)
print("-" * 60)

# 7. Using groupby, find the average fare paid by passengers of each embarking port
avg_fare_port = titanic_original.groupby('embark_town')['fare'].mean()
print("7. Average fare paid by passenger at each embarking port:")
print(avg_fare_port)
print("-" * 60)

# 8. Find the number of survivors per class, sorted from highest to lowest
# (Note: 'survived' contains 1 for survived and 0 for deceased, so sum() gives the total count of survivors)
survivors_per_class = titanic_original.groupby('class')['survived'].sum().sort_values(ascending=False)
print("8. Number of survivors per class (sorted highest to lowest):")
print(survivors_per_class)
print("-" * 60)

# 9. Create a second lookup table with port full name and merge it with df2 on 'embarked'
import pandas as pd

# Define df2 as a copy of the original dataset
df2 = titanic_original.copy()

# Create the port lookup DataFrame
port_lookup = pd.DataFrame({
    'embarked': ['S', 'C', 'Q'],
    'port_full_name': ['Southampton', 'Cherbourg', 'Queenstown']
})

print("9. Port Lookup Table:")
print(port_lookup)
print("-" * 60)

# Merge df2 with the lookup table on 'embarked'
df2_merged = pd.merge(df2, port_lookup, on='embarked', how='left')

print("Merged DataFrame (confirming 'port_full_name' column was added):")
print(df2_merged[['sex', 'embarked', 'embark_town', 'port_full_name']].head(10))
print(f"\nJoin Confirmation: Row count of original df2: {len(df2)} | Row count of merged df2: {len(df2_merged)}")
print("-" * 60)



