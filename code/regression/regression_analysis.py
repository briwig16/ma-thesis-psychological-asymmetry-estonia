import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Load data
df = pd.read_csv("../data/EIM23.csv")

# Filter to only Estonian (0) and Russian (1) respondents
df = df[df["ethnicity_binary"].isin([0, 1])].copy()
print(f"Starting N (Estonian/Russian): {len(df)}")

# --- Recode non-substantive responses as NaN ---

# T16 (income): 23 = No income, 24 = Prefer not to answer → NaN
# Keep 1-22 as ordinal income brackets
df["T16"] = df["T16"].replace({23: np.nan, 24: np.nan})

# Q117a (left-right): 98 = Do not wish to rate, 99 = Don't know → NaN
df["Q117a"] = df["Q117a"].replace({98: np.nan, 99: np.nan})

# T2 (gender): keep as-is (1=Male, 2=Female, 3=Other), treat as categorical
# T18 (education): 1-9, no non-substantive codes
# Vanus (age group): 1-4, no non-substantive codes
# Q118_1 (Center Party): already binary 0/1

# --- Set up variables ---

# DV
dv = "composite_belonging"

# IV + controls
# Treat T2 and Vanus as categorical (dummies)
df["female"] = (df["T2"] == 2).astype(int)
df["gender_other"] = (df["T2"] == 3).astype(int)

# Age group dummies (reference: 1 = 15-29)
df["age_30_44"] = (df["Vanus"] == 2).astype(int)
df["age_45_59"] = (df["Vanus"] == 3).astype(int)
df["age_60plus"] = (df["Vanus"] == 4).astype(int)

# Predictors
predictors = [
    "ethnicity_binary",  # 0=Estonian, 1=Russian
    "female",            # gender (ref: male)
    "gender_other",      # gender (ref: male)
    "age_30_44",         # age group (ref: 15-29)
    "age_45_59",
    "age_60plus",
    "T16",               # income (ordinal 1-22)
    "T18",               # education (ordinal 1-9)
    "Q117a",             # left-right scale (1-10)
    "Q118_1",            # Center Party (0/1)
]

# Drop rows with missing values on any variable used
vars_used = [dv] + predictors
df_reg = df[vars_used].dropna()
print(f"Complete cases for regression: {len(df_reg)}")
print(f"Dropped due to missingness: {len(df) - len(df_reg)}")

# --- OLS Regression ---
X = df_reg[predictors]
X = sm.add_constant(X)
y = df_reg[dv]

model = sm.OLS(y, X).fit()
print("\n" + "="*70)
print("OLS REGRESSION: Predictors of Composite Belonging Score")
print("DV: composite_belonging (1-4 scale, lower = stronger belonging)")
print("="*70)
print(model.summary())

# --- VIF for multicollinearity check ---
print("\n--- Variance Inflation Factors ---")
vif_data = pd.DataFrame()
vif_data["Variable"] = X.columns[1:]  # skip constant
vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(1, X.shape[1])]
print(vif_data.to_string(index=False))

# --- Standardized coefficients for effect size comparison ---
print("\n--- Standardized (Beta) Coefficients ---")
X_std = (X.iloc[:, 1:] - X.iloc[:, 1:].mean()) / X.iloc[:, 1:].std()
X_std = sm.add_constant(X_std)
y_std = (y - y.mean()) / y.std()
model_std = sm.OLS(y_std, X_std).fit()
for name, beta, pval in zip(predictors, model_std.params[1:], model_std.pvalues[1:]):
    sig = ""
    if pval < 0.001: sig = "***"
    elif pval < 0.01: sig = "**"
    elif pval < 0.05: sig = "*"
    print(f"  {name:20s}  β = {beta:7.4f}  p = {pval:.4f} {sig}")
