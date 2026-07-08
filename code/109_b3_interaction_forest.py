"""
Forest plot of the B₃ Contact × Language interaction coefficient from the
interactive MLR (Table 2 of MLR_Contact_Language_APA.docx, script 99).

Each row = one cell. B₃ tests whether contact's slope on the outcome depends
on language level. A significant B₃ means language moderates contact's effect;
B₃ ≈ 0 means contact and language operate independently in that cell.

Layout: 8 outcome sections, 4 dots per section (Est 2020/2023, Rus 2020/2023).

Output: viz/fig_b3_interaction_forest.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

df = pd.read_csv(ROOT / "code" / "_mlr_contact_language_interaction.tsv", sep="\t")

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

EST_COLOR = "#2563eb"
RUS_COLOR = "#d97706"

fig, ax = plt.subplots(figsize=(15.0, 13.0), dpi=300)

# Y-positions: 8 sections × 4 cells per section
y_positions = {}
y = len(OUTCOMES) * 6.5
section_gap = 0.8
within_gap = 0.9

for outcome in OUTCOMES:
    for cell in [("Estonian", 2020), ("Estonian", 2023),
                  ("Russian", 2020), ("Russian", 2023)]:
        y_positions[(outcome, *cell)] = y
        y -= within_gap
    y -= section_gap

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
    y_pos = y_positions[key]
    color = EST_COLOR if r["group"] == "Estonian" else RUS_COLOR
    B3 = r["B3_cxl"]
    ll, ul = r["CI3_low"], r["CI3_high"]
    p = r["p3"]

    # CI bracket
    ax.plot([ll, ul], [y_pos, y_pos], color=color, linewidth=2.0, alpha=0.85,
            solid_capstyle="round", zorder=2)
    for xx in (ll, ul):
        ax.plot([xx, xx], [y_pos - 0.13, y_pos + 0.13],
                color=color, linewidth=1.4, alpha=0.9, zorder=2)

    # Dot: open for 2020, filled for 2023
    if r["year"] == 2020:
        ax.scatter([B3], [y_pos], s=130, facecolor="white",
                   edgecolor=color, linewidth=1.8, zorder=3)
    else:
        ax.scatter([B3], [y_pos], s=150, color=color,
                   edgecolor="white", linewidth=1.0, zorder=3)

    # Annotation
    ann = f"{r['group'][0]} {r['year']}  B₃ = {B3:+.4f} {stars(p)}    [{ll:+.4f}, {ul:+.4f}]    {fmt_p(p)}"
    ax.text(ul + 0.003, y_pos, ann, ha="left", va="center", fontsize=8.0,
            color="#222", family="monospace")

# Reference line at 0
ax.axvline(0, color="#666", linewidth=1.0, linestyle="-", zorder=1)

# Y-axis labels at section midpoints
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
all_lo = df["CI3_low"].min()
all_hi = df["CI3_high"].max()
ax.set_xlim(all_lo - 0.01, all_hi + 0.15)
ax.set_xlabel("B₃ — Contact × Language interaction coefficient",
              fontsize=10, color="#444", labelpad=8)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#666")
ax.tick_params(axis="x", length=2.5, color="#666", labelsize=9)
ax.tick_params(axis="y", length=0)

# Grid
xt = np.arange(round(all_lo, 2), round(all_hi, 2) + 0.02, 0.02)
for x in xt:
    ax.axvline(x, color="#eee", linewidth=0.4, zorder=0)

# Title block
fig.text(0.04, 0.975,
         "Contact × Language Interaction — Forest Plot of B₃ by Outcome × Cell",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.04, 0.957,
         "Each dot is the B₃ coefficient from the interactive MLR (outcome = B₀ + B₁ × Contact_c + B₂ × Language_c + B₃ × (Contact_c × Language_c) + ε).",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.942,
         "B₃ tests whether contact's slope on the outcome depends on language. B₃ ≈ 0 → independent additive predictors. B₃ ≠ 0 → language moderates contact's effect. Reference at B₃ = 0.",
         fontsize=9, color="#444", ha="left")

handles = [
    mlines.Line2D([], [], marker="o", color=EST_COLOR, markerfacecolor="white",
                  markeredgecolor=EST_COLOR, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Estonian 2020"),
    mlines.Line2D([], [], marker="o", color=EST_COLOR, markerfacecolor=EST_COLOR,
                  markeredgecolor="white", markersize=10,
                  linestyle="None", label="Estonian 2023"),
    mlines.Line2D([], [], marker="o", color=RUS_COLOR, markerfacecolor="white",
                  markeredgecolor=RUS_COLOR, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Russian 2020"),
    mlines.Line2D([], [], marker="o", color=RUS_COLOR, markerfacecolor=RUS_COLOR,
                  markeredgecolor="white", markersize=10,
                  linestyle="None", label="Russian 2023"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.985, 0.955),
           frameon=False, fontsize=9, ncol=4,
           handlelength=1.4, columnspacing=1.5)

fig.text(0.04, 0.020,
         "B₃ in raw (unstandardized) units. Contact mean-centered within cell, inverted so higher = more contact. Language mean-centered within cell, reverse-coded so higher = more proficient.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.008,
         "HC3 robust standard errors. Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.18, right=0.985, top=0.92, bottom=0.05)

out = ROOT / "viz" / "fig_b3_interaction_forest.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
