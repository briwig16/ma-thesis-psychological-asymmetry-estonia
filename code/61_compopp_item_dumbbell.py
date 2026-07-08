"""
Dumbbell chart — Q44 / K3X1 Comparative Opportunity Assessment item-level
==========================================================================
Same visual grammar as fig_between_group_dumbbell.jpg (script 21), but each
row is one of the 12 items in the Comparative Opportunity battery instead of
a composite variable.

For each item:
  - Two horizontal dumbbells stacked: 2020 (open dots, dashed) and 2023
    (filled dots, solid) connecting Estonian and Russian mean responses
  - Three-column layout: item name | dumbbell | between-group Cohen's d
  - Vertical dashed reference line at 3.0 ("perceived equal opportunity")

Q44 scale (raw, NOT inverted):
  1 = much better for Estonians
  3 = equal
  5 = much better for other nationalities

Output: viz/fig_compopp_item_dumbbell.jpg  (300 DPI)
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.lines as mlines
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent

ITEM_LABELS = [
    "Material well-being",
    "Cultural participation",
    "Education",
    "Social / political rights",
    "Entrepreneurship",
    "Career & jobs",
    "Medical care",
    "Housing",
    "Leisure & holidays",
    "Children & youth opportunities",
    "Sports & exercise",
    "State benefits / services",
]


# ---------- Load data --------------------------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).dropna().astype(float)


def cohens_d(m1, sd1, n1, m2, sd2, n2):
    s = math.sqrt((sd1**2 + sd2**2) / 2)
    return (m1 - m2) / s if s > 0 else float("nan")


def stars(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


# ---------- Build per-item rows ---------------------------------------------
rows = []
for i, label in enumerate(ITEM_LABELS, start=1):
    e20 = to_num(df20[df20["ethnicity_binary"] == 0][f"K3X1_{i}"])
    r20 = to_num(df20[df20["ethnicity_binary"] == 1][f"K3X1_{i}"])
    e23 = to_num(df23[df23["ethnicity_binary"] == 0][f"Q44_{i}"])
    r23 = to_num(df23[df23["ethnicity_binary"] == 1][f"Q44_{i}"])

    d20 = cohens_d(e20.mean(), e20.std(ddof=1), len(e20),
                   r20.mean(), r20.std(ddof=1), len(r20))
    d23 = cohens_d(e23.mean(), e23.std(ddof=1), len(e23),
                   r23.mean(), r23.std(ddof=1), len(r23))
    p20 = float(stats.ttest_ind(e20, r20, equal_var=False).pvalue)
    p23 = float(stats.ttest_ind(e23, r23, equal_var=False).pvalue)

    rows.append({
        "name": label, "idx": i,
        "e20_M": e20.mean(), "r20_M": r20.mean(),
        "e23_M": e23.mean(), "r23_M": r23.mean(),
        "d20": d20, "d23": d23,
        "s20": stars(p20), "s23": stars(p23),
    })


# ---------- Diagnostics -----------------------------------------------------
print("=" * 100)
print("Q44 / K3X1 — Comparative Opportunity Assessment item-level dumbbell data")
print("Scale: 1 = much better for Estonians, 3 = equal, 5 = much better for other nationalities")
print("=" * 100)
for r in rows:
    print(f"  Q44_{r['idx']:<2d}  {r['name']:<32s}  "
          f"Est20={r['e20_M']:.2f}  Rus20={r['r20_M']:.2f}  d20={r['d20']:+.2f} {r['s20']:<3s}    "
          f"Est23={r['e23_M']:.2f}  Rus23={r['r23_M']:.2f}  d23={r['d23']:+.2f} {r['s23']}")


# ---------- Style / layout --------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.6,
})

EST       = "#2563eb"
RUS       = "#d97706"
LINE_2020 = "#9ca3af"
LINE_2023 = "#1f2937"
EQUAL     = "#9ca3af"

n = len(rows)
SCALE_MIN, SCALE_MAX = 1, 5

fig = plt.figure(figsize=(9.0, 12.0), dpi=300)
gs = gridspec.GridSpec(
    n, 3,
    width_ratios=[1.7, 4.0, 1.2],
    wspace=0.10, hspace=0.65,
    left=0.03, right=0.985, top=0.890, bottom=0.075
)

for i, row in enumerate(rows):
    name = row["name"]
    e20, r20 = row["e20_M"], row["r20_M"]
    e23, r23 = row["e23_M"], row["r23_M"]
    d20, d23 = row["d20"], row["d23"]
    s20, s23 = row["s20"], row["s23"]

    # --- Column 1: variable name ----------------------------------------
    ax_l = fig.add_subplot(gs[i, 0])
    ax_l.axis("off")
    line1, line2 = name, None
    if len(name) > 18:
        words = name.split(" ")
        best, best_diff = 0, 1e9
        for k in range(1, len(words)):
            left_text = " ".join(words[:k])
            right_text = " ".join(words[k:])
            diff = abs(len(left_text) - len(right_text))
            if diff < best_diff:
                best, best_diff = k, diff
        line1 = " ".join(words[:best])
        line2 = " ".join(words[best:])
    if line2:
        ax_l.text(0.98, 0.66, line1, ha="right", va="center",
                  fontsize=9.5, fontweight="bold", color="#111",
                  transform=ax_l.transAxes)
        ax_l.text(0.98, 0.42, line2, ha="right", va="center",
                  fontsize=9.5, fontweight="bold", color="#111",
                  transform=ax_l.transAxes)
        ax_l.text(0.98, 0.18, f"Q44_{row['idx']}",
                  ha="right", va="center", fontsize=7.2, color="#666",
                  style="italic", transform=ax_l.transAxes)
    else:
        ax_l.text(0.98, 0.55, line1, ha="right", va="center",
                  fontsize=9.7, fontweight="bold", color="#111",
                  transform=ax_l.transAxes)
        ax_l.text(0.98, 0.27, f"Q44_{row['idx']}",
                  ha="right", va="center", fontsize=7.2, color="#666",
                  style="italic", transform=ax_l.transAxes)

    # --- Column 2: dumbbell plot ----------------------------------------
    ax = fig.add_subplot(gs[i, 1])

    Y_2020, Y_2023 = 1.0, 0.0

    # Equality reference at 3.0 (dashed vertical line behind everything)
    ax.axvline(3.0, color=EQUAL, linewidth=0.8, linestyle=(0, (2, 3)),
               alpha=0.7, zorder=0)

    # Connectors
    ax.plot([min(e20, r20), max(e20, r20)], [Y_2020, Y_2020],
            color=LINE_2020, linestyle=(0, (3, 2)),
            linewidth=1.4, alpha=0.85, zorder=1)
    ax.plot([min(e23, r23), max(e23, r23)], [Y_2023, Y_2023],
            color=LINE_2023, linestyle="-",
            linewidth=1.6, alpha=0.95, zorder=1)

    # Dots
    ax.scatter([e20], [Y_2020], s=80, facecolors="white",
               edgecolors=EST, linewidths=1.7, zorder=3)
    ax.scatter([r20], [Y_2020], s=80, facecolors="white",
               edgecolors=RUS, linewidths=1.7, zorder=3)
    ax.scatter([e23], [Y_2023], s=85, color=EST, edgecolors="white",
               linewidths=0.8, zorder=3)
    ax.scatter([r23], [Y_2023], s=85, color=RUS, edgecolors="white",
               linewidths=0.8, zorder=3)

    # Numeric labels (place outside dots when close, above/below otherwise)
    OVERLAP_THRESHOLD = 0.30

    def place_pair(v_est, v_rus, y, dy):
        close = abs(v_est - v_rus) < OVERLAP_THRESHOLD
        nudge_y = +0.18 if dy > 0 else -0.18
        if close:
            if v_est <= v_rus:
                left_x, left_c = v_est, EST
                right_x, right_c = v_rus, RUS
            else:
                left_x, left_c = v_rus, RUS
                right_x, right_c = v_est, EST
            ax.text(left_x - 0.05, y + nudge_y, f"{left_x:.2f}",
                    ha="right", va="center", fontsize=7.4,
                    color=left_c, fontweight="bold")
            ax.text(right_x + 0.05, y + nudge_y, f"{right_x:.2f}",
                    ha="left", va="center", fontsize=7.4,
                    color=right_c, fontweight="bold")
        else:
            ax.text(v_est, y + dy, f"{v_est:.2f}",
                    ha="center", va="center", fontsize=7.4,
                    color=EST, fontweight="bold")
            ax.text(v_rus, y + dy, f"{v_rus:.2f}",
                    ha="center", va="center", fontsize=7.4,
                    color=RUS, fontweight="bold")

    place_pair(e20, r20, Y_2020, +0.62)
    place_pair(e23, r23, Y_2023, -0.62)

    # Year labels inside the axis on the left
    ax.text(0.005, Y_2020, "2020", ha="left", va="center",
            fontsize=7.4, color="#666", transform=ax.get_yaxis_transform())
    ax.text(0.005, Y_2023, "2023", ha="left", va="center",
            fontsize=7.6, color="#222", fontweight="bold",
            transform=ax.get_yaxis_transform())

    # Axis range
    pad_left = (SCALE_MAX - SCALE_MIN) * 0.08
    ax.set_xlim(SCALE_MIN - pad_left, SCALE_MAX + 0.05)
    ax.set_ylim(-1.1, 2.1)
    ax.set_yticks([])

    xticks = list(range(SCALE_MIN, SCALE_MAX + 1))
    ax.set_xticks(xticks)
    ax.tick_params(axis="x", length=2.5, color="#888", labelsize=6.8, pad=2,
                   labelcolor="#666")

    # Light vertical gridlines at integer ticks
    for xt in xticks:
        ax.axvline(xt, color="#e5e7eb", linewidth=0.5, zorder=0)

    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")
    ax.spines["bottom"].set_linewidth(0.5)

    # --- Column 3: Cohen's d ---------------------------------------------
    ax_r = fig.add_subplot(gs[i, 2])
    ax_r.axis("off")
    ax_r.text(0.05, 0.66, f"d = {d20:+.2f} {s20}",
              ha="left", va="center", fontsize=8.0,
              color="#777" if s20 == "ns" else "#222",
              fontweight="normal" if s20 == "ns" else "bold",
              transform=ax_r.transAxes)
    ax_r.text(0.05, 0.34, f"d = {d23:+.2f} {s23}",
              ha="left", va="center", fontsize=8.0,
              color="#777" if s23 == "ns" else "#222",
              fontweight="normal" if s23 == "ns" else "bold",
              transform=ax_r.transAxes)


# ---------- Title, subtitle, legend, footnote ------------------------------
fig.text(0.03, 0.967,
         "Comparative Opportunity Assessment — Item-Level Dumbbell, 2020 and 2023",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.03, 0.950,
         "Estonian (blue) vs. Russian (amber) respondent means on each Q44 item.",
         fontsize=8.5, color="#444", ha="left")
fig.text(0.03, 0.937,
         "Raw 1–5 scale: 1 = much better for Estonians, 3 = equal, 5 = much better for other nationalities.",
         fontsize=8.5, color="#444", ha="left")

est_dot = mlines.Line2D([], [], marker="o", color="white",
                        markerfacecolor=EST, markeredgecolor=EST,
                        markersize=8, linestyle="None",
                        label="Estonian respondents")
rus_dot = mlines.Line2D([], [], marker="o", color="white",
                        markerfacecolor=RUS, markeredgecolor=RUS,
                        markersize=8, linestyle="None",
                        label="Russian respondents")
y20_line = mlines.Line2D([], [], marker="o", color=LINE_2020,
                         markerfacecolor="white", markeredgecolor="#666",
                         markersize=7, linestyle=(0, (3, 2)),
                         linewidth=1.4, label="2020 (open dots, dashed)")
y23_line = mlines.Line2D([], [], marker="o", color=LINE_2023,
                         markerfacecolor="#444", markeredgecolor="#444",
                         markersize=7, linestyle="-",
                         linewidth=1.6, label="2023 (filled dots, solid)")
eq_line = mlines.Line2D([], [], color=EQUAL, linewidth=0.8,
                        linestyle=(0, (2, 3)),
                        label="3.0 = equal opportunity")
fig.legend(handles=[est_dot, rus_dot, y20_line, y23_line, eq_line],
           loc="upper center", bbox_to_anchor=(0.5, 0.918),
           frameon=False, fontsize=7.6, handlelength=2.4,
           handleheight=1.0, ncol=5, columnspacing=1.6)

# Footnote
fig.text(0.03, 0.030,
         "Means below 3.0 indicate the respondent group perceives the listed domain as more accessible to Estonians; above 3.0, more accessible to other nationalities.",
         fontsize=7.0, color="#555", ha="left")
fig.text(0.03, 0.015,
         "Cohen's d uses root-mean-square SD: "
         r"$d = (M_{Est} - M_{Rus}) / \sqrt{(SD_1^2 + SD_2^2)/2}$. "
         "Positive d means Estonians scored higher on the item (perceived more equality). Significance: *** p<.001, ** p<.01, * p<.05, ns = not significant.",
         fontsize=7.0, color="#555", ha="left")

out_path = ROOT / "viz" / "fig_compopp_item_dumbbell.jpg"
plt.savefig(out_path, dpi=300, format="jpg",
            facecolor="white", pil_kwargs={"quality": 95})
print(f"\nSaved: {out_path}")
