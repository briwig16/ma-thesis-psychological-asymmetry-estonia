"""
Item-level breakdown of the two contact composites.

Each composite (Contact with Estonian speakers, Contact with Russian speakers)
is the mean of 6 context items: work/school, neighbors, internet/social media,
leisure, family, friends. This figure shows each context as its own dumbbell so
that the heterogeneity inside the composite is visible.

Layout: two stacked panels, each with 6 rows.
- Top panel: Contact with Estonian Speakers (Q51 in 2023, K4X1 in 2020)
- Bottom panel: Contact with Russian Speakers (Q52 in 2023, K4X2 in 2020)
- Each row: 2020 dumbbell (open dots, dashed) above 2023 dumbbell (filled, solid)
- Values inverted (6 - raw) so higher = more contact, matching the dumbbell chart.
- X-axis: raw 1-5 contact scale.

Outputs viz/fig_contact_breakdown.jpg at 300 DPI.
"""

import pandas as pd
import pyreadstat
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.lines as mlines
from pathlib import Path

# ---------- Load data and compute item-level means -----------------------
ROOT = Path(__file__).parent.parent

df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda row: 0 if row.get("T9_1") == 1 else (1 if row.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()

contexts = ["Work / school", "Neighbors", "Internet / social media",
            "Leisure", "Family / relatives", "Friends"]

def cell_means(var23_prefix, var20_prefix):
    """Return list of dicts with means for each of the 6 contexts."""
    out = []
    for j, ctx in enumerate(contexts, 1):
        v23 = f"{var23_prefix}_{j}"
        v20 = f"{var20_prefix}_{j}"
        s23 = df23[v23].replace(9, pd.NA)
        s20 = df20[v20].replace(9, pd.NA)
        out.append({
            "context": ctx,
            "e20": s20[df20["ethnicity_binary"] == 0].mean(),
            "r20": s20[df20["ethnicity_binary"] == 1].mean(),
            "e23": s23[df23["ethnicity_binary"] == 0].mean(),
            "r23": s23[df23["ethnicity_binary"] == 1].mean(),
        })
    return out

q51 = cell_means("Q51", "K4X1")    # Contact with Estonian speakers
q52 = cell_means("Q52", "K4X2")    # Contact with Russian speakers

# Invert raw means so higher = more contact (raw scale: 1 = every day, 5 = none)
def invert(rows):
    for r in rows:
        for k in ("e20", "r20", "e23", "r23"):
            r[k + "_inv"] = 6 - r[k]
    return rows

q51 = invert(q51)
q52 = invert(q52)

# ---------- Style --------------------------------------------------------
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

n_per = len(contexts)
fig = plt.figure(figsize=(9.0, 11.0), dpi=300)

# Outer 2-row grid: top = Q51 panel, bottom = Q52 panel.
# Top is pulled down from 0.91 to 0.87 to leave room above each panel for its
# header text. hspace is increased so the Q52 header has space between panels.
outer = gridspec.GridSpec(
    2, 1, height_ratios=[1, 1], hspace=0.30,
    left=0.04, right=0.985, top=0.87, bottom=0.085
)

def draw_panel(panel_gs, panel_title, panel_subtitle, rows, panel_y_top):
    inner = gridspec.GridSpecFromSubplotSpec(
        n_per, 3, subplot_spec=panel_gs,
        width_ratios=[1.4, 4.0, 1.0],
        wspace=0.10, hspace=0.55
    )

    # Panel header (placed in figure coords, aligned to inner grid top)
    fig.text(0.04, panel_y_top, panel_title,
             fontsize=11.5, fontweight="bold", ha="left", color="#111")
    fig.text(0.04, panel_y_top - 0.018, panel_subtitle,
             fontsize=8.5, color="#555", ha="left", style="italic")

    for i, row in enumerate(rows):
        ctx = row["context"]
        n_e20 = row["e20_inv"]; n_r20 = row["r20_inv"]
        n_e23 = row["e23_inv"]; n_r23 = row["r23_inv"]

        # --- Column 1: context name -------------------------------
        ax_l = fig.add_subplot(inner[i, 0])
        ax_l.axis("off")
        ax_l.text(0.97, 0.55, ctx, ha="right", va="center",
                  fontsize=9.4, fontweight="bold", color="#111",
                  transform=ax_l.transAxes)

        # --- Column 2: dumbbell -----------------------------------
        ax = fig.add_subplot(inner[i, 1])
        Y_2020, Y_2023 = 1.0, 0.0

        ax.plot([min(n_e20, n_r20), max(n_e20, n_r20)], [Y_2020, Y_2020],
                color=LINE_2020, linestyle=(0, (3, 2)), linewidth=1.4, alpha=0.85, zorder=1)
        ax.plot([min(n_e23, n_r23), max(n_e23, n_r23)], [Y_2023, Y_2023],
                color=LINE_2023, linestyle="-", linewidth=1.6, alpha=0.95, zorder=1)

        ax.scatter([n_e20], [Y_2020], s=70, facecolors="white",
                   edgecolors=EST, linewidths=1.7, zorder=3)
        ax.scatter([n_r20], [Y_2020], s=70, facecolors="white",
                   edgecolors=RUS, linewidths=1.7, zorder=3)
        ax.scatter([n_e23], [Y_2023], s=78, color=EST, edgecolors="white",
                   linewidths=0.8, zorder=3)
        ax.scatter([n_r23], [Y_2023], s=78, color=RUS, edgecolors="white",
                   linewidths=0.8, zorder=3)

        # Numeric labels — overlap-aware
        OVERLAP = 0.30
        def place_pair(ne, nr, y, dy):
            close = abs(ne - nr) < OVERLAP
            nudge_y = +0.18 if dy > 0 else -0.18
            if close:
                if ne <= nr:
                    lx, lc, rx, rc = ne, EST, nr, RUS
                else:
                    lx, lc, rx, rc = nr, RUS, ne, EST
                ax.text(lx - 0.06, y + nudge_y, f"{lx:.2f}",
                        ha="right", va="center", fontsize=7.2,
                        color=lc, fontweight="bold")
                ax.text(rx + 0.06, y + nudge_y, f"{rx:.2f}",
                        ha="left", va="center", fontsize=7.2,
                        color=rc, fontweight="bold")
            else:
                ax.text(ne, y + dy, f"{ne:.2f}",
                        ha="center", va="center", fontsize=7.2,
                        color=EST, fontweight="bold")
                ax.text(nr, y + dy, f"{nr:.2f}",
                        ha="center", va="center", fontsize=7.2,
                        color=RUS, fontweight="bold")

        place_pair(n_e20, n_r20, Y_2020, +0.62)
        place_pair(n_e23, n_r23, Y_2023, -0.62)

        # Year labels at left edge
        ax.text(0.005, Y_2020, "2020", ha="left", va="center",
                fontsize=7.2, color="#666", transform=ax.get_yaxis_transform())
        ax.text(0.005, Y_2023, "2023", ha="left", va="center",
                fontsize=7.4, color="#222", fontweight="bold",
                transform=ax.get_yaxis_transform())

        # X-axis: contact scale (inverted), 1 = no contact, 5 = every day
        ax.set_xlim(0.85, 5.15)
        ax.set_ylim(-1.1, 2.1)
        ax.set_yticks([])

        xticks = [1, 2, 3, 4, 5]
        ax.set_xticks(xticks)

        for xt in xticks:
            ax.axvline(xt, color="#e5e7eb", linewidth=0.5, zorder=0)

        # Tick labels only on the bottom-most row of each panel
        if i == n_per - 1:
            ax.set_xticklabels(["1\nnone", "2", "3", "4", "5\ndaily"])
            ax.tick_params(axis="x", length=2.5, color="#888", labelsize=7,
                           pad=2, labelcolor="#666")
        else:
            ax.set_xticklabels([])
            ax.tick_params(axis="x", length=2.5, color="#888", labelbottom=False)

        for s_ in ("top", "right", "left"):
            ax.spines[s_].set_visible(False)
        ax.spines["bottom"].set_color("#cccccc")
        ax.spines["bottom"].set_linewidth(0.5)

        # --- Column 3: gap (raw difference, in scale units) -----
        ax_r = fig.add_subplot(inner[i, 2])
        ax_r.axis("off")
        gap20 = abs(n_e20 - n_r20)
        gap23 = abs(n_e23 - n_r23)
        ax_r.text(0.05, 0.66, f"gap = {gap20:.2f}",
                  ha="left", va="center", fontsize=8.0,
                  color="#222", fontweight="bold",
                  transform=ax_r.transAxes)
        ax_r.text(0.05, 0.34, f"gap = {gap23:.2f}",
                  ha="left", va="center", fontsize=8.0,
                  color="#222", fontweight="bold",
                  transform=ax_r.transAxes)

# Title block
fig.text(0.04, 0.965,
         "Contact Composites Broken Down by Context",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.04, 0.946,
         "Each composite is the mean of six contexts shown below. Higher = more frequent contact (inverted from raw 1=daily, 5=never).",
         fontsize=9, color="#444", ha="left")

# Shared legend
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
           loc="upper center", bbox_to_anchor=(0.5, 0.928),
           frameon=False, fontsize=8, handlelength=2.4,
           handleheight=1.0, ncol=4, columnspacing=2.2)

# Draw the two panels — y_top sits ABOVE each panel's grid area.
# Top panel grid ends at outer.top = 0.87, so Q51 header at 0.895.
# Bottom panel grid ends at ~0.46 (with hspace=0.30), so Q52 header at 0.475.
draw_panel(outer[0],
           "Contact with Estonian speakers",
           "Q51 (2023) / K4X1 (2020) — by social context",
           q51, panel_y_top=0.895)
draw_panel(outer[1],
           "Contact with Russian speakers",
           "Q52 (2023) / K4X2 (2020) — by social context",
           q52, panel_y_top=0.473)

# Footnote
fig.text(0.04, 0.026,
         "Means are inverted from the raw 1–5 scale (raw: 1 = almost every day, 5 = have not communicated) so that rightward = more contact.",
         fontsize=7.0, color="#555", ha="left")
fig.text(0.04, 0.012,
         "'Gap' is the raw between-group difference in inverted means for that context, in scale units.",
         fontsize=7.0, color="#555", ha="left")

out_path = ROOT / "viz" / "fig_contact_breakdown.jpg"
plt.savefig(out_path, dpi=300, format="jpg",
            facecolor="white", pil_kwargs={"quality": 95})
print(f"Saved: {out_path}")
