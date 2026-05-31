import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Notebook display settings
# %matplotlib inline
plt.rcParams['figure.dpi'] = 120
sns.set_theme(style='whitegrid', palette='muted')

# Load dataset
df = sns.load_dataset('titanic').dropna(subset=['age', 'embarked'])

df['age_group'] = pd.cut(
    df['age'],
    bins=[0, 12, 18, 35, 60, 120],
    labels=['Child', 'Teen', 'Young Adult', 'Adult', 'Senior']
)

print('Dataset Shape:', df.shape)

# Create a grouped bar chart showing survival rate by both class and sex
plt.figure(figsize=(8, 6))
sns.barplot(data=df, x='pclass', y='survived', hue='sex', errorbar=None)

# Add labels and title
plt.title('Titanic Survival Rate by Class and Sex')
plt.xlabel('Class (pclass)')
plt.ylabel('Survival Rate')
plt.ylim(0, 1)

# Save the plot
plt.savefig('survival_rate.png')
print('Plot saved to survival_rate.png')