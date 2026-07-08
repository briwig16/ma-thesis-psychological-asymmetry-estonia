"""
Magnitude-only variant of the between-group gap chart.

Where fig_between_group_gap.jpg shows signed Cohen's d (left = Russians higher,
right = Estonians higher), this version plots |d| as bars extending from the
left, so every bar shows the size of the gap regardless of direction. Direction
is encoded in two ways:
  - The trailing "(E)" / "(R)" label on each bar tip, colored blue/amber.
  - The bar value text uses the same color.

Source of truth: code/_effect_sizes.tsv. The TSV stores signed d in the
convention "positive = Estonian higher on the construct" (after code/24's
inversion for inv=True rows). This script takes |d| for the bar length and
sign(d) > 0 for Estonian-higher, sign(d) < 0 for Russian-higher.

Outputs viz/fig_between_group_gap_magnitude.jpg at 300 DPI.
"""

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

ROOT = Path(__file__).parent.parent

# ---------- Read d and p from the canonical TSV --------------------------
tsv_path = ROOT / "code" / "_effect_sizes.tsv"
between = {}
with open(tsv_path) as f:
    for r in csv.DictReader(f, delimiter="\t"):
        if r["table"] != "between":
            continue
        between[(r["variable"], r["comparison"])] = {
            "d": float(r["d"]),
            "p": float(r["p"]),
        }

# Same row order as fig_between_group_gap.jpg for easy side-by-side reading.
rows = [
    ("Contact: Russian Speakers",          "Contact: Russian Speakers",         True),
    ("Contact: Estonian Speakers",         "Contact: Estonian Speakers",        True),
    ("SD: Primary Out-group",              "Social Distance: Primary Out-group", False),
    ("Minority Support Inclusion",         "Minority Inclusion Support",        True),
    ("Superordinate Identity",             "Superordinate Identity",            True),
    ("Belief in Inevitable Conflict",      "Belief in Inevitable Conflict",     False),
    ("Comparative Opportunity Assessment", "Comparative Opportunity Assessment", True),
    ("Group ID Patterns",                  "Group ID Patterns",                 False),
    ("SD: General Out-group",              "Social Distance: General Out-group", False),
    ("Territorial Attachment",             "Territorial Attachment",            True),
]

def stars(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"

labels = []
abs_d_2020, abs_d_2023 = [], []
sign_2020, sign_2023 = [], []     # +1 = Est higher, -1 = Rus higher
p_2020, p_2023 = [], []
for tsv_name, lbl, inv in rows:
    r20 = between[(tsv_name, "2020")]
    r23 = between[(tsv_name, "2023")]
    labels.append(lbl + ("  (inv.)" if inv else ""))
    abs_d_2020.append(abs(r20["d"]))
    abs_d_2023.append(abs(r23["d"]))
    sign_2020.append(1 if r20["d"] >= 0 else -1)
    sign_2023.append(1 if r23["d"] >= 0 else -1)
    p_2020.append(r20["p"])
    p_2023.append(r23["p"])

n = len(labels)
y_pos = np.arange(n)[::-1]

# ---------- Style ---------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.7,
})

C2020 = "#94a3b8"   # slate-400 — past
C2023 = "#1e3a8a"   # blue-900  — focus
EST   = "#2563eb"   # blue
RUS   = "#d97706"   # amber

fig, ax = plt.subplots(figsize=(7.5, 7.4), dpi=300)

bar_h = 0.36
y_2020 = y_pos + bar_h/2 + 0.02
y_2023 = y_pos - bar_h/2 - 0.02

# Bars (all start at 0 and grow rightward)
for i in range(n):
    sig_20 = p_2020[i] < 0.05
    sig_23 = p_2023[i] < 0.05
    ax.barh(y_2020[i], abs_d_2020[i], height=bar_h,
            color=C2020, alpha=0.95 if sig_20 else 0.30,
            edgecolor=C2020, linewidth=0.8 if not sig_20 else 0,
            linestyle="-" if sig_20 else (0,(3,2)))
    ax.barh(y_2023[i], abs_d_2023[i], height=bar_h,
            color=C2023, alpha=0.95 if sig_23 else 0.30,
            edgecolor=C2023, linewidth=0.8 if not sig_23 else 0,
            linestyle="-" if sig_23 else (0,(3,2)))

# d label at end of each bar
def write_label(d_abs, y, p):
    sig = p < 0.05
    ax.text(d_abs + 0.04, y, f"{d_abs:.2f} {stars(p)}",
            va="center", ha="left",
            fontsize=7.5,
            color="#111" if sig else "#888",
            fontweight="bold" if sig else "normal")

for i in range(n):
    write_label(abs_d_2020[i], y_2020[i], p_2020[i])
    write_label(abs_d_2023[i], y_2023[i], p_2023[i])

# Reference lines
for x in [0.5, 1.0, 1.5, 2.0]:
    ax.axvline(x, color="#cccccc", linewidth=0.6, linestyle=":", zorder=0)
ax.axvline(0, color="#333333", linewidth=0.9, zorder=1)

# Effect-size benchmark labels under axis
for x, lbl in [(0.5, "medium"), (0.8, "large"), (2.0, "very large")]:
    ax.text(x, -0.55, lbl, ha="center", fontsize=6.5, color="#999", style="italic")

# Axes
ax.set_yticks(y_pos)
ax.set_yticklabels(labels, fontsize=8.5)
ax.set_ylim(-0.9, n + 0.4)
ax.set_xlim(0, 2.85)
ax.set_xticks([0, 0.5, 1.0, 1.5, 2.0, 2.5])
ax.set_xlabel("|Cohen's d| — magnitude of between-group gap (Estonian vs. Russian)",
              fontsize=9.5, labelpad=8)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#333333")
ax.spines["bottom"].set_color("#333333")
ax.tick_params(axis="x", length=3, color="#333333")
ax.tick_params(axis="y", length=0)

# Title and subtitle
fig.text(0.05, 0.965, "Magnitude of Between-Group Gap, 2020 and 2023",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.05, 0.940,
         "|Cohen's d| comparing Estonian and Russian respondents — bar length is the size of the gap regardless of direction",
         fontsize=9, color="#444", ha="left")

# Legend (year palette + significance only — direction tags explained in footnote)
patch_2020 = mpatches.Patch(color=C2020, label="2020")
patch_2023 = mpatches.Patch(color=C2023, label="2023")
patch_sig  = mpatches.Patch(facecolor="white", edgecolor="#666",
                            label="Faded bars: not significant (p ≥ .05)")
fig.legend(handles=[patch_2020, patch_2023, patch_sig],
           loc="upper left", bbox_to_anchor=(0.03, 0.915),
           frameon=False, fontsize=8,
           handlelength=1.4, handleheight=1.0, ncol=1)

# Footnote
fig.text(0.05, 0.038,
         "(inv.) = construct scale was inverted (raw scale: lower = more of construct) so higher = more of construct.",
         fontsize=7, color="#555", ha="left")
fig.text(0.05, 0.014,
         "Significance: *** p<.001, ** p<.01, * p<.05, ns = not significant. d uses root-mean-square SD: "
         r"$d = (M_{Est} - M_{Rus}) / \sqrt{(SD_1^2 + SD_2^2)/2}$.",
         fontsize=7, color="#555", ha="left")

plt.subplots_adjust(left=0.37, right=0.97, top=0.89, bottom=0.14)

out_path = ROOT / "viz" / "fig_between_group_gap_magnitude.jpg"
plt.savefig(out_path, dpi=300, format="jpg",
            facecolor="white", pil_kwargs={"quality": 95})
print(f"Saved: {out_path}")
