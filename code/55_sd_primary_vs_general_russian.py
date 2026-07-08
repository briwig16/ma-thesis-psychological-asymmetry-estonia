"""
Distribution Shape — Russian Primary vs. General Out-group SD (2020 + 2023)
=============================================================================
Mirror of script 54, focused on Russian respondents.

Layout:
  - Top row (1×2): composite — 2020 (left) vs. 2023 (right), Primary vs. General overlaid
  - Middle row (1×3): item-level 2020 — Neighbors / Work / Marriage
                      Each panel: Primary (Estonian-speakers) vs. General (new immigrants)
  - Bottom row (1×3): item-level 2023 — same contexts
                      Each panel: Primary vs. General other-Eur. vs. General non-Eur.

Russian Primary items (rating Estonian-speakers):
  2020: K4X7_2 / K4X8_2 / K4X9_2
  2023: Q57_2 / Q58_2 / Q59_2

Shared General items:
  2020: K4X7_3 / K4X8_3 / K4X9_3   (single 'new immigrants' target)
  2023: Q57_4 / Q57_5 / Q58_4 / Q58_5 / Q59_4 / Q59_5

Direction: scale 1–5, no reverse coding. Higher = more social distance.

Output: viz/fig_sd_primary_vs_general_russian.jpg  (300 DPI)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent

# ---------- Load both waves --------------------------------------------------
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

def composite(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    return sub.mean(axis=1, skipna=True).dropna()


# ---------- Russian composites ---------------------------------------------
rus_pri_2020 = composite(df20[df20["ethnicity_binary"]==1], ["K4X7_2","K4X8_2","K4X9_2"])
rus_gen_2020 = composite(df20[df20["ethnicity_binary"]==1], ["K4X7_3","K4X8_3","K4X9_3"])
rus_pri_2023 = composite(df23[df23["ethnicity_binary"]==1], ["Q57_2","Q58_2","Q59_2"])
rus_gen_2023 = composite(df23[df23["ethnicity_binary"]==1],
                         ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"])

ITEMS_2020 = [   # (label, rus_pri_code, gen_code)
    ("Neighbors",          "K4X7_2", "K4X7_3"),
    ("Work / study",       "K4X8_2", "K4X8_3"),
    ("Marriage in family", "K4X9_2", "K4X9_3"),
]
ITEMS_2023 = [   # (label, rus_pri_code, gen_oe_code, gen_ne_code)
    ("Neighbors",          "Q57_2", "Q57_4", "Q57_5"),
    ("Work / study",       "Q58_2", "Q58_4", "Q58_5"),
    ("Marriage in family", "Q59_2", "Q59_4", "Q59_5"),
]


def fetch(df, ethval, code):
    sub = df[df["ethnicity_binary"] == ethval]
    return to_num(sub[code])


# ---------- Diagnostics -----------------------------------------------------
print("="*92)
print("RUSSIAN respondents — SD Primary vs. General, 2020 + 2023")
print("="*92)
for label, s in [("Pri 2020", rus_pri_2020), ("Gen 2020", rus_gen_2020),
                 ("Pri 2023", rus_pri_2023), ("Gen 2023", rus_gen_2023)]:
    print(f"  {label}: N={len(s):4d}  M={s.mean():.3f}  SD={s.std(ddof=1):.3f}")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

RUS = "#d97706"          # Primary line (Russian = orange)
GEN_DARK = "#7c2d12"     # General (single line in 2020; "other Eur" in 2023)
GEN_MID  = "#c2410c"     # General "non-Eur" in 2023

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


def item_panel_2020(ax, primary, general, color_pri, color_gen,
                    x_grid, label_pri, label_gen):
    composite_panel(ax, primary, general, color_pri, color_gen,
                    x_grid, label_pri, label_gen)


def item_panel_2023(ax, primary, gen_oe, gen_ne, color_pri, color_oe, color_ne,
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

# ---- Top row: composite — 2020 vs 2023 ----
ax_2020 = fig.add_subplot(gs[0, 0:3].subgridspec(1, 2, wspace=0.18)[0])
ax_2023 = fig.add_subplot(gs[0, 0:3].subgridspec(1, 2, wspace=0.18)[1], sharey=ax_2020)

composite_panel(ax_2020, rus_pri_2020, rus_gen_2020, RUS, GEN_DARK, xg,
                "Primary (Estonian-speakers)",
                "General (new immigrants)")
ax_2020.set_title("Composite — 2020", fontsize=11, fontweight="bold", loc="left")
ax_2020.set_xlim(0.8, 5.2)
ax_2020.set_xlabel("Score (1 = no distance, 5 = maximal distance)",
                   fontsize=8.5, color="#444")
ax_2020.set_ylabel("Density", fontsize=9, color="#444")
ax_2020.legend(frameon=False, fontsize=8, loc="upper right")

composite_panel(ax_2023, rus_pri_2023, rus_gen_2023, RUS, GEN_DARK, xg,
                "Primary (Estonian-speakers)",
                "General (Eur + non-Eur, mean)")
ax_2023.set_title("Composite — 2023", fontsize=11, fontweight="bold", loc="left")
ax_2023.set_xlim(0.8, 5.2)
ax_2023.set_xlabel("Score (1 = no distance, 5 = maximal distance)",
                   fontsize=8.5, color="#444")
ax_2023.legend(frameon=False, fontsize=8, loc="upper right")

for ax in (ax_2020, ax_2023):
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")


# ---- Middle row: item-level 2020 ----
for col, (ctx, pri_code, gen_code) in enumerate(ITEMS_2020):
    ax = fig.add_subplot(gs[1, col])
    s_pri = fetch(df20, 1, pri_code)
    s_gen = fetch(df20, 1, gen_code)
    item_panel_2020(ax, s_pri, s_gen, RUS, GEN_DARK, xg,
                    f"Primary ({pri_code})",
                    f"General ({gen_code})")
    ax.set_title(f"2020 — {ctx}",
                 fontsize=10, fontweight="bold", loc="left", pad=6)
    ax.set_xlim(0.8, 5.2)
    if col == 0:
        ax.set_ylabel("Density", fontsize=9, color="#444")
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")


# ---- Bottom row: item-level 2023 ----
for col, (ctx, pri_code, gen_oe_code, gen_ne_code) in enumerate(ITEMS_2023):
    ax = fig.add_subplot(gs[2, col])
    s_pri = fetch(df23, 1, pri_code)
    s_oe = fetch(df23, 1, gen_oe_code)
    s_ne = fetch(df23, 1, gen_ne_code)
    item_panel_2023(ax, s_pri, s_oe, s_ne, RUS, GEN_DARK, GEN_MID, xg,
                    f"Primary ({pri_code})",
                    f"General other-Eur ({gen_oe_code})",
                    f"General non-Eur ({gen_ne_code})")
    ax.set_title(f"2023 — {ctx}",
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
         "Russian respondents — Social Distance: Primary vs. General Out-group (2020 vs. 2023)",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.03, 0.940,
         "Top: composite-level distributions, 2020 (left) vs. 2023 (right).  "
         "Middle: 2020 item-level (Primary = Estonian-speakers, General = new immigrants).",
         fontsize=9, color="#444")
fig.text(0.03, 0.922,
         "Bottom: 2023 item-level (Primary = Estonian-speakers, General split into other-Eur. and non-Eur.).",
         fontsize=9, color="#444")
fig.text(0.03, 0.900,
         "Solid line = Primary out-group; long-dashed = General (or General other-Eur. in 2023); dotted = General non-Eur. (2023 only). Higher x = more social distance.",
         fontsize=8.5, color="#444")

fig.text(0.03, 0.012,
         "Bars = histogram density. Curves = Gaussian KDE. Dotted vertical lines mark each composite/item mean.",
         fontsize=7, color="#555")

out = ROOT / "viz" / "fig_sd_primary_vs_general_russian.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
