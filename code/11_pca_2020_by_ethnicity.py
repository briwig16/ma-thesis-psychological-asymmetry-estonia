import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from factor_analyzer import FactorAnalyzer
import pingouin as pg
import pyreadstat

# Load 2020 data
df, meta = pyreadstat.read_sav("../data/EIM 2020_20.10.25.sav copy", encoding='latin1')

# Map 2020 variables to 2023 equivalents:
# K6X5_2 = "Feel proud seeing Estonian flag" (= Q67_2)
# K6X5_3 = "Feel like second-class citizen" (= Q67_4) — needs reverse coding
# K6X5_4 = "Feel part of Estonian society" (= Q67_5)

items_raw = ["K6X5_2", "K6X5_3", "K6X5_4"]

# Recode 9 (Don't know) as NaN
for col in items_raw:
    df[col] = df[col].replace(9, np.nan)

# Reverse-code K6X5_3 (second-class citizen)
df["K6X5_3_inv"] = 5 - df["K6X5_3"]

# Create ethnicity binary: Estonian (T9_1==1) vs Russian (T9_2==1)
# Some respondents may select multiple; keep only pure Estonian or pure Russian
df["is_estonian"] = (df["T9_1"] == 1).astype(int)
df["is_russian"] = (df["T9_2"] == 1).astype(int)

# Analysis items
pca_items = ["K6X5_2", "K6X5_3_inv", "K6X5_4"]
item_labels = {
    "K6X5_2": "Proud of flag (K6X5_2)",
    "K6X5_3_inv": "Not 2nd-class (K6X5_3 inv)",
    "K6X5_4": "Part of society (K6X5_4)"
}

def run_analysis(data, label):
    sub = data[pca_items].dropna()
    n = len(sub)

    print("\n" + "#" * 60)
    print(f"  {label} (N = {n})")
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
    print(f"{'Item':<30} {'Loading':>10}")
    print("-" * 41)
    for item, loading in zip(pca_items, pca.components_[0]):
        print(f"  {item_labels[item]:<28} {loading:>10.4f}")

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
    print(f"{'Item':<30} {'Loading':>10} {'h²':>10}")
    print("-" * 51)
    communalities = fa.get_communalities()
    for item, l, h2 in zip(pca_items, loadings.flatten(), communalities):
        print(f"  {item_labels[item]:<28} {l:>10.4f} {h2:>10.4f}")

    # Correlation matrix
    print(f"\nCorrelation Matrix:")
    corr = sub.corr()
    corr.index = [item_labels[i] for i in pca_items]
    corr.columns = ["Flag", "Not2ndClass", "PartSoc"]
    print(corr.round(4).to_string())


print("=" * 60)
print("  EIM 2020 — PCA BY ETHNICITY (3-item composite)")
print("=" * 60)

# Estonian respondents
run_analysis(df[df["is_estonian"] == 1], "ESTONIAN RESPONDENTS (2020)")

# Russian respondents
run_analysis(df[df["is_russian"] == 1], "RUSSIAN RESPONDENTS (2020)")
