"""
Forest plot comparing unadjusted (script 79) and demographic-controlled
(script 81) within-group B₁ estimates.

Each row pairs an unadjusted estimate (open dot, faded line) with the
demographic-controlled estimate (filled dot, solid CI bracket), connected by
a thin line so the shift is directly visible. Color-coded by group:
Estonian = blue, Russian = orange. Reference line at 0.

Reading the plot:
  - When the open and filled dots overlap, controls did not change the
    estimate (Bilali's "covariates don't matter" finding).
  - When they diverge, controls explained part of the year effect (or
    revealed an effect previously suppressed by demographic composition).

Output: viz/fig_controlled_regression_forest.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

ctrl = pd.read_csv(ROOT / "code" / "_within_group_year_regression_controlled.tsv", sep="\t")

# Build a CI for the unadjusted estimate using the unadjusted SE (~95% via ±1.96*SE).
ctrl["CI_low_unadj"]  = ctrl["B1_unadj"] - 1.96 * ctrl["SE_unadj"]
ctrl["CI_high_unadj"] = ctrl["B1_unadj"] + 1.96 * ctrl["SE_unadj"]


# Plot order: composite, then Estonian above Russian within each composite
COMPOSITES = [
    "Superordinate Identity",
    "SD: Primary Out-group",
    "SD: General Out-group",
    "Comparative Opportunity Assessment",
    "Belief in Inevitable Conflict",
    "Minority Inclusion Support",
]

# Pretty labels for y-axis
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
    if p < .001: return "p < .001"
    return f"p = {p:.3f}".replace("0.", ".")


# ---- Plot setup -----------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.7,
})

RUS = "#d97706"
EST = "#2563eb"

fig, ax = plt.subplots(figsize=(15.0, 9.0), dpi=300)

# Vertical layout: top → bottom, with two rows per composite (Est above Rus)
# and a small gap between composites.
y_positions = {}
y = 13.0
row_gap = 1.0
composite_gap = 0.6
for comp in COMPOSITES:
    y_positions[(comp, "Estonian")] = y
    y -= row_gap
    y_positions[(comp, "Russian")] = y
    y -= row_gap + composite_gap

# Light banding behind each composite
y_min_band, y_max_band = min(y_positions.values()) - 0.5, max(y_positions.values()) + 0.6
for i, comp in enumerate(COMPOSITES):
    y_top = y_positions[(comp, "Estonian")] + 0.5
    y_bot = y_positions[(comp, "Russian")]  - 0.5
    if i % 2 == 0:
        ax.axhspan(y_bot, y_top, facecolor="#f7f7f7", zorder=0)

# Plot every row
for comp in COMPOSITES:
    for group in ("Estonian", "Russian"):
        r = ctrl[(ctrl["variable"] == comp) & (ctrl["group"] == group)].iloc[0]
        y = y_positions[(comp, group)]
        color = EST if group == "Estonian" else RUS

        # Unadjusted: faded CI bracket + open dot
        ax.plot([r["CI_low_unadj"], r["CI_high_unadj"]], [y + 0.15, y + 0.15],
                color=color, linewidth=1.4, alpha=0.35,
                solid_capstyle="round", zorder=2)
        for xx in (r["CI_low_unadj"], r["CI_high_unadj"]):
            ax.plot([xx, xx], [y + 0.07, y + 0.23],
                    color=color, linewidth=1.0, alpha=0.35, zorder=2)
        ax.scatter([r["B1_unadj"]], [y + 0.15], s=130, facecolor="white",
                   edgecolor=color, linewidth=1.8, zorder=3, alpha=0.85)

        # Connector line between unadjusted and adjusted estimates
        ax.plot([r["B1_unadj"], r["B1_adj"]], [y + 0.15, y - 0.15],
                color=color, linewidth=0.8, alpha=0.5,
                linestyle=(0, (2, 2)), zorder=2)

        # Adjusted: solid CI bracket + filled dot
        ax.plot([r["CI_low_adj"], r["CI_high_adj"]], [y - 0.15, y - 0.15],
                color=color, linewidth=2.2, alpha=0.9,
                solid_capstyle="round", zorder=2)
        for xx in (r["CI_low_adj"], r["CI_high_adj"]):
            ax.plot([xx, xx], [y - 0.23, y - 0.07],
                    color=color, linewidth=1.6, alpha=0.95, zorder=2)
        ax.scatter([r["B1_adj"]], [y - 0.15], s=155, color=color,
                   edgecolor="white", linewidth=1.0, zorder=3)

        # Annotation to the right
        delta = r["delta_B1"]
        ann = (f"{group:<8}  unadj. B = {r['B1_unadj']:+.3f} {stars(r['p_unadj'])}    "
               f"adj. B = {r['B1_adj']:+.3f} {stars(r['p_adj'])}    "
               f"Δ = {delta:+.3f}")
        ax.text(max(r["CI_high_unadj"], r["CI_high_adj"]) + 0.025, y,
                ann, ha="left", va="center", fontsize=8.2,
                color="#222", family="monospace")

# Reference line at 0
ax.axvline(0, color="#666", linewidth=1.0, linestyle="-", zorder=1)

# Y-axis labels: composite name at the pair midpoint
yticks, yticklabels = [], []
for comp in COMPOSITES:
    y_E = y_positions[(comp, "Estonian")]
    y_R = y_positions[(comp, "Russian")]
    yticks.append((y_E + y_R) / 2)
    yticklabels.append(PRETTY[comp])
ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels, fontsize=10, fontweight="bold")
ax.set_ylim(y_min_band, y_max_band)
ax.invert_yaxis()

# X-axis
ax.set_xlim(-0.85, 1.55)
ax.set_xticks(np.arange(-0.8, 0.81, 0.2))
ax.set_xlabel("Year coefficient B₁  (2023 − 2020, original Likert metric)",
              fontsize=10, color="#444", labelpad=8)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#666")
ax.tick_params(axis="x", length=2.5, color="#666", labelsize=9)
ax.tick_params(axis="y", length=0)

# Vertical grid
for x in np.arange(-0.8, 0.81, 0.2):
    ax.axvline(x, color="#eee", linewidth=0.4, zorder=0)

# Title block
fig.text(0.04, 0.965,
         "Demographic Controls on the Within-Group Year Effect — Forest Plot",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Open dot + faded bracket = unadjusted B₁ (script 79). Filled dot + solid bracket = demographic-controlled B₁ (age + gender + education + income).",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.918,
         "Dashed line connects the two estimates per row, showing how much the year effect changes once demographic composition is partialed out.",
         fontsize=9, color="#444", ha="left")

# Legend
legend_handles = [
    mlines.Line2D([], [], marker="o", color=EST, markerfacecolor="white",
                  markeredgecolor=EST, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Estonian — unadjusted"),
    mlines.Line2D([], [], marker="o", color=EST, markerfacecolor=EST,
                  markeredgecolor="white", markersize=10,
                  linestyle="None", label="Estonian — controlled"),
    mlines.Line2D([], [], marker="o", color=RUS, markerfacecolor="white",
                  markeredgecolor=RUS, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Russian — unadjusted"),
    mlines.Line2D([], [], marker="o", color=RUS, markerfacecolor=RUS,
                  markeredgecolor="white", markersize=10,
                  linestyle="None", label="Russian — controlled"),
]
fig.legend(handles=legend_handles, loc="upper right",
           bbox_to_anchor=(0.97, 0.94),
           frameon=False, fontsize=8.5, ncol=2,
           handlelength=1.5, columnspacing=1.5)

# Footer
fig.text(0.04, 0.022,
         "Controls: age (years), gender (1 = female), education (T18 / T22), income (T17 / T19, 5-level descriptive). Listwise deletion across composite, year, and all four covariates. HC3 robust SEs.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.008,
         "ⁱ SD: General Out-group uses different items in 2020 (3) vs 2023 (6); year effect partially confounds with item-set change. Significance: *** p < .001, ** p < .01, * p < .05, ⁺ p < .10, ns = ns.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.18, right=0.985, top=0.88, bottom=0.075)

out = ROOT / "viz" / "fig_controlled_regression_forest.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
