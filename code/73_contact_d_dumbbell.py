"""
Focused dumbbell chart of between-group differences (Estonian vs. Russian)
for the two contact composites only — same visual conventions as
viz/fig_between_group_dumbbell_d.jpg (normalized 0-1 axis, 2020 open / 2023
filled, Cohen's d annotated on the right).

Outputs viz/fig_contact_d_dumbbell.jpg at 300 DPI.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.lines as mlines
from pathlib import Path
import csv

# ---------- Pull canonical means / d / p from _effect_sizes.tsv -------------
TSV = Path(__file__).parent / "_effect_sizes.tsv"

records = {}
with open(TSV) as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        records[(row["variable"], row["table"], row["comparison"])] = row

def stars(p):
    p = float(p)
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"

# The means stored in _effect_sizes.tsv match the visualization convention
# used in code/22 (higher = more contact). Use them directly — no further
# inversion. M1 = Estonian, M2 = Russian.
rows = []
for label in ("Contact: Russian Speakers", "Contact: Estonian Speakers"):
    r20 = records[(label, "between", "2020")]
    r23 = records[(label, "between", "2023")]
    rows.append((
        label, 1, 5,
        float(r20["M1"]), float(r20["M2"]),
        float(r23["M1"]), float(r23["M2"]),
        abs(float(r20["d"])), abs(float(r23["d"])),
        stars(r20["p"]), stars(r23["p"]),
        "(inv.)",
    ))

def norm(v, mn, mx):
    return (v - mn) / (mx - mn)

# ---------- Style ----------------------------------------------------------
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

n = len(rows)
fig = plt.figure(figsize=(9.0, 4.2), dpi=300)
gs = gridspec.GridSpec(
    n, 3,
    width_ratios=[1.7, 4.0, 1.2],
    wspace=0.10, hspace=0.85,
    left=0.03, right=0.985, top=0.78, bottom=0.22
)

for i, row in enumerate(rows):
    name, smin, smax, e20, r20, e23, r23, d20, d23, s20, s23, scale_note = row

    n_e20 = norm(e20, smin, smax)
    n_r20 = norm(r20, smin, smax)
    n_e23 = norm(e23, smin, smax)
    n_r23 = norm(r23, smin, smax)

    # --- Column 1: variable name ----------------------------------------
    ax_l = fig.add_subplot(gs[i, 0])
    ax_l.axis("off")
    head, tail = name.split(":", 1)
    line1, line2 = head.strip() + ":", tail.strip()
    ax_l.text(0.98, 0.66, line1, ha="right", va="center",
              fontsize=10.0, fontweight="bold", color="#111", transform=ax_l.transAxes)
    ax_l.text(0.98, 0.43, line2, ha="right", va="center",
              fontsize=10.0, fontweight="bold", color="#111", transform=ax_l.transAxes)
    ax_l.text(0.98, 0.18, f"Scale {smin}–{smax}  {scale_note}".strip(),
              ha="right", va="center", fontsize=7.4, color="#666",
              style="italic", transform=ax_l.transAxes)

    # --- Column 2: dumbbell on shared 0-1 normalized axis ---------------
    ax = fig.add_subplot(gs[i, 1])

    Y_2020, Y_2023 = 1.0, 0.0

    ax.plot([min(n_e20, n_r20), max(n_e20, n_r20)], [Y_2020, Y_2020],
            color=LINE_2020, linestyle=(0, (3, 2)), linewidth=1.4, alpha=0.85, zorder=1)
    ax.plot([min(n_e23, n_r23), max(n_e23, n_r23)], [Y_2023, Y_2023],
            color=LINE_2023, linestyle="-", linewidth=1.6, alpha=0.95, zorder=1)

    ax.scatter([n_e20], [Y_2020], s=80, facecolors="white",
               edgecolors=EST, linewidths=1.7, zorder=3)
    ax.scatter([n_r20], [Y_2020], s=80, facecolors="white",
               edgecolors=RUS, linewidths=1.7, zorder=3)
    ax.scatter([n_e23], [Y_2023], s=85, color=EST, edgecolors="white",
               linewidths=0.8, zorder=3)
    ax.scatter([n_r23], [Y_2023], s=85, color=RUS, edgecolors="white",
               linewidths=0.8, zorder=3)

    OVERLAP_THRESHOLD_RAW = 0.30

    def place_pair(ne, nr, ve, vr, y, dy):
        close = abs(ve - vr) < OVERLAP_THRESHOLD_RAW
        nudge_y = +0.18 if dy > 0 else -0.18
        if close:
            if ne <= nr:
                left_n, left_v, left_c = ne, ve, EST
                right_n, right_v, right_c = nr, vr, RUS
            else:
                left_n, left_v, left_c = nr, vr, RUS
                right_n, right_v, right_c = ne, ve, EST
            ax.text(left_n - 0.012, y + nudge_y, f"{left_v:.2f}",
                    ha="right", va="center", fontsize=7.6,
                    color=left_c, fontweight="bold")
            ax.text(right_n + 0.012, y + nudge_y, f"{right_v:.2f}",
                    ha="left", va="center", fontsize=7.6,
                    color=right_c, fontweight="bold")
        else:
            ax.text(ne, y + dy, f"{ve:.2f}",
                    ha="center", va="center", fontsize=7.6,
                    color=EST, fontweight="bold")
            ax.text(nr, y + dy, f"{vr:.2f}",
                    ha="center", va="center", fontsize=7.6,
                    color=RUS, fontweight="bold")

    place_pair(n_e20, n_r20, e20, r20, Y_2020, +0.62)
    place_pair(n_e23, n_r23, e23, r23, Y_2023, -0.62)

    ax.text(0.005, Y_2020, "2020", ha="left", va="center",
            fontsize=7.6, color="#666", transform=ax.get_yaxis_transform())
    ax.text(0.005, Y_2023, "2023", ha="left", va="center",
            fontsize=7.8, color="#222", fontweight="bold",
            transform=ax.get_yaxis_transform())

    ax.set_xlim(-0.04, 1.04)
    ax.set_ylim(-1.1, 2.1)
    ax.set_yticks([])

    grid_positions = [0, 0.25, 0.5, 0.75, 1.0]
    for gp in grid_positions:
        is_bound = (gp == 0 or gp == 1)
        ax.axvline(gp,
                   color="#9ca3af" if is_bound else ("#d1d5db" if gp == 0.5 else "#e5e7eb"),
                   linewidth=0.9 if is_bound else (0.7 if gp == 0.5 else 0.5),
                   linestyle="-" if is_bound else ("--" if gp == 0.5 else (0, (1, 3))),
                   zorder=0)

    ax.set_xticks(grid_positions)

    if i == n - 1:
        ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
        ax.tick_params(axis="x", length=2.5, color="#888", labelsize=7.8,
                       pad=2, labelcolor="#444")
    else:
        ax.set_xticklabels([])
        ax.tick_params(axis="x", length=2.5, color="#888", labelbottom=False)

    for s_ in ("top", "right", "left"):
        ax.spines[s_].set_visible(False)
    ax.spines["bottom"].set_color("#cccccc")
    ax.spines["bottom"].set_linewidth(0.5)

    # --- Column 3: Cohen's d (per-year) ---------------------------------
    ax_r = fig.add_subplot(gs[i, 2])
    ax_r.axis("off")
    ax_r.text(0.05, 0.66, f"d = {d20:.2f} {s20}",
              ha="left", va="center", fontsize=8.4,
              color="#777" if s20 == "ns" else "#222",
              fontweight="normal" if s20 == "ns" else "bold",
              transform=ax_r.transAxes)
    ax_r.text(0.05, 0.34, f"d = {d23:.2f} {s23}",
              ha="left", va="center", fontsize=8.4,
              color="#777" if s23 == "ns" else "#222",
              fontweight="normal" if s23 == "ns" else "bold",
              transform=ax_r.transAxes)

# ---------- Title, subtitle, legend, footnote ----------
fig.text(0.03, 0.945,
         "Between-Group Difference in Intergroup Contact, 2020 and 2023",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.03, 0.905,
         "Estonian (blue) vs. Russian (amber) respondent means, normalized to each variable's theoretical scale range",
         fontsize=9, color="#444", ha="left")

est_dot = mlines.Line2D([], [], marker="o", color="white",
                        markerfacecolor=EST, markeredgecolor=EST,
                        markersize=8, linestyle="None", label="Estonian respondents")
rus_dot = mlines.Line2D([], [], marker="o", color="white",
                        markerfacecolor=RUS, markeredgecolor=RUS,
                        markersize=8, linestyle="None", label="Russian respondents")
y20 = mlines.Line2D([], [], marker="o", color=LINE_2020,
                    markerfacecolor="white", markeredgecolor="#666",
                    markersize=7, linestyle=(0, (3, 2)),
                    linewidth=1.4, label="2020 (open dots, dashed)")
y23 = mlines.Line2D([], [], marker="o", color=LINE_2023,
                    markerfacecolor="#444", markeredgecolor="#444",
                    markersize=7, linestyle="-",
                    linewidth=1.6, label="2023 (filled dots, solid)")
fig.legend(handles=[est_dot, rus_dot, y20, y23],
           loc="upper center", bbox_to_anchor=(0.5, 0.875),
           frameon=False, fontsize=8, handlelength=2.4,
           handleheight=1.0, ncol=4, columnspacing=2.2)

fig.text(0.50, 0.140,
         "Position on each variable's theoretical scale range (0% = scale minimum, 100% = scale maximum)",
         fontsize=8.5, color="#222", ha="center")

fig.text(0.03, 0.085,
         "Numeric labels on the dumbbells show the raw mean on each variable's natural scale (1–5).",
         fontsize=7.2, color="#555", ha="left")
fig.text(0.03, 0.055,
         "Both contact composites are inverted (higher = more contact); raw scale is 1 = almost daily, 5 = no contact.",
         fontsize=7.2, color="#555", ha="left")
fig.text(0.03, 0.025,
         "Cohen's d uses root-mean-square SD: " r"$d = (M_{Est} - M_{Rus}) / \sqrt{(SD_1^2 + SD_2^2)/2}$"
         ".  Significance: *** p<.001, ** p<.01, * p<.05, ns = not significant.",
         fontsize=7.2, color="#555", ha="left")

out_path = Path(__file__).parent.parent / "viz" / "fig_contact_d_dumbbell.jpg"
plt.savefig(out_path, dpi=300, format="jpg",
            facecolor="white", pil_kwargs={"quality": 95})
print(f"Saved: {out_path}")
