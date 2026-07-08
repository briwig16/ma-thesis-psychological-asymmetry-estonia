"""
Forest plot of within-group 2020→2023 Cohen's d for each non-contact composite,
paired by group (Estonian + Russian), with the interaction F-test annotated
per row. Companion to 76_anova_2x2_composites.

The interaction effect in a 2×2 ANOVA is the difference-in-differences:
  Δ(Estonian) − Δ(Russian)
where Δ(group) = M_2023 − M_2020 for that group. Plotting the two within-
group d's side by side makes the interaction visually inspectable: when the
two dots point in opposite directions or differ substantially in magnitude,
the gap has changed (asymmetric divergence). When they point the same way
and have similar magnitudes, the change is parallel — no interaction.

The plot mirrors the contact-theory coefplot (script 64) in style:
  - Y-axis: 6 composite rows (each row contains 2 dots, Estonian + Russian)
  - X-axis: within-group Cohen's d, 2023 − 2020
  - Vertical reference at 0 (no change)
  - Color-coded by group (blue Estonian, orange Russian)

Output: viz/fig_anova_interaction_forest.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

# Read canonical effect-size TSV (within-group rows already contain 2020→2023 d's)
es = pd.read_csv(ROOT / "code" / "_effect_sizes.tsv", sep="\t")
es = es[es["table"] == "within"]

# ANOVA TSV (interaction F, p, η²p)
an = pd.read_csv(ROOT / "code" / "_anova_2x2_composites.tsv", sep="\t")
an = an.set_index("variable")

# Composites in plot order (top to bottom).
# Tuples of (es_TSV_name, anova_TSV_name, display_label).
# Effect-sizes TSV uses canonical name "Minority Support Inclusion";
# ANOVA TSV uses user-facing label "Minority Inclusion Support"
# (per CLAUDE.md 2026-05-03 convention).
COMPOSITES_SPEC = [
    ("Superordinate Identity",             "Superordinate Identity",             "Superordinate Identity"),
    ("SD: Primary Out-group",              "SD: Primary Out-group",              "SD: Primary Out-group"),
    ("SD: General Out-group",              "SD: General Out-group",              "SD: General Out-group  ⁱ"),
    ("Comparative Opportunity Assessment", "Comparative Opportunity Assessment", "Comparative Opportunity"),
    ("Belief in Inevitable Conflict",      "Belief in Inevitable Conflict",      "Belief in Inevitable Conflict"),
    ("Minority Support Inclusion",         "Minority Inclusion Support",         "Minority Inclusion Support"),
]
COMPOSITES = [es_name for es_name, _, _ in COMPOSITES_SPEC]
ANOVA_NAME = {es_name: anova_name for es_name, anova_name, _ in COMPOSITES_SPEC}
PRETTY    = {es_name: pretty      for es_name, _, pretty      in COMPOSITES_SPEC}

# Caveat composites (note "ⁱ" superscript for SD: General; per-group items already noted)
CAVEAT = {
    "SD: General Out-group": "ⁱ Items differ across waves (3 in 2020, 6 in 2023); "
                              "year and interaction effects partially confound with item change.",
}


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"


def fmt_p(p):
    if p < .001: return "p < .001"
    return f"p = {p:.3f}".replace("0.", ".")


# ---- Plot setup -----------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.7,
})

RUS = "#d97706"
EST = "#2563eb"

fig, ax = plt.subplots(figsize=(14.0, 7.5), dpi=300)

# Y-positions: one row per composite, two dots (Est + Rus) per row
row_spacing = 1.0
dot_offset = 0.20   # vertical separation between Est and Rus within a row
y_centers = {comp: (len(COMPOSITES) - i) * row_spacing for i, comp in enumerate(COMPOSITES)}

# Light row-separator bands
for i, comp in enumerate(COMPOSITES):
    if i % 2 == 0:
        y = y_centers[comp]
        ax.axhspan(y - 0.45, y + 0.45, facecolor="#f7f7f7", zorder=0)

# Plot data
for comp in COMPOSITES:
    y = y_centers[comp]
    rows = es[es["variable"] == comp][["comparison","d","CI_low","CI_high","p"]].set_index("comparison")
    # Estonian
    e = rows.loc["Estonian"]
    # Russian
    r = rows.loc["Russian"]

    for grp, row, color, dy in [
        ("Estonian", e, EST, +dot_offset),
        ("Russian",  r, RUS, -dot_offset),
    ]:
        yy = y + dy
        d, ll, ul = row["d"], row["CI_low"], row["CI_high"]
        p = row["p"]
        # CI bracket
        ax.plot([ll, ul], [yy, yy], color=color, linewidth=2.2, alpha=0.85,
                solid_capstyle="round", zorder=2)
        for x in (ll, ul):
            ax.plot([x, x], [yy - 0.08, yy + 0.08],
                    color=color, linewidth=1.6, alpha=0.9, zorder=2)
        # Point
        ax.scatter([d], [yy], s=170, color=color, edgecolor="white",
                   linewidth=1.0, zorder=3)
        # Label to right of CI
        ax.text(ul + 0.015, yy,
                f"{grp:<8}  d = {d:+.3f} {stars(p)}    "
                f"95% CI [{ll:+.3f}, {ul:+.3f}]    {fmt_p(p)}",
                ha="left", va="center", fontsize=8,
                color="#222", family="monospace")

    # Interaction annotation on the right
    a = an.loc[ANOVA_NAME[comp]]
    F_ix = a["F_interaction"]; p_ix = a["p_interaction"]; eta_ix = a["eta2p_interaction"]
    ax.text(1.30, y,
            f"Interaction: F = {F_ix:.2f}, {fmt_p(p_ix)} {stars(p_ix)}, η²p = .{int(round(eta_ix*1000)):03d}",
            ha="left", va="center", fontsize=8.5,
            color="#333", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff8e7",
                      edgecolor="#e0c97f", linewidth=0.6, alpha=0.95))

# Reference line at 0
ax.axvline(0, color="#666", linewidth=1.0, linestyle="-", zorder=1)

# Y-axis labels
ax.set_yticks(list(y_centers.values()))
ax.set_yticklabels([PRETTY[c] for c in COMPOSITES], fontsize=10, fontweight="bold")
ax.set_ylim(0.4, len(COMPOSITES) + 0.7)

# X-axis
ax.set_xlim(-0.75, 1.85)
ax.set_xticks(np.arange(-0.7, 0.61, 0.1))
ax.set_xlabel("Within-group Cohen's d  (2023 − 2020)   |   Positive = mean shifted up; negative = mean shifted down",
              fontsize=9.5, color="#444", labelpad=8)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#666")
ax.tick_params(axis="x", length=2.5, color="#666", labelsize=8)
ax.tick_params(axis="y", length=0)

# Light grid
for x in np.arange(-0.7, 0.61, 0.1):
    ax.axvline(x, color="#eee", linewidth=0.4, zorder=0)

# Title block
fig.text(0.04, 0.965,
         "Asymmetric Divergence — Within-Group Change 2020 → 2023 by Composite",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Each row shows the within-group Cohen's d for the 2020 → 2023 shift for Estonian (blue) and Russian (orange) respondents.",
         fontsize=8.5, color="#444", ha="left")
fig.text(0.04, 0.918,
         "Interaction effect (yellow box) tests whether the two groups changed differently — the asymmetric-divergence claim. Positive d = mean shifted up.",
         fontsize=8.5, color="#444", ha="left")

# Legend
est_dot = mlines.Line2D([], [], marker="o", color="white",
                        markerfacecolor=EST, markeredgecolor="white",
                        markersize=10, linestyle="None", label="Estonian respondents")
rus_dot = mlines.Line2D([], [], marker="o", color="white",
                        markerfacecolor=RUS, markeredgecolor="white",
                        markersize=10, linestyle="None", label="Russian respondents")
zero = mlines.Line2D([], [], color="#666", linewidth=1.0,
                     label="0 = no change 2020 → 2023")
fig.legend(handles=[est_dot, rus_dot, zero],
           loc="upper right", bbox_to_anchor=(0.97, 0.918),
           frameon=False, fontsize=8.5, ncol=3, handlelength=2.0,
           columnspacing=2.2)

# Footer
fig.text(0.04, 0.022,
         "Within-group d uses root-mean-square SD denominator (CLAUDE.md). HC0 SEs on d via Hedges & Olkin (1985). Interaction effect from Type III ANOVA on the full 2 × 2 design.",
         fontsize=7.0, color="#555", ha="left")
fig.text(0.04, 0.008,
         "ⁱ SD: General Out-group uses different items per wave (3 in 2020, 6 in 2023); the within-group d's and interaction effect partially confound year with item-set change.",
         fontsize=7.0, color="#555", ha="left")

plt.subplots_adjust(left=0.16, right=0.985, top=0.86, bottom=0.12)

out = ROOT / "viz" / "fig_anova_interaction_forest.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
