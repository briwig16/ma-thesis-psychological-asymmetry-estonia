"""
Ad-hoc diagnostic: statistical evidence for dropping Q67_1 from the
Superordinate Identity composite. Compares the 4-item solution (incl. Q67_1)
against the 3-item solution, by ethnicity, 2023 data. Same method as
10_pca_by_ethnicity.py.
"""
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pingouin as pg

df = pd.read_csv("../data/EIM23.csv")
df = df[df["ethnicity_binary"].isin([0, 1])].copy()

for col in ["Q67_1", "Q67_2", "Q67_4", "Q67_5"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").replace(9, np.nan)
df["Q67_4_inv"] = 5 - df["Q67_4"]

items4 = ["Q67_1", "Q67_2", "Q67_4_inv", "Q67_5"]
items3 = ["Q67_2", "Q67_4_inv", "Q67_5"]


def pca_alpha(data, items, label):
    sub = data[items].dropna()
    n = len(sub)
    scaler = StandardScaler()
    pca = PCA()
    pca.fit(scaler.fit_transform(sub))
    evr = pca.explained_variance_ratio_[0] * 100
    ev1 = pca.explained_variance_[0]
    n_kaiser = int(sum(1 for ev in pca.explained_variance_ if ev > 1))
    alpha, ci = pg.cronbach_alpha(sub)
    print(f"\n  {label} (N={n})")
    print(f"    PC1 eigenvalue={ev1:.3f}  PC1 var={evr:.1f}%  "
          f"Kaiser components>1: {n_kaiser}")
    print(f"    Cronbach alpha={alpha:.3f}  95% CI[{ci[0]:.3f},{ci[1]:.3f}]")
    # PC1 loadings
    print("    PC1 loadings:")
    for it, ld in zip(items, pca.components_[0]):
        print(f"      {it:<12}{ld:>8.3f}")


def item_total(data, items, focus, label):
    """Corrected item-total correlation + alpha-if-item-deleted for `focus`."""
    sub = data[items].dropna()
    rest = [i for i in items if i != focus]
    corr = sub[focus].corr(sub[rest].mean(axis=1))
    alpha_dropped, _ = pg.cronbach_alpha(sub[rest])
    alpha_full, _ = pg.cronbach_alpha(sub[items])
    print(f"    {label}: {focus} corrected item-total r = {corr:.3f} | "
          f"alpha with {focus} = {alpha_full:.3f} -> alpha if dropped = {alpha_dropped:.3f}")


for name, code in [("ESTONIAN", 0), ("RUSSIAN", 1)]:
    d = df[df["ethnicity_binary"] == code]
    print("\n" + "=" * 64)
    print(f"  {name} RESPONDENTS (2023)")
    print("=" * 64)
    pca_alpha(d, items4, "4-item (Q67_1 included)")
    pca_alpha(d, items3, "3-item (Q67_1 dropped)")
    print()
    item_total(d, items4, "Q67_1", name.title())

# Correlation of Q67_1 with each retained item, Russians
print("\n" + "=" * 64)
print("  Q67_1 inter-item correlations (within 4-item set)")
print("=" * 64)
for name, code in [("Estonian", 0), ("Russian", 1)]:
    sub = df[df["ethnicity_binary"] == code][items4].dropna()
    cors = sub.corr()["Q67_1"].drop("Q67_1")
    print(f"  {name}: " + "  ".join(f"{k}={v:.3f}" for k, v in cors.items()))
