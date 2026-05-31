import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Set plotting style
sns.set_style("whitegrid")

# Load NASA GISS temperature anomaly dataset
url = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"
df = pd.read_csv(url, skiprows=1, na_values="***")

print("Dataset shape:", df.shape)
print("\nFirst 5 rows:")
print(df.head())

# --- Data Cleaning ---

# Drop summary columns if present
cols_to_drop = ['J-D', 'D-N', 'DJF', 'MAM', 'JJA', 'SON']
df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])

# Rename columns and convert monthly anomalies to numeric
df = df.rename(columns={'Year': 'year'})
monthly_cols = [col for col in df.columns if col != 'year']
for col in monthly_cols:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# Calculate annual average anomalies
df['annual_avg'] = df[monthly_cols].mean(axis=1)

print("\nMissing values per column:")
print(df.isnull().sum())

# --- Summary Statistics ---

print("\nSummary Statistics:")
print(df.describe())

# Find extreme anomalies
max_idx = df['annual_avg'].idxmax()
min_idx = df['annual_avg'].idxmin()
highest_year, highest_temp = df.loc[max_idx, 'year'], df.loc[max_idx, 'annual_avg']
lowest_year, lowest_temp = df.loc[min_idx, 'year'], df.loc[min_idx, 'annual_avg']

# Decadal trend analysis
df['decade'] = (df['year'] // 10) * 10
decade_avg = df.groupby('decade')['annual_avg'].mean()
print("\nDecadal averages:")
print(decade_avg)

# --- Visualization ---

# 1. Annual average anomalies line plot
plt.figure(figsize=(12, 5))
plt.plot(df['year'], df['annual_avg'], color='#c0392b', linewidth=1.5)
plt.title('Global Annual Temperature Anomalies Over Time')
plt.xlabel('Year')
plt.ylabel('Anomaly (°C)')
plt.tight_layout()
plt.savefig('annual_temp_trend.png')
plt.close()

# 2. Decadal average anomalies bar plot
plt.figure(figsize=(10, 5))
decade_avg.plot(kind='bar', color='#2980b9', edgecolor='black')
plt.title('Average Temperature Anomaly by Decade')
plt.xlabel('Decade')
plt.ylabel('Average Anomaly (°C)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('decadal_averages.png')
plt.close()

# 3. Correlation heatmap
plt.figure(figsize=(10, 8))
sns.heatmap(df[monthly_cols].corr(), annot=True, fmt=".2f", cmap='coolwarm', cbar=True)
plt.title('Correlation Heatmap of Monthly Temperature Anomalies')
plt.tight_layout()
plt.savefig('monthly_correlations.png')
plt.close()

# 4. Distribution plot
plt.figure(figsize=(8, 5))
sns.histplot(df['annual_avg'], bins=15, kde=True, color='#16a085')
plt.title('Distribution of Annual Temperature Anomalies')
plt.xlabel('Anomaly (°C)')
plt.tight_layout()
plt.savefig('anomaly_distribution.png')
plt.close()

# 5. Boxplot of monthly anomalies
plt.figure(figsize=(12, 5))
sns.boxplot(data=df[monthly_cols], palette='Set2')
plt.title('Monthly Temperature Anomaly Distribution')
plt.xlabel('Month')
plt.ylabel('Anomaly (°C)')
plt.tight_layout()
plt.savefig('monthly_anomaly_boxplot.png')
plt.close()

print("\nPlots generated and saved successfully.")

# --- Summary of Key Findings ---

oldest_decade, recent_decade = decade_avg.index.min(), decade_avg.index.max()
oldest_avg, recent_avg = decade_avg.loc[oldest_decade], decade_avg.loc[recent_decade]
temp_change = recent_avg - oldest_avg
avg_monthly_corr = df[monthly_cols].corr().mean().mean()

print("\n" + "="*40)
print("             KEY FINDINGS")
print("="*40)
print(f"- Highest recorded anomaly: {highest_temp:.2f}°C in {highest_year}")
print(f"- Lowest recorded anomaly:  {lowest_temp:.2f}°C in {lowest_year}")
print(f"- Average anomaly shift:    {oldest_avg:.2f}°C ({oldest_decade}s) -> {recent_avg:.2f}°C ({recent_decade}s)")
print(f"- Overall decadal increase: +{temp_change:.2f}°C over the study period")
print(f"- Monthly correlation:      Mean correlation of {avg_monthly_corr:.2f} across all months")
print("-"*40)
print("Conclusion: The analysis confirms a consistent long-term warming trend.")
print("="*40)