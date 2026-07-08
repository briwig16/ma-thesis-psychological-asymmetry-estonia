import pandas as pd
import numpy as np
import pyreadstat
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from factor_analyzer import FactorAnalyzer
import pingouin as pg

# Load 2020 data
df, meta = pyreadstat.read_sav("../data/EIM 2020_20.10.25.sav copy", encoding="latin1")

# K3X1: "How would you rate the opportunities and situation of Estonians
# and people of other nationalities?"
# Same scale as 2023 Q44: 1 = much better for Estonians ... 5 = much better for others; 9 = DK
#
# 2020 items (K3X1_1 to K3X1_12) differ from 2023 (Q44_1 to Q44_12):
#   K3X1_1:  Material well-being / opportunities     ~ Q44_1
#   K3X1_2:  Cultural opportunities                   ~ Q44_2
#   K3X1_3:  Education / self-improvement             ~ Q44_3
#   K3X1_4:  Political activity                       ~ Q44_4
#   K3X1_5:  Local government decision-making         (no 2023 equivalent)
#   K3X1_6:  Good job opportunities                   ~ Q44_6
#   K3X1_7:  Leadership in state/local government     (no 2023 equivalent)
#   K3X1_8:  Leadership in private sector             (no 2023 equivalent)
#   K3X1_9:  Civic organization participation         (no 2023 equivalent)
#   K3X1_10: Housing                                  ~ Q44_8
#   K3X1_11: Access to reliable information           (no 2023 equivalent)
#   K3X1_12: Public services and benefits             ~ Q44_12

items = [
    "K3X1_1", "K3X1_2", "K3X1_3", "K3X1_4", "K3X1_5", "K3X1_6",
    "K3X1_7", "K3X1_8", "K3X1_9", "K3X1_10", "K3X1_11", "K3X1_12",
]

labels = [
    "Material well-being", "Cultural opportunities", "Education",
    "Political activity", "Local govt decisions", "Good jobs",
    "Leadership (public)", "Leadership (private)", "Civic orgs",
    "Housing", "Reliable information", "Public services",
]

# Recode 9 -> NaN
for col in items:
    df[col] = df[col].replace(9, np.nan)


def run_analysis(data, label):
    sub = data[items].dropna()
    n = len(sub)

    print("\n" + "#" * 60)
    print("  {} (N = {})".format(label, n))
    print("#" * 60)

    # PCA
    scaler = StandardScaler()
    pca_data = scaler.fit_transform(sub)
    pca = PCA()
    pca.fit(pca_data)

    print("\n{:<12} {:>12} {:>12} {:>14}".format(
        "Component", "Eigenvalue", "% Variance", "Cumulative %"))
    print("-" * 52)
    cum = 0
    for i, (ev, evr) in enumerate(zip(pca.explained_variance_, pca.explained_variance_ratio_), 1):
        cum += evr * 100
        print("  {:<10} {:>12.4f} {:>11.2f}% {:>12.2f}%".format(i, ev, evr * 100, cum))

    print("\nComponent Loadings (PC1):")
    print("{:<15} {:>10}".format("Item", "Loading"))
    print("-" * 26)
    for item, loading in zip(items, pca.components_[0]):
        print("  {:<13} {:>10.4f}".format(item, loading))

    n_kaiser = sum(1 for ev in pca.explained_variance_ if ev > 1)
    print("\nKaiser criterion: {} component(s) retained".format(n_kaiser))

    # Cronbach's Alpha
    alpha_result = pg.cronbach_alpha(sub)
    alpha = alpha_result[0]
    ci = alpha_result[1]
    print("\nCronbach's Alpha: {:.4f}".format(alpha))
    print("95% CI: [{:.4f}, {:.4f}]".format(ci[0], ci[1]))

    # RMSR
    R = sub.corr().values
    k = R.shape[0]
    fa = FactorAnalyzer(n_factors=1, method="principal", rotation=None)
    fa.fit(sub)
    loadings = fa.loadings_
    R_reproduced = loadings @ loadings.T
    residual = R - R_reproduced
    off_diag_mask = ~np.eye(k, dtype=bool)
    rmsr = np.sqrt(np.mean(residual[off_diag_mask] ** 2))
    print("RMSR: {:.4f}".format(rmsr))

    # Factor loadings & communalities
    print("\nFactor Loadings (1-factor, principal axis):")
    print("{:<15} {:>10} {:>10}".format("Item", "Loading", "h\u00b2"))
    print("-" * 36)
    communalities = fa.get_communalities()
    for item, l, h2 in zip(items, loadings.flatten(), communalities):
        print("  {:<13} {:>10.4f} {:>10.4f}".format(item, l, h2))

    # Correlation matrix
    print("\nCorrelation Matrix:")
    print(sub.corr().round(4).to_string())


# Estonian respondents (T9_1 == 1)
est_data = df[df["T9_1"] == 1].copy()
run_analysis(est_data, "2020 ESTONIAN RESPONDENTS")

# Russian respondents (T9_2 == 1)
rus_data = df[df["T9_2"] == 1].copy()
run_analysis(rus_data, "2020 RUSSIAN RESPONDENTS")
