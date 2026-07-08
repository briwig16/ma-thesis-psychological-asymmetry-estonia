"""
Forest plot of the 32 bivariate contact regressions from script 97.

Layout:
  - 8 outcomes stacked vertically, each with 4 cells (Est 2020, Est 2023,
    Rus 2020, Rus 2023). 32 dots total.
  - X-axis: β (standardized regression coefficient) with 95% CIs.
  - Color: Estonian blue, Russian orange.
  - Marker style: open circle = 2020, filled circle = 2023.
  - Vertical reference line at 0.

Output: viz/fig_bivariate_contact_forest.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

df = pd.read_csv(ROOT / "code" / "_bivariate_contact_per_cell.tsv", sep="\t")

# Compute β CI by scaling the B1 CI by (β / B1)
ratio = df["beta"] / df["B1"]
df["beta_CI_low"]  = df["CI_low"]  * ratio
df["beta_CI_high"] = df["CI_high"] * ratio

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


def fmt_p(p):
    if p < .001: return "p < .001"
    return f"p = {p:.3f}".replace("0.", ".")


plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.7,
})

RUS = "#d97706"
EST = "#2563eb"

fig, ax = plt.subplots(figsize=(15.0, 13.0), dpi=300)

# Y-positions
y_positions = {}
y = len(OUTCOMES) * 6.5
section_gap = 0.8
within_section_gap = 0.9

for outcome in OUTCOMES:
    # 4 rows within this section: Est 2020, Est 2023, Rus 2020, Rus 2023
    for cell in [("Estonian", 2020), ("Estonian", 2023),
                  ("Russian", 2020), ("Russian", 2023)]:
        y_positions[(outcome, *cell)] = y
        y -= within_section_gap
    y -= section_gap  # gap between outcomes

y_min = y + 0.5
y_max = len(OUTCOMES) * 6.5 + 0.5

# Section banding
for i, outcome in enumerate(OUTCOMES):
    if i % 2 == 0:
        y_top = y_positions[(outcome, "Estonian", 2020)] + 0.5
        y_bot = y_positions[(outcome, "Russian", 2023)] - 0.5
        ax.axhspan(y_bot, y_top, facecolor="#f7f7f7", zorder=0)

# Plot each dot
for _, r in df.iterrows():
    key = (r["variable"], r["group"], r["year"])
    if key not in y_positions: continue
    y = y_positions[key]
    color = EST if r["group"] == "Estonian" else RUS
    beta = r["beta"]
    ll, ul = r["beta_CI_low"], r["beta_CI_high"]
    p = r["p"]

    # CI bracket
    ax.plot([ll, ul], [y, y], color=color, linewidth=2.0, alpha=0.85,
            solid_capstyle="round", zorder=2)
    for xx in (ll, ul):
        ax.plot([xx, xx], [y - 0.13, y + 0.13],
                color=color, linewidth=1.4, alpha=0.9, zorder=2)

    # Dot: open for 2020, filled for 2023
    if r["year"] == 2020:
        ax.scatter([beta], [y], s=130, facecolor="white",
                   edgecolor=color, linewidth=1.8, zorder=3)
    else:
        ax.scatter([beta], [y], s=150, color=color,
                   edgecolor="white", linewidth=1.0, zorder=3)

    # Annotation
    ann = f"{r['group'][0]} {r['year']}  β = {beta:+.3f} {stars(p)}    [{ll:+.3f}, {ul:+.3f}]    R² = {r['R2']:.3f}"
    ax.text(ul + 0.012, y, ann,
            ha="left", va="center", fontsize=8.0,
            color="#222", family="monospace")

# Reference line at 0
ax.axvline(0, color="#666", linewidth=1.0, linestyle="-", zorder=1)

# Y-axis labels: outcome names at center of each section
yticks, yticklabels = [], []
for outcome in OUTCOMES:
    y_top = y_positions[(outcome, "Estonian", 2020)]
    y_bot = y_positions[(outcome, "Russian", 2023)]
    yticks.append((y_top + y_bot) / 2)
    yticklabels.append(PRETTY[outcome])

ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels, fontsize=10, fontweight="bold")
ax.set_ylim(y_min, y_max)

# X-axis
all_lo = df["beta_CI_low"].min()
all_hi = df["beta_CI_high"].max()
ax.set_xlim(all_lo - 0.05, all_hi + 0.50)
ax.set_xticks(np.arange(-0.4, 0.4, 0.1))
ax.set_xlabel("β — standardized regression coefficient of out-group contact on outcome",
              fontsize=10, color="#444", labelpad=8)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#666")
ax.tick_params(axis="x", length=2.5, color="#666", labelsize=9)
ax.tick_params(axis="y", length=0)

# Light grid
for x in np.arange(-0.4, 0.4, 0.1):
    ax.axvline(x, color="#eee", linewidth=0.4, zorder=0)

# Title
fig.text(0.04, 0.975,
         "Out-group Contact as Predictor — Bivariate β by Outcome × Group × Year",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.04, 0.957,
         "Each dot represents one bivariate OLS regression (outcome = B₀ + B₁ × Contact + ε). β = standardized slope.",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.942,
         "Estonian = blue, Russian = orange. Open dot = 2020, filled dot = 2023. Reference line at β = 0 (no association).",
         fontsize=9, color="#444", ha="left")

# Legend
handles = [
    mlines.Line2D([], [], marker="o", color=EST, markerfacecolor="white",
                  markeredgecolor=EST, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Estonian 2020"),
    mlines.Line2D([], [], marker="o", color=EST, markerfacecolor=EST,
                  markeredgecolor="white", markersize=10,
                  linestyle="None", label="Estonian 2023"),
    mlines.Line2D([], [], marker="o", color=RUS, markerfacecolor="white",
                  markeredgecolor=RUS, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Russian 2020"),
    mlines.Line2D([], [], marker="o", color=RUS, markerfacecolor=RUS,
                  markeredgecolor="white", markersize=10,
                  linestyle="None", label="Russian 2023"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.955),
           frameon=False, fontsize=9, ncol=4,
           handlelength=1.4, columnspacing=1.5)

fig.text(0.04, 0.020,
         "Contact composite: Estonian respondents → Russian-speakers (Q52/K4X2); Russian respondents → Estonian-speakers (Q51/K4X1). Inverted: higher = more contact.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.008,
         "HC3 robust standard errors. Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.18, right=0.985, top=0.92, bottom=0.05)

out = ROOT / "viz" / "fig_bivariate_contact_forest.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
