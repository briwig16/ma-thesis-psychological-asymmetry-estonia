"""
Social Distance: General Out-group — Item-Level Distribution Shapes
=====================================================================
Layout (4 rows × 3 columns) — handles the differing item sets:

  Columns = social context (Neighbors, Work / study, Marriage in family)

  Row 1: Russian respondents — 2023 'other Europeans' (Q57_4 / Q58_4 / Q59_4),
         with 2020 'new immigrants' (K4X7_3 / K4X8_3 / K4X9_3) overlaid as baseline
  Row 2: Russian respondents — 2023 'non-Europeans' (Q57_5 / Q58_5 / Q59_5),
         with 2020 'new immigrants' overlaid as baseline
  Row 3: Estonian respondents — 2023 'other Europeans', with 2020 baseline
  Row 4: Estonian respondents — 2023 'non-Europeans',  with 2020 baseline

The same 2020 'new immigrants' item is overlaid twice per group/context so the
viewer can see how the single 2020 immigrant target split into two 2023
sub-targets (other Europeans vs. non-Europeans).

Direction: scale 1–5, no reverse coding. Higher = more social distance.

Output: viz/fig_sd_general_item_density.jpg  (300 DPI)
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadstat
from scipy import stats

ROOT = Path(__file__).parent.parent

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


# Columns: (label, 2020 item, 2023 'other Europeans' item, 2023 'non-Europeans' item)
COLUMNS = [
    ("Neighbors",         "K4X7_3", "Q57_4", "Q57_5"),
    ("Work / study",      "K4X8_3", "Q58_4", "Q58_5"),
    ("Marriage",          "K4X9_3", "Q59_4", "Q59_5"),
]


def fetch(df, ethval, code):
    sub = df[df["ethnicity_binary"] == ethval]
    return to_num(sub[code])


# ---------- Diagnostics -----------------------------------------------------
print("="*92)
print("SD: GENERAL OUT-GROUP — item-level diagnostics")
print("(All items: higher = more social distance, scale 1-5)")
print("="*92)
for ctx, c20, c23a, c23b in COLUMNS:
    print(f"\n  Context: {ctx}")
    for grp, ev in [("Russian", 1), ("Estonian", 0)]:
        s20 = fetch(df20, ev, c20)
        s23a = fetch(df23, ev, c23a)
        s23b = fetch(df23, ev, c23b)
        print(f"    {grp:<8s} 2020 {c20:<7s}: N={len(s20):4d}  M={s20.mean():.3f}  SD={s20.std(ddof=1):.3f}")
        print(f"    {grp:<8s} 2023 {c23a:<7s} (other Eur): N={len(s23a):4d}  M={s23a.mean():.3f}  SD={s23a.std(ddof=1):.3f}")
        print(f"    {grp:<8s} 2023 {c23b:<7s} (non-Eur):   N={len(s23b):4d}  M={s23b.mean():.3f}  SD={s23b.std(ddof=1):.3f}")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

LINE_2020 = "#9ca3af"
RUS = "#d97706"
EST = "#2563eb"

fig, axes = plt.subplots(4, 3, figsize=(14.0, 12.5), dpi=300, sharey="row")

xg = np.linspace(0.5, 5.5, 500)
bin_edges = np.array([0.5, 1.5, 2.5, 3.5, 4.5, 5.5])
centers = np.array([1, 2, 3, 4, 5], dtype=float)
BAR_W = 0.33


def panel(ax, s2020, s2023, color2023, label2020, label2023):
    h20, _ = np.histogram(s2020, bins=bin_edges, density=True)
    h23, _ = np.histogram(s2023, bins=bin_edges, density=True)
    ax.bar(centers, h20, width=BAR_W, align="center",
           color=LINE_2020, alpha=0.55, edgecolor="none", zorder=1)
    ax.bar(centers, h23, width=BAR_W, align="center",
           color=color2023, alpha=0.50, edgecolor="none", zorder=2)
    if len(s2020) > 5:
        k = stats.gaussian_kde(s2020)
        ax.plot(xg, k(xg), color=LINE_2020, linewidth=1.4,
                linestyle=(0, (3, 2)), label=label2020, zorder=3)
    if len(s2023) > 5:
        k = stats.gaussian_kde(s2023)
        ax.plot(xg, k(xg), color=color2023, linewidth=1.6,
                linestyle="-", label=label2023, zorder=3)
    ax.axvline(s2020.mean(), color=LINE_2020, linewidth=0.9,
               linestyle=":", alpha=0.7, zorder=2)
    ax.axvline(s2023.mean(), color=color2023, linewidth=0.9,
               linestyle=":", alpha=0.9, zorder=2)


# Row config: (target_year_label, eth_value, base_color, label_2023_target_kind)
ROW_CONFIG = [
    ("Russian — other Europeans (2023)",   1, RUS, "other Eur."),
    ("Russian — non-Europeans (2023)",     1, RUS, "non-Eur."),
    ("Estonian — other Europeans (2023)",  0, EST, "other Eur."),
    ("Estonian — non-Europeans (2023)",    0, EST, "non-Eur."),
]

for row_i, (row_title, eth_val, color, target_kind) in enumerate(ROW_CONFIG):
    for col_j, (ctx, c20, c23a, c23b) in enumerate(COLUMNS):
        ax = axes[row_i, col_j]
        s2020 = fetch(df20, eth_val, c20)
        c23 = c23a if target_kind == "other Eur." else c23b
        s2023 = fetch(df23, eth_val, c23)

        grp_lbl = "Russian" if eth_val == 1 else "Estonian"
        panel(ax, s2020, s2023, color,
              f"{grp_lbl} 2020 (new immigrants)",
              f"{grp_lbl} 2023 ({target_kind})")

        if row_i == 0:
            ax.set_title(f"{ctx}",
                         fontsize=10.5, fontweight="bold", loc="left", pad=12)
        # left-edge row label
        if col_j == 0:
            ax.set_ylabel(f"Density\n{row_title}",
                          fontsize=8.5, color="#444",
                          linespacing=1.4)
        ax.set_xlim(0.4, 5.6)
        ax.set_xticks([1, 2, 3, 4, 5])
        ax.set_xticklabels(["1", "2", "3", "4", "5"])
        if row_i == 3:
            ax.set_xlabel("Score (1 = no distance, 5 = maximal distance)",
                          fontsize=8, color="#444")
        ax.legend(frameon=False, fontsize=7, loc="upper right")
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.tick_params(axis="both", labelsize=8, color="#888")
        # small item-code annotation in the corner
        ax.text(0.02, 0.97, f"{c20} → {c23}",
                transform=ax.transAxes, fontsize=7, color="#666",
                ha="left", va="top")


# Title and footer
fig.text(0.03, 0.975,
         "SD: General Out-group — Item-Level Distribution Shapes 2020 → 2023",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.03, 0.957,
         "Rows split each respondent group by 2023 target (other Europeans vs. non-Europeans).",
         fontsize=8.5, color="#444")
fig.text(0.03, 0.943,
         "2020 baseline = the single 'new immigrants' item in each context, repeated across both 2023 sub-targets.",
         fontsize=8.5, color="#444")
fig.text(0.03, 0.925,
         "CAVEAT: 2020 measured social distance from a single 'new immigrants' target; 2023 split this into 'other Europeans' and 'non-Europeans'.",
         fontsize=8, color="#a0522d", style="italic")
fig.text(0.03, 0.911,
         "Cross-year comparison is suggestive, not strict.",
         fontsize=8, color="#a0522d", style="italic")

fig.text(0.03, 0.012,
         "Bars are histogram density, curves are Gaussian KDE. Dotted vertical lines mark each year's mean.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.10, right=0.985, top=0.88, bottom=0.07,
                    wspace=0.22, hspace=0.75)

out = ROOT / "viz" / "fig_sd_general_item_density.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
