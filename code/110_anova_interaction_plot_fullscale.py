"""
ANOVA interaction plot — FULL SCALE version.

Identical to script 103 (fig_anova_interaction_plot.jpg) but with each
panel's y-axis spanning the full Likert range of the outcome (1 to scale_max)
rather than zooming in around the cell means. This makes the absolute size
of between-group gaps and within-group shifts visually accurate — a 0.1
point shift on a 1–5 scale will look small (which it is) rather than being
exaggerated by an auto-tight y-axis.

Output: viz/fig_anova_interaction_plot_fullscale.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

df = pd.read_csv(ROOT / "code" / "_anova_2x2_all_variables.tsv", sep="\t")

OUTCOMES = [
    "Contact: Estonian Speakers",
    "Contact: Russian Speakers",
    "SD: Primary Out-group",
    "SD: General Out-group",
    "Minority Inclusion Support",
    "Belief in Inevitable Conflict",
    "Comparative Opportunity Assessment",
    "Superordinate Identity",
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
    "font.size": 8,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.5,
})

EST_COLOR = "#2563eb"
RUS_COLOR = "#d97706"

# A4 portrait: 8.27" × 11.69" — 5 rows × 2 cols for 10 outcomes
fig, axes = plt.subplots(5, 2, figsize=(8.27, 11.69), dpi=300)
axes = axes.flatten()

for idx, outcome in enumerate(OUTCOMES):
    ax = axes[idx]
    row = df[df["variable"] == outcome]
    if row.empty:
        ax.set_visible(False); continue
    r = row.iloc[0]

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
                color=EST_COLOR, marker="o", markersize=6, markerfacecolor=EST_COLOR,
                markeredgecolor="white", markeredgewidth=0.7,
                linewidth=1.4, capsize=3, capthick=0.8, zorder=3)
    # Russian line
    ax.errorbar([0, 1], [M_R_20, M_R_23],
                yerr=[[ci_R_20, ci_R_23], [ci_R_20, ci_R_23]],
                color=RUS_COLOR, marker="s", markersize=6, markerfacecolor=RUS_COLOR,
                markeredgecolor="white", markeredgewidth=0.7,
                linewidth=1.4, capsize=3, capthick=0.8, zorder=3)

    # Compact interaction annotation in lower-right
    F_int = r["F_interaction"]; p_int = r["p_interaction"]; eta = r["eta2p_interaction"]
    ax.text(0.97, 0.04,
            f"Y×E: F={F_int:.1f}{stars(p_int)}  η²ₚ=.{int(round(eta*1000)):03d}",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=6.2, color="#5a4a16", family="monospace", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#fff8e7",
                      edgecolor="#e0c97f", linewidth=0.35, alpha=0.92))

    # Format — FULL SCALE Y-AXIS (this is the change)
    smax = SCALE_MAX[outcome]
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["2020", "2023"], fontsize=7.5)
    ax.set_xlim(-0.20, 1.20)

    # Full Likert range, with a small padding so error bars at extremes don't get cut off
    y_lo = 1.0 - 0.05
    y_hi = smax + 0.05
    ax.set_ylim(y_lo, y_hi)
    ax.set_yticks(list(range(1, smax + 1)))   # integer tick marks at each Likert level
    ax.set_yticks(np.arange(1, smax + 0.5, 0.5), minor=True)
    ax.grid(True, axis="y", which="major", linestyle="-",
            linewidth=0.4, color="#ddd", zorder=0)
    ax.grid(True, axis="y", which="minor", linestyle=":",
            linewidth=0.25, color="#eee", zorder=0)

    ax.set_xlabel("Year", fontsize=7, color="#444", labelpad=2)
    ax.set_ylabel(f"Mean (1–{smax} scale)", fontsize=7, color="#444", labelpad=2)
    ax.set_title(PRETTY[outcome], fontsize=8.5, fontweight="bold",
                 loc="left", pad=3)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="both", labelsize=6.5, color="#888",
                   length=2.5, width=0.4, pad=1.5)

# Global title
fig.text(0.04, 0.978,
         "Figure 1 - ANOVA Interaction Plot (Full-Scale Y-axis)",
         fontsize=11.5, fontweight="bold", ha="left")
fig.text(0.04, 0.965,
         "Cell Means by Year × Ethnicity",
         fontsize=9, fontweight="bold", color="#333", ha="left")
fig.text(0.04, 0.953,
         "Each panel shows 2020 and 2023 cell means for Estonian (blue circles) and Russian (orange squares) respondents.",
         fontsize=6.8, color="#444", ha="left")
fig.text(0.04, 0.943,
         "Error bars = 95% CI on the cell mean. Y-axis spans the full Likert range (1 to scale_max).",
         fontsize=6.8, color="#444", ha="left")

handles = [
    mlines.Line2D([], [], marker="o", color=EST_COLOR, markerfacecolor=EST_COLOR,
                  markeredgecolor="white", markersize=6, linewidth=1.4,
                  label="Estonian respondents"),
    mlines.Line2D([], [], marker="s", color=RUS_COLOR, markerfacecolor=RUS_COLOR,
                  markeredgecolor="white", markersize=6, linewidth=1.4,
                  label="Russian respondents"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.975),
           frameon=False, fontsize=7.5, ncol=1,
           handlelength=1.8, labelspacing=0.3, borderaxespad=0.2)

fig.text(0.04, 0.020,
         "Cell means on the original Likert scale. After display-direction inversion where applicable, higher = more of the construct.",
         fontsize=6, color="#555", ha="left")
fig.text(0.04, 0.010,
         "Contact composites inverted so higher = more frequent contact. Year × Ethnicity F is the diff-in-diff test. η²ₚ: .01 small, .06 medium, .14 large.",
         fontsize=6, color="#555", ha="left")

plt.subplots_adjust(left=0.085, right=0.98, top=0.925, bottom=0.045,
                    wspace=0.25, hspace=0.50)

out = ROOT / "viz" / "fig_anova_interaction_plot_fullscale.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
