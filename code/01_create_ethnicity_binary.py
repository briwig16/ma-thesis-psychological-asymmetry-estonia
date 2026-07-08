import pandas as pd

# Load data
df = pd.read_csv("../data/EIM23.csv")

# Create binary ethnicity variable from T8
# T8: 1 = Estonian, 2 = Russian
# Keep only Estonian (1) and Russian (2), code others as NaN
df["ethnicity_binary"] = df["T8"].map({1: 0, 2: 1})

# Labels: 0 = Estonian, 1 = Russian
# Rows with other T8 values get NaN (excluded from analyses using this variable)

# Verify
print("ethnicity_binary value counts:")
print(df["ethnicity_binary"].value_counts(dropna=False))
print(f"\nTotal Estonian (0): {(df['ethnicity_binary'] == 0).sum()}")
print(f"Total Russian (1): {(df['ethnicity_binary'] == 1).sum()}")
print(f"Excluded (NaN): {df['ethnicity_binary'].isna().sum()}")

# Save updated dataset
df.to_csv("../data/EIM23.csv", index=False)
print("\nSaved updated dataset with 'ethnicity_binary' column to data/EIM23.csv")
