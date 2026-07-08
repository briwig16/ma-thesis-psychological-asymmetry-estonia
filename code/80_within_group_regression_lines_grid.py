"""
Visualization of the within-group regressions from script 79: one panel per
composite, showing the regression line for Estonians and Russians across
2020 → 2023 on the original Likert metric.

With year as a binary predictor (0/1), the OLS fit reduces to a line segment
between the two cell means per group, with the slope = B1. Shaded bands show
95% confidence intervals on the cell means. Annotation in each panel shows
B1 ± SE and p for each group, plus the Year × Ethnicity interaction p-value
from the corresponding 2 × 2 ANOVA.

Output: viz/fig_within_group_regression_lines.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent

reg = pd.read_csv(ROOT / "code" / "_within_group_year_regression.tsv", sep="\t")
an  = pd.read_csv(ROOT / "code" / "_anova_2x2_composites.tsv", sep="\t")
an  = an.set_index("variable")

# Panel order
COMPOSITES = [
    "Superordinate Identity",
    "SD: Primary Out-group",
    "SD: General Out-group",
    "Comparative Opportunity Assessment",
    "Belief in Inevitable Conflict",
    "Minority Inclusion Support",
]

# Pretty labels for panel titles
PRETTY = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group ⁱ",
    "Comparative Opportunity Assessment": "Comparative Opportunity",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Inclusion Support",
}


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ("⁺" if p < .10 else "ns")


def fmt_p(p):
    if p < .001: return "< .001"
    return f"= {p:.3f}".replace("0.", ".")


# ---- Plot setup -----------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.7,
})

RUS = "#d97706"
EST = "#2563eb"

fig, axes = plt.subplots(2, 3, figsize=(15.0, 9.0), dpi=300)
axes = axes.flatten()

x_pos = {2020: 0, 2023: 1}

for ax, comp in zip(axes, COMPOSITES):
    rE = reg[(reg["variable"] == comp) & (reg["group"] == "Estonian")].iloc[0]
    rR = reg[(reg["variable"] == comp) & (reg["group"] == "Russian")].iloc[0]

    # Cell means: M_2020 = B0; M_2023 = B0 + B1
    M_E_20 = rE["B0_intercept"]; M_E_23 = rE["B0_intercept"] + rE["B1_year2023"]
    M_R_20 = rR["B0_intercept"]; M_R_23 = rR["B0_intercept"] + rR["B1_year2023"]

    # SEs on cell means via the SE of the regression coefficients:
    # M_2020 = B0, M_2023 = B0 + B1 → use residual SE / sqrt(n) per cell.
    # Simpler: read cell SDs and Ns from the ANOVA TSV for proper 95% CIs.
    a_row = an.loc[comp]
    se_E_20 = a_row["Est_2020_SD"] / np.sqrt(a_row["Est_2020_N"])
    se_E_23 = a_row["Est_2023_SD"] / np.sqrt(a_row["Est_2023_N"])
    se_R_20 = a_row["Rus_2020_SD"] / np.sqrt(a_row["Rus_2020_N"])
    se_R_23 = a_row["Rus_2023_SD"] / np.sqrt(a_row["Rus_2023_N"])

    # 95% CI half-widths (≈ 1.96 × SE)
    ci_E_20, ci_E_23 = 1.96 * se_E_20, 1.96 * se_E_23
    ci_R_20, ci_R_23 = 1.96 * se_R_20, 1.96 * se_R_23

    # Plot Estonian
    ax.errorbar([0, 1], [M_E_20, M_E_23],
                yerr=[[ci_E_20, ci_E_23], [ci_E_20, ci_E_23]],
                color=EST, marker="o", markersize=9, markerfacecolor=EST,
                markeredgecolor="white", markeredgewidth=1.0,
                linewidth=2.0, capsize=4, capthick=1.0, zorder=3,
                label="Estonian")

    # Plot Russian
    ax.errorbar([0, 1], [M_R_20, M_R_23],
                yerr=[[ci_R_20, ci_R_23], [ci_R_20, ci_R_23]],
                color=RUS, marker="s", markersize=9, markerfacecolor=RUS,
                markeredgecolor="white", markeredgewidth=1.0,
                linewidth=2.0, capsize=4, capthick=1.0, zorder=3,
                label="Russian")

    # B1 annotation per group
    pE_str = fmt_p(rE["p"]); sE = stars(rE["p"])
    pR_str = fmt_p(rR["p"]); sR = stars(rR["p"])
    ax.text(0.02, 0.97,
            f"Est. B = {rE['B1_year2023']:+.3f} (SE {rE['SE']:.3f}, p {pE_str}) {sE}\n"
            f"Rus. B = {rR['B1_year2023']:+.3f} (SE {rR['SE']:.3f}, p {pR_str}) {sR}",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=8.0, color="#222", family="monospace",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor="#aaa", linewidth=0.5, alpha=0.93))

    # Interaction p-value top-right
    p_ix = a_row["p_interaction"]; F_ix = a_row["F_interaction"]; eta_ix = a_row["eta2p_interaction"]
    ax.text(0.98, 0.97,
            f"Year × Ethn.\nF = {F_ix:.2f}, p {fmt_p(p_ix)} {stars(p_ix)}\nη²p = .{int(round(eta_ix*1000)):03d}",
            transform=ax.transAxes, ha="right", va="top",
            fontsize=8.0, color="#333", family="monospace",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff8e7",
                      edgecolor="#e0c97f", linewidth=0.5, alpha=0.95))

    ax.set_title(PRETTY[comp], fontsize=11, fontweight="bold", loc="left", pad=8)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["2020", "2023"], fontsize=10)
    ax.set_xlim(-0.25, 1.25)
    ax.set_xlabel("Year", fontsize=9, color="#444")
    ax.set_ylabel("Composite mean", fontsize=9, color="#444")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.4, color="#ddd", zorder=0)

# Global title block
fig.text(0.04, 0.965,
         "Within-Group OLS Regressions — Composite Score on Year, by Ethnic Group",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Each panel shows the regression line fit within each ethnic group (Estonian = blue circles; Russian = orange squares).",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.918,
         "Line slope = B₁ (mean shift 2020 → 2023 on the original Likert metric). Error bars = 95% CI on the cell mean. Year × Ethnicity interaction p reported per panel.",
         fontsize=9, color="#444", ha="left")

# Single shared legend
handles = [
    plt.Line2D([], [], marker="o", color=EST, markerfacecolor=EST,
               markeredgecolor="white", markersize=9, linewidth=2.0,
               label="Estonian respondents"),
    plt.Line2D([], [], marker="s", color=RUS, markerfacecolor=RUS,
               markeredgecolor="white", markersize=9, linewidth=2.0,
               label="Russian respondents"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.97, 0.935),
           frameon=False, fontsize=9, ncol=2, handlelength=2.4,
           columnspacing=2.0)

# Footer
fig.text(0.04, 0.015,
         "ⁱ SD: General Out-group uses different items in 2020 (3 items) vs 2023 (6 items); within-group shifts and interaction partially confound year with item-set change.",
         fontsize=7.0, color="#555", ha="left")
fig.text(0.04, 0.003,
         "Significance: *** p < .001, ** p < .01, * p < .05, ⁺ p < .10. Slopes computed via OLS regression of composite on a binary year predictor (0 = 2020, 1 = 2023).",
         fontsize=7.0, color="#555", ha="left")

plt.subplots_adjust(left=0.06, right=0.985, top=0.88, bottom=0.07,
                    wspace=0.22, hspace=0.36)

out = ROOT / "viz" / "fig_within_group_regression_lines.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
