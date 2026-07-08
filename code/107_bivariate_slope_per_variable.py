"""
Slope visualization for the bivariate contact regressions, grouped by
variable rather than by cell.

Each panel = one outcome. Within each panel, four slope lines show the
bivariate contact–outcome slope for each group × wave cell, plotted in
standardized (β) units so they're directly comparable.

Layout: 2 rows × 4 columns = 8 panels, one per outcome.

Line styling:
  Estonian 2020 — blue dashed
  Estonian 2023 — blue solid
  Russian  2020 — orange dashed
  Russian  2023 — orange solid

Each line's slope equals the bivariate β from script 97/106. A steeper line
= stronger standardized association between contact and that outcome in
that cell. Lines fanning out from a common origin make cross-cell
comparisons visually obvious within each panel.

Output: viz/fig_bivariate_slope_per_variable.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

df = pd.read_csv(ROOT / "code" / "_bivariate_contact_per_cell.tsv", sep="\t")

OUTCOMES = [
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
    "Group ID Patterns":                  "Group ID Patterns",
    "Territorial Attachment":             "Territorial Attachment",
}


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

EST_COLOR = "#2563eb"
RUS_COLOR = "#d97706"

# Global y-axis range
all_betas = df["beta"].abs().max() * 1.25
y_lim = (-all_betas, all_betas)

# A4 portrait: 8.27" × 11.69" — 4 rows × 2 cols for 8 outcomes
fig, axes = plt.subplots(4, 2, figsize=(8.27, 11.69), dpi=300,
                          sharex=True, sharey=True)
axes = axes.flatten()

# Cells in plot order with their line styling
CELLS = [
    ("Estonian", 2020, EST_COLOR, (0, (5, 3)), "o", "white"),    # blue dashed, open circle
    ("Estonian", 2023, EST_COLOR, "-",         "o", EST_COLOR),  # blue solid, filled circle
    ("Russian",  2020, RUS_COLOR, (0, (5, 3)), "s", "white"),    # orange dashed, open square
    ("Russian",  2023, RUS_COLOR, "-",         "s", RUS_COLOR),  # orange solid, filled square
]

for idx, outcome in enumerate(OUTCOMES):
    ax = axes[idx]
    sub = df[df["variable"] == outcome]
    if sub.empty:
        ax.set_visible(False); continue

    # Plot each cell's slope line
    contact_range = np.array([-1.0, 1.0])  # ±1 SD on standardized x
    annotation_lines = []
    for (group, year, color, linestyle, marker, mfc) in CELLS:
        match = sub[(sub["group"] == group) & (sub["year"] == year)]
        if match.empty: continue
        r = match.iloc[0]
        beta = r["beta"]
        y_vals = beta * contact_range   # y = β × x (slope through origin)

        ax.plot(contact_range, y_vals,
                color=color, linestyle=linestyle, linewidth=1.8,
                solid_capstyle="round", zorder=3,
                label=f"{group} {year}")
        # Endpoint marker
        ax.scatter([1.0], [beta], s=42, color=mfc if mfc != "white" else "white",
                   marker=marker, edgecolor=color, linewidth=1.3, zorder=4)
        annotation_lines.append((group, year, beta, r["p"], color))

    # Reference lines
    ax.axhline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)
    ax.axvline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)

    # Annotation block (small, top-left)
    ann_text = "\n".join([
        f"{grp[0]}{yr % 100:02d}: β={b:+.2f}{stars(p)}"
        for grp, yr, b, p, _ in annotation_lines
    ])
    ax.text(0.02, 0.98, ann_text, transform=ax.transAxes,
            ha="left", va="top", fontsize=6.8, family="monospace",
            color="#222",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                      edgecolor="#aaa", linewidth=0.4, alpha=0.93))

    ax.set_title(PRETTY[outcome], fontsize=9, fontweight="bold",
                 loc="left", pad=4)
    ax.set_xticks([-1, 0, 1])
    ax.set_xticklabels(["−1 SD", "0", "+1 SD"], fontsize=7)
    ax.set_xlim(-1.2, 1.4)
    ax.set_ylim(y_lim)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="both", labelsize=7, color="#888")
    ax.grid(True, axis="y", linestyle=":", linewidth=0.3, color="#eee", zorder=0)

# Axis labels: bottom row of 4×2 grid = indices 6, 7; left column = 0, 2, 4, 6
for col in range(2):
    axes[3 * 2 + col].set_xlabel("Standardized contact (SD)",
                                   fontsize=8, color="#444")
for row in range(4):
    axes[row * 2].set_ylabel("Standardized outcome change",
                              fontsize=8, color="#444")

# Title block
fig.text(0.045, 0.980,
         "Figure 2 - Bivariate Contact Slopes by Outcome",
         fontsize=12, fontweight="bold", ha="left")
fig.text(0.045, 0.966,
         "Standardized β per Group × Year Cell",
         fontsize=9.5, fontweight="bold", color="#333", ha="left")
fig.text(0.045, 0.953,
         "Each panel: four slope lines, one per group × year cell.",
         fontsize=7.5, color="#444", ha="left")
fig.text(0.045, 0.942,
         "Slope = β (standardized regression coefficient from script 97).",
         fontsize=7.5, color="#444", ha="left")

# Legend
handles = [
    mlines.Line2D([], [], color=EST_COLOR, linewidth=1.8,
                  linestyle=(0, (5, 3)), marker="o", markerfacecolor="white",
                  markeredgecolor=EST_COLOR, markeredgewidth=1.3, markersize=6,
                  label="Estonian 2020"),
    mlines.Line2D([], [], color=EST_COLOR, linewidth=1.8,
                  linestyle="-", marker="o", markerfacecolor=EST_COLOR,
                  markeredgecolor=EST_COLOR, markersize=6,
                  label="Estonian 2023"),
    mlines.Line2D([], [], color=RUS_COLOR, linewidth=1.8,
                  linestyle=(0, (5, 3)), marker="s", markerfacecolor="white",
                  markeredgecolor=RUS_COLOR, markeredgewidth=1.3, markersize=6,
                  label="Russian 2020"),
    mlines.Line2D([], [], color=RUS_COLOR, linewidth=1.8,
                  linestyle="-", marker="s", markerfacecolor=RUS_COLOR,
                  markeredgecolor=RUS_COLOR, markersize=6,
                  label="Russian 2023"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.975, 0.978),
           frameon=False, fontsize=7.5, ncol=2,
           handlelength=2.2, columnspacing=1.2, labelspacing=0.4)

fig.text(0.045, 0.026,
         "Lines extend from (−1 SD, −β) to (+1 SD, +β): a standardized predictor change of 1 SD produces a β-SD change in the standardized outcome.",
         fontsize=6.5, color="#555", ha="left")
fig.text(0.045, 0.012,
         "Annotation: group letter (E/R), wave (last two digits), β, and significance. *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=6.5, color="#555", ha="left")

plt.subplots_adjust(left=0.085, right=0.975, top=0.905, bottom=0.075,
                    wspace=0.18, hspace=0.42)

out = ROOT / "viz" / "fig_bivariate_slope_per_variable.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
