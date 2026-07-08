"""
Per-variable visualization of the conditional contact slopes from script 105
(total effects model: contact slope = B₁ + B₃ × Language).

Each panel = one outcome. Within each panel, four lines (one per group × wave
cell) show how contact's slope on the outcome changes across language levels:
low (−1 SD), mean, high (+1 SD).

  - Flat line within a cell → no Contact × Language moderation in that cell
    (contact's slope is constant across language levels)
  - Sloped line within a cell → moderation (B₃ ≠ 0); contact's slope changes
    as language increases

Layout: 2 rows × 4 columns = 8 panels, one per outcome.

Line styling:
  Estonian 2020 — blue dashed
  Estonian 2023 — blue solid
  Russian  2020 — orange dashed
  Russian  2023 — orange solid

Output: viz/fig_conditional_slope_per_variable.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

df = pd.read_csv(ROOT / "code" / "_conditional_contact_slopes.tsv", sep="\t")

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


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST_COLOR = "#2563eb"
RUS_COLOR = "#d97706"

# Global y-axis range from all slope values
all_slopes = pd.concat([df["slope_low"], df["slope_mean"], df["slope_high"]])
all_ci_lo = pd.concat([df["CI_low_low"], df["CI_low_mean"], df["CI_low_high"]])
all_ci_hi = pd.concat([df["CI_high_low"], df["CI_high_mean"], df["CI_high_high"]])
y_lo = all_ci_lo.min() - 0.05
y_hi = all_ci_hi.max() + 0.05

fig, axes = plt.subplots(2, 4, figsize=(18.0, 10.0), dpi=300,
                          sharex=True, sharey=True)
axes = axes.flatten()

CELLS = [
    ("Estonian", 2020, EST_COLOR, (0, (5, 3)), "o", "white"),
    ("Estonian", 2023, EST_COLOR, "-",         "o", EST_COLOR),
    ("Russian",  2020, RUS_COLOR, (0, (5, 3)), "s", "white"),
    ("Russian",  2023, RUS_COLOR, "-",         "s", RUS_COLOR),
]

x_positions = [0, 1, 2]   # low, mean, high

for idx, outcome in enumerate(OUTCOMES):
    ax = axes[idx]
    sub = df[df["variable"] == outcome]
    if sub.empty:
        ax.set_visible(False); continue

    annotation_lines = []
    for (group, year, color, linestyle, marker, mfc) in CELLS:
        match = sub[(sub["group"] == group) & (sub["year"] == year)]
        if match.empty: continue
        r = match.iloc[0]
        slopes = [r["slope_low"], r["slope_mean"], r["slope_high"]]
        ci_lo  = [r["CI_low_low"], r["CI_low_mean"], r["CI_low_high"]]
        ci_hi  = [r["CI_high_low"], r["CI_high_mean"], r["CI_high_high"]]

        # Connect the 3 conditional slopes
        ax.plot(x_positions, slopes,
                color=color, linestyle=linestyle, linewidth=2.0,
                solid_capstyle="round", zorder=3)
        # Markers at each language level
        for x_pos, slope_val in zip(x_positions, slopes):
            ax.scatter([x_pos], [slope_val], s=55, color=mfc if mfc != "white" else "white",
                       marker=marker, edgecolor=color, linewidth=1.5, zorder=4)
        # Light CI error bars
        for x_pos, lo, hi in zip(x_positions, ci_lo, ci_hi):
            ax.plot([x_pos, x_pos], [lo, hi], color=color, linewidth=0.8,
                    alpha=0.4, zorder=2)

        annotation_lines.append((group, year, r["B3_interaction"], r["p_B3"], color))

    # Reference line at 0
    ax.axhline(0, color="#999", linewidth=0.6, linestyle="--", zorder=1)

    # Annotation: B₃ × significance per cell (smaller, compact)
    ann_text = "B₃ (C×L):\n" + "\n".join([
        f"{grp[0]}{yr % 100:02d}: {b:+.3f}{stars(p)}"
        for grp, yr, b, p, _ in annotation_lines
    ])
    ax.text(0.02, 0.98, ann_text, transform=ax.transAxes,
            ha="left", va="top", fontsize=8, family="monospace",
            color="#222",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white",
                      edgecolor="#aaa", linewidth=0.5, alpha=0.93))

    ax.set_title(PRETTY[outcome], fontsize=11, fontweight="bold",
                 loc="left", pad=8)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(["Low\nLang", "Mean\nLang", "High\nLang"], fontsize=8)
    ax.set_xlim(-0.4, 2.4)
    ax.set_ylim(y_lo, y_hi)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")
    ax.grid(True, axis="y", linestyle=":", linewidth=0.4, color="#eee", zorder=0)

# Axis labels
for col in range(4):
    axes[1 * 4 + col].set_xlabel("Language level (moderator)",
                                   fontsize=9, color="#444")
for row in range(2):
    axes[row * 4].set_ylabel("Conditional contact slope\nB₁ + B₃ × Language",
                              fontsize=9, color="#444")

# Title block
fig.text(0.04, 0.965,
         "Conditional Contact Slopes at Three Language Levels — by Outcome",
         fontsize=15, fontweight="bold", ha="left")
fig.text(0.04, 0.948,
         "Each panel: four lines (one per group × year cell) showing how contact's slope on the outcome changes as language increases from low (−1 SD) to high (+1 SD).",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.932,
         "Flat line within a cell = no Contact × Language moderation. Sloping line = language modifies contact's effect (B₃ ≠ 0). Thin vertical error bars = 95% CI on each conditional slope.",
         fontsize=9, color="#444", ha="left")

# Legend
handles = [
    mlines.Line2D([], [], color=EST_COLOR, linewidth=2.0,
                  linestyle=(0, (5, 3)), marker="o", markerfacecolor="white",
                  markeredgecolor=EST_COLOR, markeredgewidth=1.5, markersize=7,
                  label="Estonian 2020"),
    mlines.Line2D([], [], color=EST_COLOR, linewidth=2.0,
                  linestyle="-", marker="o", markerfacecolor=EST_COLOR,
                  markeredgecolor=EST_COLOR, markersize=7,
                  label="Estonian 2023"),
    mlines.Line2D([], [], color=RUS_COLOR, linewidth=2.0,
                  linestyle=(0, (5, 3)), marker="s", markerfacecolor="white",
                  markeredgecolor=RUS_COLOR, markeredgewidth=1.5, markersize=7,
                  label="Russian 2020"),
    mlines.Line2D([], [], color=RUS_COLOR, linewidth=2.0,
                  linestyle="-", marker="s", markerfacecolor=RUS_COLOR,
                  markeredgecolor=RUS_COLOR, markersize=7,
                  label="Russian 2023"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.952),
           frameon=False, fontsize=9, ncol=4,
           handlelength=2.8, columnspacing=2.0)

fig.text(0.04, 0.018,
         "Conditional slope formula: B_contact,total(L) = B₁ + B₃ × L, evaluated at L = −1 SD, 0 (mean), +1 SD of language. SEs and CIs from HC3 robust covariance matrix.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.005,
         "Annotation shows B₃ Contact × Language for each cell (the interaction coefficient that drives line slope). *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.07, right=0.985, top=0.90, bottom=0.06,
                    wspace=0.20, hspace=0.30)

out = ROOT / "viz" / "fig_conditional_slope_per_variable.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
