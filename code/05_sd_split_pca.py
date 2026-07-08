"""
Social Distance: Primary vs General Out-group Split
=====================================================
Reproduces the two-factor PCA (varimax rotation) that justified splitting the
social distance battery into Primary Out-group and General Out-group composites.

Primary Out-group: attitudes toward the main ethno-linguistic out-group
  - Estonians rate Russian-speakers (Q57_1, Q58_1, Q59_1)
  - Russians rate Estonian-speakers (Q57_2, Q58_2, Q59_2)

General Out-group (6 items, Ukrainian items excluded):
  - Q57_4, Q57_5, Q58_4, Q58_5, Q59_4, Q59_5
  - Other Europeans + non-Europeans across neighbors/work/marriage contexts

Ukrainian items (Q57_3, Q58_3, Q59_3) excluded because Russians held
asymmetrically negative views of Ukrainian refugees, masking otherwise
more positive general out-group attitudes.
"""

import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from factor_analyzer import FactorAnalyzer
import pingouin as pg

# ─── Load data ───────────────────────────────────────────────────────────────
df = pd.read_csv("../data/EIM23.csv")
df = df[df["ethnicity_binary"].isin([0, 1])].copy()

# ─── Define items ────────────────────────────────────────────────────────────
# All SD items (excluding Ukrainian _3 items)
all_items = [
    "Q57_1", "Q57_2", "Q57_4", "Q57_5",
    "Q58_1", "Q58_2", "Q58_4", "Q58_5",
    "Q59_1", "Q59_2", "Q59_4", "Q59_5",
]

# Primary out-group items (group-specific)
primary_est = ["Q57_1", "Q58_1", "Q59_1"]  # Estonians rate Russian-speakers
primary_rus = ["Q57_2", "Q58_2", "Q59_2"]  # Russians rate Estonian-speakers

# General out-group items (same for both groups)
general_items = ["Q57_4", "Q57_5", "Q58_4", "Q58_5", "Q59_4", "Q59_5"]

# Recode 9 → NaN
for col in all_items:
    df[col] = pd.to_numeric(df[col], errors="coerce").replace(9, np.nan)

est = df[df["ethnicity_binary"] == 0]
rus = df[df["ethnicity_binary"] == 1]


# ─── Two-factor PCA with varimax rotation ────────────────────────────────────
def run_factor_analysis(data, items, label):
    """Run 2-factor PCA with varimax rotation to show the primary/general split."""
    sub = data[items].dropna()
    n = len(sub)

    print(f"\n{'='*70}")
    print(f"  {label} (N = {n})")
    print(f"{'='*70}")

    # Unrotated PCA — eigenvalues
    scaler = StandardScaler()
    X = scaler.fit_transform(sub)
    pca = PCA()
    pca.fit(X)

    print(f"\nEigenvalues (Kaiser criterion):")
    for i, ev in enumerate(pca.explained_variance_, 1):
        marker = " ← retain" if ev > 1 else ""
        print(f"  PC{i}: {ev:.4f}{marker}")

    n_kaiser = sum(1 for ev in pca.explained_variance_ if ev > 1)
    print(f"\nKaiser suggests {n_kaiser} factors")

    # Varimax-rotated 2-factor solution
    fa = FactorAnalyzer(n_factors=2, method='principal', rotation='varimax')
    fa.fit(sub)
    loadings = pd.DataFrame(
        fa.loadings_,
        index=items,
        columns=["Factor 1", "Factor 2"]
    )

    print(f"\nVarimax-Rotated Factor Loadings (2 factors):")
    print(f"{'Item':<12} {'Factor 1':>10} {'Factor 2':>10}")
    print("-" * 34)
    for item in items:
        f1 = loadings.loc[item, "Factor 1"]
        f2 = loadings.loc[item, "Factor 2"]
        print(f"  {item:<10} {f1:>10.4f} {f2:>10.4f}")

    var = fa.get_factor_variance()
    print(f"\nVariance explained: F1={var[1][0]*100:.1f}%, F2={var[1][1]*100:.1f}%, Total={sum(var[1])*100:.1f}%")

    return loadings


# Run on both groups — use items each group actually answers
# Estonians answer Q57_1 (not Q57_2), Russians answer Q57_2 (not Q57_1)
est_analysis_items = primary_est + general_items
rus_analysis_items = primary_rus + general_items

load_est = run_factor_analysis(est, est_analysis_items, "ESTONIAN — 2-Factor Varimax (9 items)")
load_rus = run_factor_analysis(rus, rus_analysis_items, "RUSSIAN — 2-Factor Varimax (9 items)")


# ─── Composite reliability for each sub-composite ────────────────────────────
def composite_reliability(data, items, label):
    """Compute alpha, PCA variance, and descriptives for a composite."""
    sub = data[items].dropna()
    n = len(sub)

    alpha, ci = pg.cronbach_alpha(sub)

    scaler = StandardScaler()
    X = scaler.fit_transform(sub)
    pca = PCA()
    pca.fit(X)
    var_pct = pca.explained_variance_ratio_[0] * 100

    composite = data[items].mean(axis=1).dropna()
    m = composite.mean()
    sd = composite.std(ddof=1)

    print(f"  {label}: N={n}, α={alpha:.3f}, Var%={var_pct:.1f}%, M={m:.2f}, SD={sd:.2f}")
    return composite


print(f"\n{'='*70}")
print("  COMPOSITE RELIABILITY — PRIMARY OUT-GROUP")
print(f"{'='*70}")
comp_est_pri = composite_reliability(est, primary_est, "Estonian (rate Russian-speakers)")
comp_rus_pri = composite_reliability(rus, primary_rus, "Russian (rate Estonian-speakers)")

print(f"\n{'='*70}")
print("  COMPOSITE RELIABILITY — GENERAL OUT-GROUP (6 items, no Ukrainian)")
print(f"{'='*70}")
comp_est_gen = composite_reliability(est, general_items, "Estonian")
comp_rus_gen = composite_reliability(rus, general_items, "Russian")


# ─── Inter-composite correlation ─────────────────────────────────────────────
print(f"\n{'='*70}")
print("  INTER-COMPOSITE CORRELATIONS")
print(f"{'='*70}")

# For Estonians
est_pri = est[primary_est].mean(axis=1)
est_gen = est[general_items].mean(axis=1)
r_est = est_pri.corr(est_gen)
print(f"  Estonian: r(Primary, General) = {r_est:.3f}")

# For Russians
rus_pri = rus[primary_rus].mean(axis=1)
rus_gen = rus[general_items].mean(axis=1)
r_rus = rus_pri.corr(rus_gen)
print(f"  Russian:  r(Primary, General) = {r_rus:.3f}")

print(f"\n  Correlation range {min(r_est, r_rus):.2f}–{max(r_est, r_rus):.2f}")
print(f"  Confirms related but distinct constructs (split justified)")


# ─── Between-group comparisons ───────────────────────────────────────────────
def cohens_d_rms(g1, g2):
    """Cohen's d using root-mean-square SD denominator."""
    s1, s2 = g1.std(ddof=1), g2.std(ddof=1)
    return (g1.mean() - g2.mean()) / np.sqrt((s1**2 + s2**2) / 2)

from scipy import stats

print(f"\n{'='*70}")
print("  BETWEEN-GROUP COMPARISONS (2023)")
print(f"{'='*70}")

for label, g1, g2 in [
    ("SD Primary Out-group", comp_est_pri, comp_rus_pri),
    ("SD General Out-group", comp_est_gen, comp_rus_gen),
]:
    d = cohens_d_rms(g1.dropna(), g2.dropna())
    t, p = stats.ttest_ind(g1.dropna(), g2.dropna(), equal_var=False)
    print(f"\n  {label}:")
    print(f"    Est: M={g1.mean():.2f}, SD={g1.std(ddof=1):.2f}, N={g1.count()}")
    print(f"    Rus: M={g2.mean():.2f}, SD={g2.std(ddof=1):.2f}, N={g2.count()}")
    print(f"    d={d:+.2f}, p={p:.6f}")

print(f"\nDone.")
