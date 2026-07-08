"""
Distribution Shape — Primary vs. General Out-group SD (2023)
=============================================================
Mirror of script 52, applied to the 2023 wave. The General out-group battery
expanded in 2023 from a single 'new immigrants' target to two targets ('other
Europeans' + 'non-Europeans') — so each context has TWO General items in 2023.

Layout:
  - Top row (1×2): composite-level KDEs, Primary vs. General overlaid per group
                   (General composite = mean of all 6 items, Eur + non-Eur)
  - Middle row (2×3): Russian item-level — each panel overlays the Primary item
                      with BOTH General sub-target items (other Eur + non-Eur)
  - Bottom row (2×3): Estonian item-level — same structure

Group-specific Primary items:
  Estonians: Q57_1 / Q58_1 / Q59_1   (rating Russian-speakers)
  Russians:  Q57_2 / Q58_2 / Q59_2   (rating Estonian-speakers)

Shared General items (both groups):
  Q57_4/Q57_5  (Neighbors: other Eur. / non-Eur.)
  Q58_4/Q58_5  (Work: other Eur. / non-Eur.)
  Q59_4/Q59_5  (Marriage: other Eur. / non-Eur.)

Direction: scale 1–5, no reverse coding. Higher = more social distance.

Output: viz/fig_sd_primary_vs_general_2023.jpg  (300 DPI)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent.parent

# ---------- Load 2023 data --------------------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).dropna().astype(float)

def composite(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    return sub.mean(axis=1, skipna=True).dropna()


# ---------- Composites ------------------------------------------------------
GEN_ITEMS = ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"]
est_pri = composite(df23[df23["ethnicity_binary"]==0], ["Q57_1","Q58_1","Q59_1"])
est_gen = composite(df23[df23["ethnicity_binary"]==0], GEN_ITEMS)
rus_pri = composite(df23[df23["ethnicity_binary"]==1], ["Q57_2","Q58_2","Q59_2"])
rus_gen = composite(df23[df23["ethnicity_binary"]==1], GEN_ITEMS)

# Items per context: (label, est_primary_code, rus_primary_code,
#                    general_other_eur_code, general_non_eur_code)
ITEMS = [
    ("Neighbors",          "Q57_1", "Q57_2", "Q57_4", "Q57_5"),
    ("Work / study",       "Q58_1", "Q58_2", "Q58_4", "Q58_5"),
    ("Marriage in family", "Q59_1", "Q59_2", "Q59_4", "Q59_5"),
]


def fetch(df, ethval, code):
    sub = df[df["ethnicity_binary"] == ethval]
    return to_num(sub[code])


# ---------- Diagnostics -----------------------------------------------------
print("="*92)
print("SD: PRIMARY vs. GENERAL — 2023 distribution shapes")
print("="*92)
for label, s in [("Rus Primary", rus_pri), ("Rus General", rus_gen),
                 ("Est Primary", est_pri), ("Est General", est_gen)]:
    print(f"  {label}: N={len(s):4d}  M={s.mean():.3f}  SD={s.std(ddof=1):.3f}")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

RUS = "#d97706"
EST = "#2563eb"
GEN_RUS_OE = "#7c2d12"   # dark amber — General other Eur (Russian)
GEN_RUS_NE = "#c2410c"   # mid amber  — General non-Eur (Russian)
GEN_EST_OE = "#1e3a8a"   # dark navy  — General other Eur (Estonian)
GEN_EST_NE = "#3b82f6"   # mid blue   — General non-Eur (Estonian)
# Composite General is a single distribution: use the dark variant.

fig = plt.figure(figsize=(13.5, 11.0), dpi=300)
gs = gridspec.GridSpec(3, 3, hspace=0.75, wspace=0.20,
                       left=0.06, right=0.985, top=0.85, bottom=0.09,
                       height_ratios=[1.3, 1.0, 1.0])


def composite_panel(ax, primary, general, color_pri, color_gen,
                    x_grid, label_pri, label_gen):
    bins = np.arange(min(x_grid)-0.05, max(x_grid)+0.05, 0.1)
    ax.hist(primary, bins=bins, density=True, alpha=0.18,
            color=color_pri, zorder=1)
    ax.hist(general, bins=bins, density=True, alpha=0.14,
            color=color_gen, zorder=1)
    if len(primary) > 5:
        k = stats.gaussian_kde(primary)
        ax.plot(x_grid, k(x_grid), color=color_pri, linewidth=1.8,
                linestyle="-", label=label_pri, zorder=3)
    if len(general) > 5:
        k = stats.gaussian_kde(general)
        ax.plot(x_grid, k(x_grid), color=color_gen, linewidth=1.6,
                linestyle=(0, (4, 2)), label=label_gen, zorder=3)
    ax.axvline(primary.mean(), color=color_pri, linewidth=0.9,
               linestyle=":", alpha=0.85, zorder=2)
    ax.axvline(general.mean(), color=color_gen, linewidth=0.9,
               linestyle=":", alpha=0.85, zorder=2)


def item_panel(ax, primary, gen_oe, gen_ne, color_pri, color_oe, color_ne,
               x_grid, label_pri, label_oe, label_ne):
    bins = np.arange(min(x_grid)-0.05, max(x_grid)+0.05, 0.1)
    ax.hist(primary, bins=bins, density=True, alpha=0.16,
            color=color_pri, zorder=1)
    if len(primary) > 5:
        k = stats.gaussian_kde(primary)
        ax.plot(x_grid, k(x_grid), color=color_pri, linewidth=1.8,
                linestyle="-", label=label_pri, zorder=3)
    if len(gen_oe) > 5:
        k = stats.gaussian_kde(gen_oe)
        ax.plot(x_grid, k(x_grid), color=color_oe, linewidth=1.4,
                linestyle=(0, (4, 2)), label=label_oe, zorder=3)
    if len(gen_ne) > 5:
        k = stats.gaussian_kde(gen_ne)
        ax.plot(x_grid, k(x_grid), color=color_ne, linewidth=1.4,
                linestyle=(0, (1, 2)), label=label_ne, zorder=3)
    ax.axvline(primary.mean(), color=color_pri, linewidth=0.9,
               linestyle=":", alpha=0.85, zorder=2)
    ax.axvline(gen_oe.mean(), color=color_oe, linewidth=0.7,
               linestyle=":", alpha=0.7, zorder=2)
    ax.axvline(gen_ne.mean(), color=color_ne, linewidth=0.7,
               linestyle=":", alpha=0.7, zorder=2)


xg = np.linspace(0.8, 5.2, 400)

# ---- Top row: composite ----
ax_r = fig.add_subplot(gs[0, 0:3].subgridspec(1, 2, wspace=0.18)[0])
ax_e = fig.add_subplot(gs[0, 0:3].subgridspec(1, 2, wspace=0.18)[1], sharey=ax_r)

composite_panel(ax_r, rus_pri, rus_gen, RUS, GEN_RUS_OE, xg,
                "Russian Primary (Estonian-speakers)",
                "Russian General (Eur + non-Eur, mean)")
ax_r.set_title("Composite — Russian respondents (2023)",
               fontsize=11, fontweight="bold", loc="left")
ax_r.set_xlim(0.8, 5.2)
ax_r.set_xlabel("Score (1 = no distance, 5 = maximal distance)",
                fontsize=8.5, color="#444")
ax_r.set_ylabel("Density", fontsize=9, color="#444")
ax_r.legend(frameon=False, fontsize=8, loc="upper right")

composite_panel(ax_e, est_pri, est_gen, EST, GEN_EST_OE, xg,
                "Estonian Primary (Russian-speakers)",
                "Estonian General (Eur + non-Eur, mean)")
ax_e.set_title("Composite — Estonian respondents (2023)",
               fontsize=11, fontweight="bold", loc="left")
ax_e.set_xlim(0.8, 5.2)
ax_e.set_xlabel("Score (1 = no distance, 5 = maximal distance)",
                fontsize=8.5, color="#444")
ax_e.legend(frameon=False, fontsize=8, loc="upper right")

for ax in (ax_r, ax_e):
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")


# ---- Middle row: Russian item-level ----
for col, (ctx, _, rus_pri_code, gen_oe_code, gen_ne_code) in enumerate(ITEMS):
    ax = fig.add_subplot(gs[1, col])
    s_pri = fetch(df23, 1, rus_pri_code)
    s_oe = fetch(df23, 1, gen_oe_code)
    s_ne = fetch(df23, 1, gen_ne_code)
    item_panel(ax, s_pri, s_oe, s_ne, RUS, GEN_RUS_OE, GEN_RUS_NE, xg,
               f"Primary ({rus_pri_code})",
               f"General other-Eur ({gen_oe_code})",
               f"General non-Eur ({gen_ne_code})")
    ax.set_title(f"Russian — {ctx}",
                 fontsize=10, fontweight="bold", loc="left", pad=6)
    ax.set_xlim(0.8, 5.2)
    if col == 0:
        ax.set_ylabel("Density", fontsize=9, color="#444")
    ax.legend(frameon=False, fontsize=7, loc="upper right")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")


# ---- Bottom row: Estonian item-level ----
for col, (ctx, est_pri_code, _, gen_oe_code, gen_ne_code) in enumerate(ITEMS):
    ax = fig.add_subplot(gs[2, col])
    s_pri = fetch(df23, 0, est_pri_code)
    s_oe = fetch(df23, 0, gen_oe_code)
    s_ne = fetch(df23, 0, gen_ne_code)
    item_panel(ax, s_pri, s_oe, s_ne, EST, GEN_EST_OE, GEN_EST_NE, xg,
               f"Primary ({est_pri_code})",
               f"General other-Eur ({gen_oe_code})",
               f"General non-Eur ({gen_ne_code})")
    ax.set_title(f"Estonian — {ctx}",
                 fontsize=10, fontweight="bold", loc="left", pad=6)
    ax.set_xlim(0.8, 5.2)
    ax.set_xlabel("Score (1 = no distance, 5 = maximal distance)",
                  fontsize=8, color="#444")
    if col == 0:
        ax.set_ylabel("Density", fontsize=9, color="#444")
    ax.legend(frameon=False, fontsize=7, loc="upper right")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")


# ---- Title and footer ------------------------------------------------------
fig.text(0.03, 0.965,
         "Social Distance: Primary vs. General Out-group — 2023",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.03, 0.940,
         "Top: composite-level distributions per group.  "
         "Middle: Russian item-level (Primary = Estonian-speakers, General split into other-Eur. and non-Eur.).",
         fontsize=9, color="#444")
fig.text(0.03, 0.922,
         "Bottom: Estonian item-level (Primary = Russian-speakers, General split into other-Eur. and non-Eur.).",
         fontsize=9, color="#444")
fig.text(0.03, 0.900,
         "Solid line = Primary out-group; long-dashed = General other-Eur.; dotted = General non-Eur. Higher x = more social distance.",
         fontsize=8.5, color="#444")

fig.text(0.03, 0.012,
         "Bars = histogram density (Primary only, for legibility). Curves = Gaussian KDE. Dotted vertical lines mark each item/composite mean.",
         fontsize=7, color="#555")

out = ROOT / "viz" / "fig_sd_primary_vs_general_2023.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
