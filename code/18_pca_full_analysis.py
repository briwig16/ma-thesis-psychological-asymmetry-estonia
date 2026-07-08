import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from factor_analyzer import FactorAnalyzer
import pingouin as pg
from scipy import stats

# Load data
df = pd.read_csv("../data/EIM23.csv")
df = df[df["ethnicity_binary"].isin([0, 1])].copy()

# Define items and recode
items_raw = ["Q67_1", "Q67_2", "Q67_4", "Q67_5"]
for col in items_raw:
    df[col] = df[col].replace(9, np.nan)

# Reverse-code Q67_4
df["Q67_4_inv"] = 5 - df["Q67_4"]

# Analysis items
pca_items = ["Q67_1", "Q67_2", "Q67_4_inv", "Q67_5"]
pca_df = df[pca_items].dropna()
n = len(pca_df)
print(f"Complete cases: {n}")

# ============================================================
# 1. PCA — Eigenvalues, Variance Explained, Component Loadings
# ============================================================
scaler = StandardScaler()
pca_data = scaler.fit_transform(pca_df)

pca = PCA()
pca.fit(pca_data)

print("\n" + "=" * 60)
print("PRINCIPAL COMPONENT ANALYSIS")
print("=" * 60)

print(f"\n{'Component':<12} {'Eigenvalue':>12} {'% Variance':>12} {'Cumulative %':>14}")
print("-" * 52)
cum = 0
for i, (ev, evr) in enumerate(zip(pca.explained_variance_, pca.explained_variance_ratio_), 1):
    cum += evr * 100
    print(f"  {i:<10} {ev:>12.4f} {evr*100:>11.2f}% {cum:>12.2f}%")

print(f"\nComponent Loadings (PC1):")
print(f"{'Item':<15} {'Loading':>10}")
print("-" * 26)
for item, loading in zip(pca_items, pca.components_[0]):
    print(f"  {item:<13} {loading:>10.4f}")

n_kaiser = sum(1 for ev in pca.explained_variance_ if ev > 1)
print(f"\nKaiser criterion: {n_kaiser} component(s) retained (eigenvalue > 1)")

# ============================================================
# 2. Cronbach's Alpha with 95% CI
# ============================================================
alpha_result = pg.cronbach_alpha(pca_df)
alpha = alpha_result[0]
ci = alpha_result[1]

print("\n" + "=" * 60)
print("RELIABILITY ANALYSIS")
print("=" * 60)
print(f"\nCronbach's Alpha: {alpha:.4f}")
print(f"95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]")
print(f"N items: {len(pca_items)}")
print(f"N cases: {n}")

# ============================================================
# 3. RMSR (Root Mean Square Residual)
# ============================================================
# Compute correlation matrix
R = pca_df.corr().values
k = R.shape[0]

# Reproduced correlation matrix from 1-factor solution
# Using factor_analyzer for a proper 1-factor extraction
fa = FactorAnalyzer(n_factors=1, method='principal', rotation=None)
fa.fit(pca_df)

loadings = fa.loadings_
# Reproduced correlation = loadings @ loadings^T + uniquenesses on diagonal
R_reproduced = loadings @ loadings.T

# Residual matrix (observed - reproduced), off-diagonal only
residual = R - R_reproduced

# RMSR: sqrt of mean of squared off-diagonal residuals
off_diag_mask = ~np.eye(k, dtype=bool)
off_diag_residuals = residual[off_diag_mask]
rmsr = np.sqrt(np.mean(off_diag_residuals ** 2))

print("\n" + "=" * 60)
print("ROOT MEAN SQUARE RESIDUAL (RMSR)")
print("=" * 60)
print(f"\nRMSR (1-factor solution): {rmsr:.4f}")
print(f"  (Values < 0.05 indicate good fit; < 0.08 acceptable)")

# Also print factor loadings from factor_analyzer for reference
print(f"\nFactor Loadings (1-factor, principal axis):")
print(f"{'Item':<15} {'Loading':>10}")
print("-" * 26)
for item, l in zip(pca_items, loadings.flatten()):
    print(f"  {item:<13} {l:>10.4f}")

# Communalities
communalities = fa.get_communalities()
print(f"\nCommunalities:")
print(f"{'Item':<15} {'h²':>10}")
print("-" * 26)
for item, h2 in zip(pca_items, communalities):
    print(f"  {item:<13} {h2:>10.4f}")

# Correlation matrix for reference
print("\n" + "=" * 60)
print("CORRELATION MATRIX")
print("=" * 60)
corr = pca_df.corr()
print(corr.round(4).to_string())
