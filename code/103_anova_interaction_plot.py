"""
Interaction plot for ANOVA Table 1 — visualizes the 2 × 2 factorial ANOVA
results for all 10 outcome variables.

Each panel = one outcome. Within each panel:
  - X-axis: Year (2020, 2023)
  - Y-axis: cell mean on the outcome's original Likert scale
  - Two lines: Estonian (blue circles), Russian (orange squares)
  - Error bars: 95% CI on each cell mean

Interpretive guide for each panel:
  - Two parallel sloping lines → year main effect, no interaction
  - Lines slope in opposite directions → asymmetric divergence (interaction)
  - Lines slope same direction at different rates → interaction
  - Both lines flat → no year effect

Annotations show the Year × Ethnicity F-statistic and partial η² to summarize
the interaction directly on each panel.

Output: viz/fig_anova_interaction_plot.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

df = pd.read_csv(ROOT / "code" / "_anova_2x2_all_variables.tsv", sep="\t")

# Outcome order for the 10-panel layout
OUTCOMES = [
    "Superordinate Identity",
    "SD: Primary Out-group",
    "SD: General Out-group",
    "Comparative Opportunity Assessment",
    "Belief in Inevitable Conflict",
    "Minority Inclusion Support",
    "Contact: Estonian Speakers",
    "Contact: Russian Speakers",
    "Group ID Patterns",
    "Territorial Attachment",
]

PRETTY = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group",
    "Comparative Opportunity Assessment": "Comparative Opportunity",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Inclusion Support",
    "Contact: Estonian Speakers":         "Contact: Estonian Speakers",
    "Contact: Russian Speakers":          "Contact: Russian Speakers",
    "Group ID Patterns":                  "Group ID Patterns",
    "Territorial Attachment":             "Territorial Attachment",
}

# Original Likert scale per outcome (for y-axis range)
SCALE_MAX = {
    "Superordinate Identity":             4,
    "SD: Primary Out-group":              5,
    "SD: General Out-group":              5,
    "Comparative Opportunity Assessment": 5,
    "Belief in Inevitable Conflict":      4,
    "Minority Inclusion Support":         4,
    "Contact: Estonian Speakers":         5,
    "Contact: Russian Speakers":          5,
    "Group ID Patterns":                  5,
    "Territorial Attachment":             4,
}


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


def fmt_p(p):
    if p < .001: return "p < .001"
    return f"p = {p:.3f}".replace("0.", ".")


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST_COLOR = "#2563eb"
RUS_COLOR = "#d97706"

fig, axes = plt.subplots(2, 5, figsize=(20.0, 10.0), dpi=300)
axes = axes.flatten()

for idx, outcome in enumerate(OUTCOMES):
    ax = axes[idx]
    row = df[df["variable"] == outcome]
    if row.empty:
        ax.set_visible(False); continue
    r = row.iloc[0]

    # Cell means and 95% CIs
    M_E_20, SD_E_20, N_E_20 = r["Est_2020_M"], r["Est_2020_SD"], r["Est_2020_N"]
    M_E_23, SD_E_23, N_E_23 = r["Est_2023_M"], r["Est_2023_SD"], r["Est_2023_N"]
    M_R_20, SD_R_20, N_R_20 = r["Rus_2020_M"], r["Rus_2020_SD"], r["Rus_2020_N"]
    M_R_23, SD_R_23, N_R_23 = r["Rus_2023_M"], r["Rus_2023_SD"], r["Rus_2023_N"]
    se_E_20 = SD_E_20 / np.sqrt(N_E_20); se_E_23 = SD_E_23 / np.sqrt(N_E_23)
    se_R_20 = SD_R_20 / np.sqrt(N_R_20); se_R_23 = SD_R_23 / np.sqrt(N_R_23)
    ci_E_20 = 1.96 * se_E_20; ci_E_23 = 1.96 * se_E_23
    ci_R_20 = 1.96 * se_R_20; ci_R_23 = 1.96 * se_R_23

    # Estonian line
    ax.errorbar([0, 1], [M_E_20, M_E_23],
                yerr=[[ci_E_20, ci_E_23], [ci_E_20, ci_E_23]],
                color=EST_COLOR, marker="o", markersize=11, markerfacecolor=EST_COLOR,
                markeredgecolor="white", markeredgewidth=1.0,
                linewidth=2.4, capsize=5, capthick=1.2, zorder=3)
    # Russian line
    ax.errorbar([0, 1], [M_R_20, M_R_23],
                yerr=[[ci_R_20, ci_R_23], [ci_R_20, ci_R_23]],
                color=RUS_COLOR, marker="s", markersize=11, markerfacecolor=RUS_COLOR,
                markeredgecolor="white", markeredgewidth=1.0,
                linewidth=2.4, capsize=5, capthick=1.2, zorder=3)

    # Compact interaction annotation in lower-right corner
    F_int = r["F_interaction"]; p_int = r["p_interaction"]; eta = r["eta2p_interaction"]
    ax.text(0.98, 0.04,
            f"Y×E: F={F_int:.1f}{stars(p_int)}  η²ₚ=.{int(round(eta*1000)):03d}",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7.5, color="#5a4a16", family="monospace", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="#fff8e7",
                      edgecolor="#e0c97f", linewidth=0.4, alpha=0.92))

    # Format
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["2020", "2023"], fontsize=10)
    ax.set_xlim(-0.20, 1.20)
    smax = SCALE_MAX[outcome]
    # Y-range: tight around the actual cell means, with padding
    all_means = [M_E_20, M_E_23, M_R_20, M_R_23]
    all_cis = [ci_E_20, ci_E_23, ci_R_20, ci_R_23]
    y_lo = min(all_means) - max(all_cis) - 0.12
    y_hi = max(all_means) + max(all_cis) + 0.12
    y_lo = max(0.5, y_lo); y_hi = min(smax + 0.5, y_hi)
    # Make sure the range is at least 0.6 wide so the lines are visible
    if y_hi - y_lo < 0.6:
        center = (y_hi + y_lo) / 2
        y_lo = center - 0.3; y_hi = center + 0.3
    ax.set_ylim(y_lo, y_hi)
    ax.set_xlabel("Year", fontsize=9, color="#444")
    ax.set_ylabel(f"Mean (1–{smax})", fontsize=9, color="#444")
    ax.set_title(PRETTY[outcome], fontsize=11, fontweight="bold",
                 loc="left", pad=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")
    ax.grid(True, axis="y", linestyle="--", linewidth=0.4, color="#ddd", zorder=0)

# Global title
fig.text(0.04, 0.965,
         "ANOVA Interaction Plot — Cell Means by Year × Ethnicity, All 10 Outcomes",
         fontsize=15, fontweight="bold", ha="left")
fig.text(0.04, 0.945,
         "Each panel shows the 2020 and 2023 cell means for Estonian (blue circles) and Russian (orange squares) respondents. Error bars = 95% CI on the cell mean.",
         fontsize=10, color="#444", ha="left")
fig.text(0.04, 0.928,
         "Diverging lines (different slopes) indicate a Year × Ethnicity interaction — asymmetric divergence between groups. Parallel lines = uniform shift or stability.",
         fontsize=10, color="#444", ha="left")

# Legend
handles = [
    mlines.Line2D([], [], marker="o", color=EST_COLOR, markerfacecolor=EST_COLOR,
                  markeredgecolor="white", markersize=11, linewidth=2.4,
                  label="Estonian respondents"),
    mlines.Line2D([], [], marker="s", color=RUS_COLOR, markerfacecolor=RUS_COLOR,
                  markeredgecolor="white", markersize=11, linewidth=2.4,
                  label="Russian respondents"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.945),
           frameon=False, fontsize=10, ncol=2,
           handlelength=2.4, columnspacing=2.0)

fig.text(0.04, 0.015,
         "Composites: cell means on the original Likert scale (1–4 or 1–5). After display-direction inversion where applicable, higher = more of the construct. Contact composites inverted: higher = more frequent contact.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.003,
         "Year × Ethnicity F is the diff-in-diff test of whether the between-group gap changed between waves. η²ₚ benchmarks: ≈.01 small, ≈.06 medium, ≈.14 large.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.04, right=0.985, top=0.89, bottom=0.06,
                    wspace=0.32, hspace=0.45)

out = ROOT / "viz" / "fig_anova_interaction_plot.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
