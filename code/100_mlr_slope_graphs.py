"""
Slope-graph visualization of the additive MLR results from script 99.

Each panel = one outcome × group × wave cell. Within each panel, two
slope lines show:
  - Contact (blue): standardized predicted outcome at low (−1 SD) vs
    high (+1 SD) contact, holding language at mean.
  - Language (green): standardized predicted outcome at low (−1 SD) vs
    high (+1 SD) language, holding contact at mean.

The two slopes are the standardized β coefficients from the additive MLR
(Table 1 of MLR_Contact_Language_APA.docx). A steeper line = stronger
standardized effect; lines slope upward for positive β, downward for
negative β. Significance stars on each line's endpoint.

Layout: 8 rows × 4 columns = 32 panels, one per outcome × cell.

Output: viz/fig_mlr_slope_graphs.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

df = pd.read_csv(ROOT / "code" / "_mlr_contact_language_additive.tsv", sep="\t")

OUTCOMES = [
    "Superordinate Identity",
    "SD: Primary Out-group",
    "SD: General Out-group",
    "Comparative Opportunity Assessment",
    "Belief in Inevitable Conflict",
    "Minority Inclusion Support",
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
    "Group ID Patterns":                  "Group ID Patterns",
    "Territorial Attachment":             "Territorial Attachment",
}

CELLS = [("Estonian", 2020), ("Estonian", 2023), ("Russian", 2020), ("Russian", 2023)]


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.5,
})

CONTACT_COLOR  = "#2563eb"   # blue
LANGUAGE_COLOR = "#15803d"   # green

# Determine y-axis range across all panels
all_betas = pd.concat([df["beta1"], df["beta2"]]).dropna()
y_max = max(abs(all_betas.min()), abs(all_betas.max())) * 1.25
y_lim = (-y_max, y_max)

fig, axes = plt.subplots(8, 4, figsize=(15.0, 22.0), dpi=300,
                          sharex=True, sharey=True)

for i, outcome in enumerate(OUTCOMES):
    for j, (group, year) in enumerate(CELLS):
        ax = axes[i, j]
        match = df[(df["variable"] == outcome) & (df["group"] == group) & (df["year"] == year)]
        if match.empty:
            ax.set_visible(False)
            continue
        r = match.iloc[0]
        beta1 = r["beta1"]; beta2 = r["beta2"]
        p1 = r["p1"]; p2 = r["p2"]

        # Contact slope: standardized predictor x = -1 to +1, y = β × x
        ax.plot([-1, 1], [-beta1, beta1], color=CONTACT_COLOR, linewidth=2.2,
                solid_capstyle="round", marker="o", markersize=6,
                markerfacecolor=CONTACT_COLOR, markeredgecolor="white",
                markeredgewidth=0.8, zorder=3)
        # Language slope
        ax.plot([-1, 1], [-beta2, beta2], color=LANGUAGE_COLOR, linewidth=2.2,
                solid_capstyle="round", marker="s", markersize=6,
                markerfacecolor=LANGUAGE_COLOR, markeredgecolor="white",
                markeredgewidth=0.8, zorder=3)

        # Reference line at y=0
        ax.axhline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)
        ax.axvline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)

        # Endpoint annotations
        ax.text(1.05, beta1,
                f"β={beta1:+.2f}{stars(p1)}",
                color=CONTACT_COLOR, fontsize=7, va="center", ha="left",
                family="monospace", fontweight="bold")
        ax.text(1.05, beta2,
                f"β={beta2:+.2f}{stars(p2)}",
                color=LANGUAGE_COLOR, fontsize=7, va="center", ha="left",
                family="monospace", fontweight="bold")

        ax.set_xlim(-1.4, 2.0)
        ax.set_ylim(y_lim)
        ax.set_xticks([-1, 0, 1])
        ax.set_xticklabels(["−1 SD", "0", "+1 SD"], fontsize=7)
        ax.tick_params(axis="both", labelsize=7, color="#888")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.grid(True, axis="y", linestyle=":", linewidth=0.3, color="#eee", zorder=0)

        # Title
        if i == 0:
            ax.set_title(f"{group} {year}", fontsize=10, fontweight="bold",
                         pad=6, color="#333")

# Outcome row labels on the leftmost column
for i, outcome in enumerate(OUTCOMES):
    axes[i, 0].set_ylabel(PRETTY[outcome], fontsize=9, fontweight="bold",
                          color="#222", labelpad=8)

# Bottom x-label
for j in range(4):
    axes[7, j].set_xlabel("Standardized predictor (SD)", fontsize=8, color="#555")

# Global title
fig.text(0.04, 0.985,
         "Multiple Linear Regression — Standardized Slopes of Contact and Language by Cell",
         fontsize=15, fontweight="bold", ha="left")
fig.text(0.04, 0.973,
         "Each panel shows two slope lines: contact (blue, circle) and language (green, square). Slopes = standardized regression coefficients (β) from the additive MLR (Table 1).",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.963,
         "Lines plot from −1 SD to +1 SD of the standardized predictor. Steeper line = stronger standardized effect. Upward slope = positive association; downward = negative.",
         fontsize=9, color="#444", ha="left")

# Legend
handles = [
    mlines.Line2D([], [], marker="o", color=CONTACT_COLOR, markerfacecolor=CONTACT_COLOR,
                  markeredgecolor="white", markersize=8, linewidth=2.2,
                  label="Out-group Contact"),
    mlines.Line2D([], [], marker="s", color=LANGUAGE_COLOR, markerfacecolor=LANGUAGE_COLOR,
                  markeredgecolor="white", markersize=8, linewidth=2.2,
                  label="Out-group Language Ability"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.972),
           frameon=False, fontsize=9, ncol=1,
           handlelength=2.0, columnspacing=1.5)

fig.text(0.04, 0.015,
         "Contact composites inverted so higher = more frequent contact; out-group language coded so higher = more proficient. Both mean-centered within each cell.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.005,
         "Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10. Standardized coefficients (β) computed as B × SD(predictor)/SD(outcome).",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.13, right=0.985, top=0.95, bottom=0.025,
                    wspace=0.15, hspace=0.30)

out = ROOT / "viz" / "fig_mlr_slope_graphs.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
