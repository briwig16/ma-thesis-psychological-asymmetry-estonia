"""
Distribution Shape — Primary vs. General Out-group SD (2020)
=============================================================
One figure containing:
  - Top row (1×2): composite-level KDEs, Primary vs. General overlaid per group
  - Middle row (2×3): item-level KDEs for Russian respondents, Primary vs. General per context
  - Bottom row (2×3): item-level KDEs for Estonian respondents, Primary vs. General per context

In 2020, Primary and General each have 3 items (one per social context).

  Group-specific Primary items:
    Estonians: K4X7_1 / K4X8_1 / K4X9_1   (rating Russian-speakers)
    Russians:  K4X7_2 / K4X8_2 / K4X9_2   (rating Estonian-speakers)

  Shared General items (both groups, 'new immigrants'):
    K4X7_3 / K4X8_3 / K4X9_3

Direction: scale 1–5, no reverse coding. Higher = more social distance.

Output: viz/fig_sd_primary_vs_general_2020.jpg  (300 DPI)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent

# ---------- Load 2020 data --------------------------------------------------
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


# ---------- Composites ------------------------------------------------------
est_pri = composite(df20[df20["ethnicity_binary"]==0], ["K4X7_1","K4X8_1","K4X9_1"])
est_gen = composite(df20[df20["ethnicity_binary"]==0], ["K4X7_3","K4X8_3","K4X9_3"])
rus_pri = composite(df20[df20["ethnicity_binary"]==1], ["K4X7_2","K4X8_2","K4X9_2"])
rus_gen = composite(df20[df20["ethnicity_binary"]==1], ["K4X7_3","K4X8_3","K4X9_3"])

# Items per context: (label, est_primary_code, rus_primary_code, general_code)
ITEMS = [
    ("Neighbors",          "K4X7_1", "K4X7_2", "K4X7_3"),
    ("Work / study",       "K4X8_1", "K4X8_2", "K4X8_3"),
    ("Marriage in family", "K4X9_1", "K4X9_2", "K4X9_3"),
]


def fetch(df, ethval, code):
    sub = df[df["ethnicity_binary"] == ethval]
    return to_num(sub[code])


# ---------- Diagnostics -----------------------------------------------------
print("="*92)
print("SD: PRIMARY vs. GENERAL — 2020 distribution shapes")
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
GEN_RUS = "#7c2d12"   # dark amber for General when group is Russian
GEN_EST = "#1e3a8a"   # dark navy for General when group is Estonian

fig = plt.figure(figsize=(13.5, 11.0), dpi=300)
gs = gridspec.GridSpec(3, 3, hspace=0.75, wspace=0.20,
                       left=0.06, right=0.985, top=0.85, bottom=0.09,
                       height_ratios=[1.3, 1.0, 1.0])


def kde_panel(ax, primary, general, color_pri, color_gen,
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


xg = np.linspace(0.8, 5.2, 400)

# ---- Top row: composite ----
ax_r = fig.add_subplot(gs[0, 0:3].subgridspec(1, 2, wspace=0.18)[0])
ax_e = fig.add_subplot(gs[0, 0:3].subgridspec(1, 2, wspace=0.18)[1], sharey=ax_r)

kde_panel(ax_r, rus_pri, rus_gen, RUS, GEN_RUS, xg,
          "Russian Primary (Estonian-speakers)",
          "Russian General (new immigrants)")
ax_r.set_title("Composite — Russian respondents (2020)",
               fontsize=11, fontweight="bold", loc="left")
ax_r.set_xlim(0.8, 5.2)
ax_r.set_xlabel("Score (1 = no distance, 5 = maximal distance)",
                fontsize=8.5, color="#444")
ax_r.set_ylabel("Density", fontsize=9, color="#444")
ax_r.legend(frameon=False, fontsize=8, loc="upper right")

kde_panel(ax_e, est_pri, est_gen, EST, GEN_EST, xg,
          "Estonian Primary (Russian-speakers)",
          "Estonian General (new immigrants)")
ax_e.set_title("Composite — Estonian respondents (2020)",
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
for col, (ctx, _, rus_pri_code, gen_code) in enumerate(ITEMS):
    ax = fig.add_subplot(gs[1, col])
    s_pri = fetch(df20, 1, rus_pri_code)
    s_gen = fetch(df20, 1, gen_code)
    kde_panel(ax, s_pri, s_gen, RUS, GEN_RUS, xg,
              f"Primary ({rus_pri_code})",
              f"General ({gen_code})")
    ax.set_title(f"Russian — {ctx}",
                 fontsize=10, fontweight="bold", loc="left", pad=6)
    ax.set_xlim(0.8, 5.2)
    if col == 0:
        ax.set_ylabel("Density", fontsize=9, color="#444")
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")


# ---- Bottom row: Estonian item-level ----
for col, (ctx, est_pri_code, _, gen_code) in enumerate(ITEMS):
    ax = fig.add_subplot(gs[2, col])
    s_pri = fetch(df20, 0, est_pri_code)
    s_gen = fetch(df20, 0, gen_code)
    kde_panel(ax, s_pri, s_gen, EST, GEN_EST, xg,
              f"Primary ({est_pri_code})",
              f"General ({gen_code})")
    ax.set_title(f"Estonian — {ctx}",
                 fontsize=10, fontweight="bold", loc="left", pad=6)
    ax.set_xlim(0.8, 5.2)
    ax.set_xlabel("Score (1 = no distance, 5 = maximal distance)",
                  fontsize=8, color="#444")
    if col == 0:
        ax.set_ylabel("Density", fontsize=9, color="#444")
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=8, color="#888")


# ---- Title and footer ------------------------------------------------------
fig.text(0.03, 0.965,
         "Social Distance: Primary vs. General Out-group — 2020",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.03, 0.940,
         "Top: composite-level distributions per group.  "
         "Middle: Russian item-level (Primary = Estonian-speakers, General = new immigrants).",
         fontsize=9, color="#444")
fig.text(0.03, 0.922,
         "Bottom: Estonian item-level (Primary = Russian-speakers, General = new immigrants).",
         fontsize=9, color="#444")
fig.text(0.03, 0.900,
         "Solid line = Primary out-group; dashed line = General out-group. Higher x = more social distance.",
         fontsize=8.5, color="#444")

fig.text(0.03, 0.012,
         "Bars = histogram density. Curves = Gaussian KDE. Dotted vertical lines mark each composite/item mean.",
         fontsize=7, color="#555")

out = ROOT / "viz" / "fig_sd_primary_vs_general_2020.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
