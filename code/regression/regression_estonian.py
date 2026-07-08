import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Load data
df = pd.read_csv("../data/EIM23.csv")

# Filter to Estonian respondents only
df = df[df["ethnicity_binary"] == 0].copy()
print(f"Estonian respondents: {len(df)}")

# --- Recode non-substantive responses as NaN ---

# T16 (income): 23 = No income, 24 = Prefer not to answer → NaN
df["T16"] = df["T16"].replace({23: np.nan, 24: np.nan})

# Q117a (left-right): 98 = Do not wish to rate, 99 = Don't know → NaN
df["Q117a"] = df["Q117a"].replace({98: np.nan, 99: np.nan})

# Q71_2, Q71_3 (language ability): 9 = Don't know → NaN
df["Q71_2"] = df["Q71_2"].replace(9, np.nan)
df["Q71_3"] = df["Q71_3"].replace(9, np.nan)

# --- Set up variables ---

# Gender dummies (T2, ref: male=1)
df["female"] = (df["T2"] == 2).astype(int)
df["gender_other"] = (df["T2"] == 3).astype(int)

# Age group dummies (ref: 15-29)
df["age_30_44"] = (df["Vanus"] == 2).astype(int)
df["age_45_59"] = (df["Vanus"] == 3).astype(int)
df["age_60plus"] = (df["Vanus"] == 4).astype(int)

# Parents birthplace dummies (ref: 1=Estonia)
df["parents_russia"] = (df["parents_birthplace"] == 2).astype(int)
df["parents_elsewhere"] = (df["parents_birthplace"] == 3).astype(int)

# Education language dummies (ref: 1=Estonian)
df["edu_lang_russian"] = (df["edu_language"] == 2).astype(int)
df["edu_lang_both"] = (df["edu_language"] == 3).astype(int)
df["edu_lang_est_other"] = (df["edu_language"] == 4).astype(int)

# Place of birth dummies (T10, ref: 1=Estonia)
df["born_russia"] = (df["T10"] == 2).astype(int)
df["born_elsewhere"] = (df["T10"] == 3).astype(int)

# Predictors
predictors = [
    "female",             # gender (ref: male)
    "gender_other",       # gender (ref: male)
    "age_30_44",          # age group (ref: 15-29)
    "age_45_59",
    "age_60plus",
    "T16",                # income (ordinal 1-22)
    "T18",                # education (ordinal 1-9)
    "Q117a",              # left-right scale (1-10)
    "Q118_1",             # Center Party (0/1)
    "parents_russia",     # parents birthplace (ref: Estonia)
    "parents_elsewhere",
    "edu_lang_russian",   # education language (ref: Estonian)
    "edu_lang_both",
    "edu_lang_est_other",
    "born_russia",        # place of birth (ref: Estonia)
    "born_elsewhere",
    "Q71_2",              # Russian language ability (1=native to 6=none)
    "Q71_3",              # English language ability (1=native to 6=none)
]

dv = "composite_belonging"

# Drop rows with missing values
vars_used = [dv] + predictors
df_reg = df[vars_used].dropna()
print(f"Complete cases for regression: {len(df_reg)}")
print(f"Dropped due to missingness: {len(df) - len(df_reg)}")

# Drop zero-variance predictors (no variation among Estonian respondents)
zero_var = [p for p in predictors if df_reg[p].std() == 0]
if zero_var:
    print(f"Dropped zero-variance predictors: {zero_var}")
    predictors = [p for p in predictors if p not in zero_var]

# --- OLS Regression ---
X = df_reg[predictors]
X = sm.add_constant(X)
y = df_reg[dv]

model = sm.OLS(y, X).fit()
print("\n" + "="*70)
print("OLS REGRESSION: Predictors of Belonging Among Estonian Respondents")
print("DV: composite_belonging (1-4 scale, lower = stronger belonging)")
print("="*70)
print(model.summary())

# --- VIF ---
print("\n--- Variance Inflation Factors ---")
vif_data = pd.DataFrame()
vif_data["Variable"] = X.columns[1:]
vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(1, X.shape[1])]
print(vif_data.to_string(index=False))

# --- Standardized coefficients ---
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
    print(f"  {name:22s}  B = {beta:7.4f}  p = {pval:.4f} {sig}")
