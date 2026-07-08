import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from factor_analyzer import FactorAnalyzer
import pingouin as pg

# Load data
df = pd.read_csv("../data/EIM23.csv")
df = df[df["ethnicity_binary"].isin([0, 1])].copy()

# Q63: "To what extent do you agree with the following statements?"
# Scale: 1 = strongly agree, 2 = somewhat agree, 3 = somewhat disagree, 4 = strongly disagree
# 9 = Don't know -> NaN
#
# Q63_1: Conflicts between ethnic groups are inevitable (negative)
# Q63_2: Intercultural differences are dividing Estonian society (negative)
# Q63_3: Different ethnic groups can get along and cooperate (positive) -> reverse-code
# Q63_4: Immigration enriches Estonian cultural life (positive) -> reverse-code
#
# After reverse-coding Q63_3 and Q63_4: higher = more perceived ethnic tension

items_raw = ["Q63_1", "Q63_2", "Q63_3", "Q63_4"]

# Recode 9 -> NaN
for col in items_raw:
    df[col] = df[col].replace(9, np.nan)

# Reverse-code Q63_3 and Q63_4: inv = 5 - original (on 1-4 scale)
df["Q63_3_inv"] = 5 - df["Q63_3"]
df["Q63_4_inv"] = 5 - df["Q63_4"]

# Analysis items
items = ["Q63_1", "Q63_2", "Q63_3_inv", "Q63_4_inv"]


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


# Estonian respondents
run_analysis(df[df["ethnicity_binary"] == 0], "ESTONIAN RESPONDENTS")

# Russian respondents
run_analysis(df[df["ethnicity_binary"] == 1], "RUSSIAN RESPONDENTS")
