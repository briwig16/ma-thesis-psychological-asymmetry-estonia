import pandas as pd
import numpy as np
import pyreadstat
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from factor_analyzer import FactorAnalyzer
import pingouin as pg

# Load 2020 data
df, meta = pyreadstat.read_sav("../data/EIM 2020_20.10.25.sav copy", encoding="latin1")

# K6X6: same Q68 battery as 2023
# Scale: 1 = strongly agree ... 4 = strongly disagree; 9 = DK -> NaN
# K6X6_1: Involving non-Estonians in economy management is beneficial
# K6X6_2: Involving non-Estonians in state governance is beneficial
# K6X6_3: Non-Estonian opinions should be better understood/considered

items = ["K6X6_1", "K6X6_2", "K6X6_3"]

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
run_analysis(df[df["T9_1"] == 1], "2020 ESTONIAN RESPONDENTS")

# Russian respondents (T9_2 == 1)
run_analysis(df[df["T9_2"] == 1], "2020 RUSSIAN RESPONDENTS")
