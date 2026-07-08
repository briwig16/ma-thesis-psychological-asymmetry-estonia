import pandas as pd
import numpy as np
import pyreadstat
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from factor_analyzer import FactorAnalyzer
import pingouin as pg

# Load 2020 data
df, meta = pyreadstat.read_sav("../data/EIM 2020_20.10.25.sav copy", encoding="latin1")

# 2020 social distance variables (3 out-groups x 3 contexts = 9 items):
# K4X7 = neighbors, K4X8 = work/study, K4X9 = marriage
# _1 = Russian-speakers, _2 = Estonian-speakers, _3 = new immigrants (last 5 years)
# Scale: 1 = very well ... 5 = very badly; 9 = don't know -> NaN
#
# 2020 has NO equivalents for 2023's _4 (other Europeans) or _5 (outside Europe).
# So the comparable composites use 6 items each:
#   Estonian composite: _1 (Russian-speakers) + _3 (new immigrants) across 3 contexts
#   Russian composite:  _2 (Estonian-speakers) + _3 (new immigrants) across 3 contexts

# Estonian out-group items (Russian-speakers + new immigrants)
estonian_items = ["K4X7_1", "K4X7_3", "K4X8_1", "K4X8_3", "K4X9_1", "K4X9_3"]

# Russian out-group items (Estonian-speakers + new immigrants)
russian_items = ["K4X7_2", "K4X7_3", "K4X8_2", "K4X8_3", "K4X9_2", "K4X9_3"]

# Recode 9 -> NaN for all relevant items
all_items = list(set(estonian_items + russian_items))
for col in all_items:
    df[col] = df[col].replace(9, np.nan)


def run_analysis(data, items, label):
    sub = data[items].dropna()
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
    fa = FactorAnalyzer(n_factors=1, method="principal", rotation=None)
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


# Estonian respondents (T9_1 == 1)
est_data = df[df["T9_1"] == 1].copy()
run_analysis(est_data, estonian_items, "2020 ESTONIAN RESPONDENTS (out-group: Russian-speakers + new immigrants)")

# Russian respondents (T9_2 == 1)
rus_data = df[df["T9_2"] == 1].copy()
run_analysis(rus_data, russian_items, "2020 RUSSIAN RESPONDENTS (out-group: Estonian-speakers + new immigrants)")
