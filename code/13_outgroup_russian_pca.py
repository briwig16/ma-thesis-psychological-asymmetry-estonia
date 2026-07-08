import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from factor_analyzer import FactorAnalyzer
import pingouin as pg

# Load data — Russian respondents only
df = pd.read_csv("../data/EIM23.csv")
df = df[df["ethnicity_binary"] == 1].copy()

# Items: social distance toward out-groups for Russian respondents
# _2 = Estonian-speakers (out-group for Russians), replacing _1 (Russian-speakers = in-group)
# _3 = Ukrainian refugees, _4 = other Europeans, _5 = outside Europe
# Q57 = neighbors, Q58 = work/study group, Q59 = marriage of close relative
# Scale: 1 = very well (no bother) ... 5 = very badly (bothers a lot)
# 9 = Don't know -> NaN

items = [
    "Q57_2", "Q57_3", "Q57_4", "Q57_5",
    "Q58_2", "Q58_3", "Q58_4", "Q58_5",
    "Q59_2", "Q59_3", "Q59_4",
]

# Coerce to numeric and recode 9 -> NaN
for col in items:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df[col] = df[col].replace(9, np.nan)

sub = df[items].dropna()
n = len(sub)

print("#" * 60)
print(f"  RUSSIAN RESPONDENTS — OUT-GROUP COMPOSITE (N = {n})")
print("#" * 60)

# PCA
scaler = StandardScaler()
pca_data = scaler.fit_transform(sub)
pca = PCA()
pca.fit(pca_data)

print(f"\n{'Component':<12} {'Eigenvalue':>12} {'% Variance':>12} {'Cumulative %':>14}")
print("-" * 52)
cum = 0
for i, (ev, evr) in enumerate(zip(pca.explained_variance_, pca.explained_variance_ratio_), 1):
    cum += evr * 100
    print(f"  {i:<10} {ev:>12.4f} {evr*100:>11.2f}% {cum:>12.2f}%")

print(f"\nComponent Loadings (PC1):")
print(f"{'Item':<15} {'Loading':>10}")
print("-" * 26)
for item, loading in zip(items, pca.components_[0]):
    print(f"  {item:<13} {loading:>10.4f}")

n_kaiser = sum(1 for ev in pca.explained_variance_ if ev > 1)
print(f"\nKaiser criterion: {n_kaiser} component(s) retained")

# Cronbach's Alpha
alpha_result = pg.cronbach_alpha(sub)
alpha = alpha_result[0]
ci = alpha_result[1]
print(f"\nCronbach's Alpha: {alpha:.4f}")
print(f"95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]")

# RMSR
R = sub.corr().values
k = R.shape[0]
fa = FactorAnalyzer(n_factors=1, method='principal', rotation=None)
fa.fit(sub)
loadings = fa.loadings_
R_reproduced = loadings @ loadings.T
residual = R - R_reproduced
off_diag_mask = ~np.eye(k, dtype=bool)
rmsr = np.sqrt(np.mean(residual[off_diag_mask] ** 2))
print(f"RMSR: {rmsr:.4f}")

# Factor loadings & communalities
print(f"\nFactor Loadings (1-factor, principal axis):")
print(f"{'Item':<15} {'Loading':>10} {'h²':>10}")
print("-" * 36)
communalities = fa.get_communalities()
for item, l, h2 in zip(items, loadings.flatten(), communalities):
    print(f"  {item:<13} {l:>10.4f} {h2:>10.4f}")

# Correlation matrix
print(f"\nCorrelation Matrix:")
print(sub.corr().round(4).to_string())
