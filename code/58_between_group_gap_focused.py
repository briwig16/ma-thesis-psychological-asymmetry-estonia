"""
Publication-ready diverging bar chart of between-group difference (Cohen's d,
Estonian vs Russian) in 2020 and 2023, focused subset for thesis insertion.

Differences from script 20 (canonical fig_between_group_gap.jpg):
  - Contact variables removed (Contact: Russian / Estonian Speakers)
  - "Minority Support Inclusion" relabeled to "Minority Inclusion Support"
  - Three core variables shown in BOLD:
      Social Distance: Primary Out-group
      Minority Inclusion Support
      Belief in Inevitable Conflict
  - "Social Distance: General Out-group" shown in ITALIC

Output: viz/fig_between_group_gap_focused.jpg  (300 DPI)
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# ---------- Data (matches script 20, contact rows removed) -----------------
# (label, raw_d_2020, p_2020, raw_d_2023, p_2023, inverted, weight, style)
#   weight in {"normal", "bold"}; style in {"normal", "italic"}
rows = [
    ("Social Distance: Primary Out-group",   +0.74, 0.0000, +1.18, 0.0000, False, "bold",   "normal"),
    ("Minority Inclusion Support",           +0.95, 0.0000, +1.14, 0.0000, True,  "bold",   "normal"),
    ("Superordinate Identity",               -1.08, 0.0000, -0.79, 0.0000, True,  "normal", "normal"),
    ("Belief in Inevitable Conflict",        +0.44, 0.0000, +0.78, 0.0000, False, "bold",   "normal"),
    ("Comparative Opportunity Assessment",   +0.83, 0.0000, +0.74, 0.0000, True,  "normal", "normal"),
    ("Group ID Patterns",                    +0.30, 0.0000, +0.15, 0.009,  False, "normal", "normal"),
    ("Social Distance: General Out-group",   -0.21, 0.0003, +0.11, 0.049,  False, "normal", "italic"),
    ("Territorial Attachment",               -0.34, 0.0000, -0.09, 0.115,  True,  "normal", "normal"),
]


def stars(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


labels, d_2020, d_2023, p_2020, p_2023, inverted = [], [], [], [], [], []
weights, styles = [], []
for lab, d20, p20, d23, p23, inv, w, st in rows:
    flip = -1 if inv else 1
    labels.append(lab + ("  (inv.)" if inv else ""))
    d_2020.append(d20 * flip)
    d_2023.append(d23 * flip)
    p_2020.append(p20)
    p_2023.append(p23)
    inverted.append(inv)
    weights.append(w)
    styles.append(st)

n = len(labels)
y_pos = np.arange(n)[::-1]


# ---------- Style ----------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.7,
})

C2020 = "#94a3b8"
C2023 = "#1e3a8a"

fig, ax = plt.subplots(figsize=(7.5, 6.4), dpi=300)

bar_h = 0.36
y_2020 = y_pos + bar_h/2 + 0.02
y_2023 = y_pos - bar_h/2 - 0.02

# Bars
for i in range(n):
    sig_20 = p_2020[i] < 0.05
    sig_23 = p_2023[i] < 0.05
    ax.barh(y_2020[i], d_2020[i], height=bar_h,
            color=C2020, alpha=0.95 if sig_20 else 0.30,
            edgecolor=C2020, linewidth=0.8 if not sig_20 else 0,
            linestyle="-" if sig_20 else (0, (3, 2)))
    ax.barh(y_2023[i], d_2023[i], height=bar_h,
            color=C2023, alpha=0.95 if sig_23 else 0.30,
            edgecolor=C2023, linewidth=0.8 if not sig_23 else 0,
            linestyle="-" if sig_23 else (0, (3, 2)))

# d labels at end of bars
for i in range(n):
    for d, y, p in [
        (d_2020[i], y_2020[i], p_2020[i]),
        (d_2023[i], y_2023[i], p_2023[i]),
    ]:
        offset = 0.04 if d >= 0 else -0.04
        ha = "left" if d >= 0 else "right"
        sig = p < 0.05
        ax.text(d + offset, y, f"{d:+.2f} {stars(p)}",
                va="center", ha=ha,
                fontsize=7.5,
                color="#111" if sig else "#888",
                fontweight="bold" if sig else "normal")

# Reference lines
for x in [-2, -1.5, -1, -0.5, 0.5, 1, 1.5, 2]:
    ax.axvline(x, color="#cccccc", linewidth=0.6, linestyle=":", zorder=0)
ax.axvline(0, color="#333333", linewidth=0.9, zorder=1)

for x, lbl in [(-1.5, "very large"), (-0.8, "large"), (-0.5, "medium"),
               (0.5, "medium"), (0.8, "large"), (1.5, "very large")]:
    ax.text(x, -0.55, lbl, ha="center", fontsize=6.5, color="#999", style="italic")

# Axes
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=8.5)
ax.set_ylim(-0.9, n + 0.4)
ax.set_xlim(-2.0, 2.0)
ax.set_xticks([-2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2])
ax.set_xlabel(
    "Cohen's d (between-group: Estonian vs. Russian respondents)",
    fontsize=9.5, labelpad=8
)

# Apply per-label weight / style
for tl, w, st in zip(ax.get_yticklabels(), weights, styles):
    tl.set_fontweight(w)
    tl.set_fontstyle(st)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#333333")
ax.spines["bottom"].set_color("#333333")
ax.tick_params(axis="x", length=3, color="#333333")
ax.tick_params(axis="y", length=0)

# Title and subtitle
fig.text(0.05, 0.965, "Between-Group Difference in Intergroup Attitudes, 2020 and 2023",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.05, 0.937,
         "Cohen's d comparing Estonian and Russian respondents in each year",
         fontsize=9, color="#444", ha="left")

# Legend
patch_2020 = mpatches.Patch(color=C2020, label="2020")
patch_2023 = mpatches.Patch(color=C2023, label="2023")
patch_sig  = mpatches.Patch(facecolor="white", edgecolor="#666",
                            label="Faded bars: not significant (p ≥ .05)")
fig.legend(handles=[patch_2020, patch_2023, patch_sig],
           loc="upper left", bbox_to_anchor=(0.03, 0.910),
           frameon=False, fontsize=8,
           handlelength=1.4, handleheight=1.0, ncol=1)

# Footnote
fig.text(0.05, 0.020,
         "(inv.) = scale inverted so that positive d indicates Estonian respondents score higher on the construct.\n"
         "Significance: *** p<.001, ** p<.01, * p<.05, ns = not significant. d uses root-mean-square SD: "
         r"$d = (M_{Est} - M_{Rus}) / \sqrt{(SD_1^2 + SD_2^2)/2}$.",
         fontsize=7, color="#555", ha="left")

plt.subplots_adjust(left=0.40, right=0.97, top=0.89, bottom=0.13)

out_path = Path(__file__).parent.parent / "viz" / "fig_between_group_gap_focused.jpg"
plt.savefig(out_path, dpi=300, format="jpg",
            facecolor="white", pil_kwargs={"quality": 95})
print(f"Saved: {out_path}")
