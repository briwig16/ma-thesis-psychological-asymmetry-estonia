import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Load data
df = pd.read_csv("../data/EIM23.csv")

# Filter to only Estonian (0) and Russian (1) respondents
df = df[df["ethnicity_binary"].isin([0, 1])].copy()
print(f"Respondents after filtering to Estonian/Russian: {len(df)}")

# Define the Q67 items
items = ["Q67_1", "Q67_2", "Q67_4", "Q67_5"]

# Replace 9 (Don't know) with NaN across Q67 items
for col in items:
    df[col] = df[col].replace(9, np.nan)

print(f"\nMissing values after recoding 9 as NaN:")
print(df[items].isna().sum())

# Reverse-code Q67_4 (scale is 1-4, so inverse = 5 - value)
# Q67_4: "Feel like a second-class citizen" — reversed so higher = more belonging
df["Q67_4_inv"] = 5 - df["Q67_4"]

# Create composite score: average of Q67_2, Q67_4_inv, Q67_5 (3-item version)
# Q67_1 dropped — weakened Russian scale; 3-item version has better psychometric properties
composite_items = ["Q67_2", "Q67_4_inv", "Q67_5"]
df["composite_belonging"] = df[composite_items].mean(axis=1)

print(f"\nComposite score (composite_belonging) descriptives:")
print(df["composite_belonging"].describe())
print(f"Missing: {df['composite_belonging'].isna().sum()}")

# --- PCA ---
# Use only complete cases for PCA
pca_items = ["Q67_2", "Q67_4_inv", "Q67_5"]
pca_df = df[pca_items].dropna()
print(f"\nComplete cases for PCA: {len(pca_df)}")

# Standardize
scaler = StandardScaler()
pca_data = scaler.fit_transform(pca_df)

# Fit PCA with all components
pca = PCA()
pca.fit(pca_data)

print("\n=== PCA Results ===")
print(f"\nEigenvalues:")
for i, ev in enumerate(pca.explained_variance_, 1):
    print(f"  Component {i}: {ev:.4f}")

print(f"\nExplained variance ratio:")
for i, evr in enumerate(pca.explained_variance_ratio_, 1):
    print(f"  Component {i}: {evr:.4f} ({evr*100:.1f}%)")

print(f"\nCumulative variance explained:")
cum = np.cumsum(pca.explained_variance_ratio_)
for i, c in enumerate(cum, 1):
    print(f"  Components 1-{i}: {c:.4f} ({c*100:.1f}%)")

print(f"\nComponent loadings (Component 1):")
for item, loading in zip(pca_items, pca.components_[0]):
    print(f"  {item}: {loading:.4f}")

# Kaiser criterion: retain components with eigenvalue > 1
n_kaiser = sum(1 for ev in pca.explained_variance_ if ev > 1)
print(f"\nKaiser criterion: {n_kaiser} component(s) with eigenvalue > 1")

# Save updated dataset
df.to_csv("../data/EIM23.csv", index=False)
print("\nSaved updated dataset with 'Q67_4_inv' and 'composite_belonging' columns.")
