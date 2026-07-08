import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ============================================================
# Helper: run OLS and return results as a DataFrame
# ============================================================

def run_ols(df, dv, predictors):
    """Run OLS and return unstandardized + standardized results."""
    vars_used = [dv] + predictors
    df_reg = df[vars_used].dropna()

    # Drop zero-variance predictors
    zero_var = [p for p in predictors if df_reg[p].std() == 0]
    preds = [p for p in predictors if p not in zero_var]

    X = sm.add_constant(df_reg[preds])
    y = df_reg[dv]
    model = sm.OLS(y, X).fit()

    # Standardized model
    X_raw = df_reg[preds]
    X_std = (X_raw - X_raw.mean()) / X_raw.std()
    X_std = sm.add_constant(X_std)
    y_std = (y - y.mean()) / y.std()
    model_std = sm.OLS(y_std, X_std).fit()

    results = pd.DataFrame({
        "variable": preds,
        "coef": model.params[1:].values,
        "se": model.bse[1:].values,
        "ci_lo": model.conf_int().iloc[1:, 0].values,
        "ci_hi": model.conf_int().iloc[1:, 1].values,
        "pval": model.pvalues[1:].values,
        "beta": model_std.params[1:].values,
        "beta_se": model_std.bse[1:].values,
        "beta_ci_lo": model_std.conf_int().iloc[1:, 0].values,
        "beta_ci_hi": model_std.conf_int().iloc[1:, 1].values,
        "beta_pval": model_std.pvalues[1:].values,
    })
    return results, model, len(df_reg)


# ============================================================
# Load and prepare data
# ============================================================

df_all = pd.read_csv("../data/EIM23.csv")

# --- Pooled model data ---
df_pooled = df_all[df_all["ethnicity_binary"].isin([0, 1])].copy()
df_pooled["T16"] = df_pooled["T16"].replace({23: np.nan, 24: np.nan})
df_pooled["Q117a"] = df_pooled["Q117a"].replace({98: np.nan, 99: np.nan})
df_pooled["female"] = (df_pooled["T2"] == 2).astype(int)
df_pooled["gender_other"] = (df_pooled["T2"] == 3).astype(int)
df_pooled["age_30_44"] = (df_pooled["Vanus"] == 2).astype(int)
df_pooled["age_45_59"] = (df_pooled["Vanus"] == 3).astype(int)
df_pooled["age_60plus"] = (df_pooled["Vanus"] == 4).astype(int)

pooled_preds = [
    "ethnicity_binary", "female", "gender_other",
    "age_30_44", "age_45_59", "age_60plus",
    "T16", "T18", "Q117a", "Q118_1",
]

# --- Estonian model data ---
df_est = df_all[df_all["ethnicity_binary"] == 0].copy()
df_est["T16"] = df_est["T16"].replace({23: np.nan, 24: np.nan})
df_est["Q117a"] = df_est["Q117a"].replace({98: np.nan, 99: np.nan})
df_est["Q71_2"] = df_est["Q71_2"].replace(9, np.nan)
df_est["Q71_3"] = df_est["Q71_3"].replace(9, np.nan)
df_est["female"] = (df_est["T2"] == 2).astype(int)
df_est["gender_other"] = (df_est["T2"] == 3).astype(int)
df_est["age_30_44"] = (df_est["Vanus"] == 2).astype(int)
df_est["age_45_59"] = (df_est["Vanus"] == 3).astype(int)
df_est["age_60plus"] = (df_est["Vanus"] == 4).astype(int)
df_est["parents_russia"] = (df_est["parents_birthplace"] == 2).astype(int)
df_est["parents_elsewhere"] = (df_est["parents_birthplace"] == 3).astype(int)
df_est["edu_lang_russian"] = (df_est["edu_language"] == 2).astype(int)
df_est["edu_lang_both"] = (df_est["edu_language"] == 3).astype(int)
df_est["edu_lang_est_other"] = (df_est["edu_language"] == 4).astype(int)
df_est["born_russia"] = (df_est["T10"] == 2).astype(int)
df_est["born_elsewhere"] = (df_est["T10"] == 3).astype(int)

est_preds = [
    "female", "gender_other",
    "age_30_44", "age_45_59", "age_60plus",
    "T16", "T18", "Q117a", "Q118_1",
    "parents_russia", "edu_lang_russian", "edu_lang_both",
    "edu_lang_est_other", "born_russia", "born_elsewhere",
    "Q71_2", "Q71_3",
]

# --- Russian model data ---
df_rus = df_all[df_all["ethnicity_binary"] == 1].copy()
df_rus["T16"] = df_rus["T16"].replace({23: np.nan, 24: np.nan})
df_rus["Q117a"] = df_rus["Q117a"].replace({98: np.nan, 99: np.nan})
df_rus["Q71_1"] = df_rus["Q71_1"].replace(9, np.nan)
df_rus["Q71_3"] = df_rus["Q71_3"].replace(9, np.nan)
df_rus["female"] = (df_rus["T2"] == 2).astype(int)
df_rus["gender_other"] = (df_rus["T2"] == 3).astype(int)
df_rus["age_30_44"] = (df_rus["Vanus"] == 2).astype(int)
df_rus["age_45_59"] = (df_rus["Vanus"] == 3).astype(int)
df_rus["age_60plus"] = (df_rus["Vanus"] == 4).astype(int)
df_rus["parents_russia"] = (df_rus["parents_birthplace"] == 2).astype(int)
df_rus["parents_elsewhere"] = (df_rus["parents_birthplace"] == 3).astype(int)
df_rus["edu_lang_russian"] = (df_rus["edu_language"] == 2).astype(int)
df_rus["edu_lang_both"] = (df_rus["edu_language"] == 3).astype(int)
df_rus["edu_lang_est_other"] = (df_rus["edu_language"] == 4).astype(int)
df_rus["born_russia"] = (df_rus["T10"] == 2).astype(int)
df_rus["born_elsewhere"] = (df_rus["T10"] == 3).astype(int)

rus_preds = [
    "female", "gender_other",
    "age_30_44", "age_45_59", "age_60plus",
    "T16", "T18", "Q117a", "Q118_1",
    "parents_russia", "parents_elsewhere",
    "edu_lang_russian", "edu_lang_both", "edu_lang_est_other",
    "born_russia", "born_elsewhere",
    "Q71_1", "Q71_3",
]

# ============================================================
# Run models
# ============================================================

dv = "composite_belonging"
res_pooled, mod_pooled, n_pooled = run_ols(df_pooled, dv, pooled_preds)
res_est, mod_est, n_est = run_ols(df_est, dv, est_preds)
res_rus, mod_rus, n_rus = run_ols(df_rus, dv, rus_preds)

# ============================================================
# Pretty labels
# ============================================================

LABELS = {
    "ethnicity_binary": "Russian (ref: Estonian)",
    "female": "Female (ref: Male)",
    "gender_other": "Other gender (ref: Male)",
    "age_30_44": "Age 30\u201344 (ref: 15\u201329)",
    "age_45_59": "Age 45\u201359 (ref: 15\u201329)",
    "age_60plus": "Age 60+ (ref: 15\u201329)",
    "T16": "Income",
    "T18": "Education",
    "Q117a": "Left\u2013Right ideology",
    "Q118_1": "Center Party supporter",
    "parents_russia": "Parents born: Russia",
    "parents_elsewhere": "Parents born: Elsewhere",
    "edu_lang_russian": "Edu language: Russian",
    "edu_lang_both": "Edu language: Est. + Rus.",
    "edu_lang_est_other": "Edu language: Est. + Other",
    "born_russia": "Born in Russia",
    "born_elsewhere": "Born elsewhere",
    "Q71_1": "Estonian language ability",
    "Q71_2": "Russian language ability",
    "Q71_3": "English language ability",
}


def add_labels(res):
    res["label"] = res["variable"].map(LABELS).fillna(res["variable"])
    return res


res_pooled = add_labels(res_pooled)
res_est = add_labels(res_est)
res_rus = add_labels(res_rus)

# ============================================================
# Figure 1: Coefficient plots (standardized betas), one panel
#           per model, arranged vertically
# ============================================================

def plot_coef(ax, res, title, n, r2, color):
    """Draw a horizontal coefficient plot on ax."""
    res = res.copy().iloc[::-1]  # reverse so first predictor is at top
    y_pos = np.arange(len(res))

    # Color bars by significance
    colors = []
    for p in res["beta_pval"]:
        if p < 0.001:
            colors.append(color)
        elif p < 0.01:
            colors.append(color)
        elif p < 0.05:
            colors.append(color)
        else:
            colors.append("#cccccc")

    ax.barh(y_pos, res["beta"], xerr=[res["beta"] - res["beta_ci_lo"],
            res["beta_ci_hi"] - res["beta"]], color=colors,
            edgecolor="none", height=0.6, capsize=2, ecolor="#888888",
            alpha=0.85)
    ax.axvline(0, color="black", linewidth=0.8, linestyle="-")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(res["label"], fontsize=9)
    ax.set_xlabel("Standardized coefficient (\u03B2)", fontsize=10)
    ax.set_title(f"{title}\n(N = {n}, R\u00B2 = {r2:.3f})", fontsize=11,
                 fontweight="bold")

    # Add significance stars
    for i, (beta, pval) in enumerate(zip(res["beta"], res["beta_pval"])):
        if pval < 0.001:
            star = "***"
        elif pval < 0.01:
            star = "**"
        elif pval < 0.05:
            star = "*"
        else:
            star = ""
        if star:
            offset = 0.01 if beta >= 0 else -0.01
            ha = "left" if beta >= 0 else "right"
            ax.text(beta + offset, i, star, va="center", ha=ha, fontsize=9,
                    fontweight="bold", color="#333333")

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", alpha=0.3, linestyle="--")


fig, axes = plt.subplots(3, 1, figsize=(10, 18))
fig.subplots_adjust(hspace=0.45, left=0.28, right=0.95, top=0.95, bottom=0.05)

plot_coef(axes[0], res_pooled,
          "Pooled Model: Predictors of National Belonging",
          n_pooled, mod_pooled.rsquared, "#2171b5")

plot_coef(axes[1], res_est,
          "Estonian Respondents: Predictors of National Belonging",
          n_est, mod_est.rsquared, "#238b45")

plot_coef(axes[2], res_rus,
          "Russian Respondents: Predictors of National Belonging",
          n_rus, mod_rus.rsquared, "#cb181d")

fig.savefig("fig_coefficient_plots.png", dpi=200, bbox_inches="tight")
print("Saved: fig_coefficient_plots.png")

# ============================================================
# Figure 2: Side-by-side comparison of shared predictors
#           (Estonian vs Russian)
# ============================================================

shared_vars = [
    "female", "age_30_44", "age_45_59", "age_60plus",
    "T16", "T18", "Q117a", "Q118_1",
    "parents_russia",
    "edu_lang_russian", "edu_lang_both",
    "born_russia", "born_elsewhere",
    "Q71_3",
]

est_shared = res_est[res_est["variable"].isin(shared_vars)].set_index("variable").loc[shared_vars]
rus_shared = res_rus[res_rus["variable"].isin(shared_vars)].set_index("variable").loc[shared_vars]

fig2, ax2 = plt.subplots(figsize=(10, 8))
y_pos = np.arange(len(shared_vars))
bar_h = 0.35

labels_shared = [LABELS.get(v, v) for v in shared_vars][::-1]
est_betas = est_shared["beta"].values[::-1]
rus_betas = rus_shared["beta"].values[::-1]
est_ci_lo = est_shared["beta_ci_lo"].values[::-1]
est_ci_hi = est_shared["beta_ci_hi"].values[::-1]
rus_ci_lo = rus_shared["beta_ci_lo"].values[::-1]
rus_ci_hi = rus_shared["beta_ci_hi"].values[::-1]
est_pvals = est_shared["beta_pval"].values[::-1]
rus_pvals = rus_shared["beta_pval"].values[::-1]

ax2.barh(y_pos + bar_h / 2, est_betas,
         xerr=[est_betas - est_ci_lo, est_ci_hi - est_betas],
         height=bar_h, color="#238b45", alpha=0.8, label="Estonian",
         capsize=2, ecolor="#888888", edgecolor="none")
ax2.barh(y_pos - bar_h / 2, rus_betas,
         xerr=[rus_betas - rus_ci_lo, rus_ci_hi - rus_betas],
         height=bar_h, color="#cb181d", alpha=0.8, label="Russian",
         capsize=2, ecolor="#888888", edgecolor="none")

# Stars
for i, (eb, ep, rb, rp) in enumerate(zip(est_betas, est_pvals,
                                          rus_betas, rus_pvals)):
    for beta, pval, y_off, color in [(eb, ep, bar_h / 2, "#238b45"),
                                      (rb, rp, -bar_h / 2, "#cb181d")]:
        if pval < 0.001:
            star = "***"
        elif pval < 0.01:
            star = "**"
        elif pval < 0.05:
            star = "*"
        else:
            star = ""
        if star:
            offset = 0.01 if beta >= 0 else -0.01
            ha = "left" if beta >= 0 else "right"
            ax2.text(beta + offset, i + y_off, star, va="center", ha=ha,
                     fontsize=8, fontweight="bold", color=color)

ax2.axvline(0, color="black", linewidth=0.8)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(labels_shared, fontsize=9)
ax2.set_xlabel("Standardized coefficient (\u03B2)", fontsize=10)
ax2.set_title("Estonian vs. Russian: Comparison of Shared Predictors\n"
              "(DV: Composite Belonging Score)",
              fontsize=12, fontweight="bold")
ax2.legend(loc="lower right", fontsize=10)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.grid(axis="x", alpha=0.3, linestyle="--")

fig2.savefig("fig_comparison_plot.png", dpi=200, bbox_inches="tight")
print("Saved: fig_comparison_plot.png")

# ============================================================
# Figure 3: R-squared comparison across models
# ============================================================

fig3, ax3 = plt.subplots(figsize=(7, 4))
models = ["Pooled", "Estonian", "Russian"]
r2_vals = [mod_pooled.rsquared, mod_est.rsquared, mod_rus.rsquared]
adj_r2_vals = [mod_pooled.rsquared_adj, mod_est.rsquared_adj, mod_rus.rsquared_adj]
colors3 = ["#2171b5", "#238b45", "#cb181d"]

x = np.arange(len(models))
w = 0.35
bars1 = ax3.bar(x - w / 2, r2_vals, w, color=colors3, alpha=0.85,
                label="R\u00B2", edgecolor="none")
bars2 = ax3.bar(x + w / 2, adj_r2_vals, w, color=colors3, alpha=0.45,
                label="Adj. R\u00B2", edgecolor="none")

for bar, val in zip(bars1, r2_vals):
    ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
             f"{val:.3f}", ha="center", fontsize=10, fontweight="bold")
for bar, val in zip(bars2, adj_r2_vals):
    ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
             f"{val:.3f}", ha="center", fontsize=10)

ax3.set_xticks(x)
ax3.set_xticklabels([f"{m}\n(N={n})" for m, n in
                      zip(models, [n_pooled, n_est, n_rus])], fontsize=10)
ax3.set_ylabel("Variance Explained", fontsize=10)
ax3.set_title("Model Fit Comparison (R\u00B2 and Adjusted R\u00B2)",
              fontsize=12, fontweight="bold")
ax3.set_ylim(0, max(r2_vals) * 1.25)
ax3.legend(fontsize=10)
ax3.spines["top"].set_visible(False)
ax3.spines["right"].set_visible(False)
ax3.grid(axis="y", alpha=0.3, linestyle="--")

fig3.savefig("fig_r_squared.png", dpi=200, bbox_inches="tight")
print("Saved: fig_r_squared.png")

plt.close("all")
print("\nAll figures saved successfully.")
