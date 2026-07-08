"""
Polarization Density Plots — Blindspot FLAG #1
================================================
Investigates the within-Russian SD increases on Superordinate Identity
(0.66 -> 0.79) and Group ID Patterns (0.81 -> 0.84) flagged in the
Blindspot Report (2026-04-29). Increasing dispersion without a mean shift
is the signature of within-group polarization.

Produces a KDE/histogram density figure for both groups, both years, on
the two variables where the Russian SD grew between waves. If the 2023
distribution is bimodal (or has heavier tails than 2020), the "Russians
integrating" framing needs to be qualified.

Outputs:
  viz/fig_polarization_density.jpg  (300 DPI, paper-style)
"""

from pathlib import Path

import matplotlib.pyplot as plt
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


# ---------- Composites (inverted, matching dumbbell convention) -----------
def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk)

def superord(df, items, reverse_item, scale_max=4):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != 9)
    sub[reverse_item] = (scale_max + 1) - sub[reverse_item]
    raw = sub.mean(axis=1, skipna=True)
    return (scale_max + 1) - raw   # invert composite

def group_id(df, var, dk):
    return to_num(df[var], dk=dk)


def get_series(group_code, year):
    """Return (superord_inv, group_id) for one group-year cell."""
    if year == 2023:
        d = df23[df23["ethnicity_binary"] == group_code]
        s = superord(d, ["Q67_2","Q67_4","Q67_5"], "Q67_4", scale_max=4)
        g = group_id(d, "Q66", dk=9)
    else:
        d = df20[df20["ethnicity_binary"] == group_code]
        s = superord(d, ["K6X5_2","K6X5_3","K6X5_4"], "K6X5_3", scale_max=4)
        g = group_id(d, "K6X4", dk=6)   # 2020 DK code differs
    return s.dropna(), g.dropna()


est20_s, est20_g = get_series(0, 2020)
est23_s, est23_g = get_series(0, 2023)
rus20_s, rus20_g = get_series(1, 2020)
rus23_s, rus23_g = get_series(1, 2023)


# ---------- Quantitative polarization diagnostics -------------------------
def polarization(s):
    """SD, IQR, skew, kurtosis."""
    return {
        "M":    s.mean(),
        "SD":   s.std(ddof=1),
        "IQR":  s.quantile(.75) - s.quantile(.25),
        "skew": stats.skew(s, bias=False),
        "kurt": stats.kurtosis(s, bias=False, fisher=True),
        "N":    len(s),
    }

print("="*92)
print("POLARIZATION DIAGNOSTICS (Russian respondents — focus group for SD increase flag)")
print("="*92)

print("\nSuperordinate Identity (inverted, range 1-4 high=more belonging)")
for label, s in [("Rus 2020", rus20_s), ("Rus 2023", rus23_s),
                 ("Est 2020", est20_s), ("Est 2023", est23_s)]:
    p = polarization(s)
    print(f"  {label}: N={p['N']:4d}  M={p['M']:.3f}  SD={p['SD']:.3f}  "
          f"IQR={p['IQR']:.3f}  skew={p['skew']:+.3f}  kurt(excess)={p['kurt']:+.3f}")

print("\nGroup ID Patterns (1-5, high=more Estonian identity)")
for label, s in [("Rus 2020", rus20_g), ("Rus 2023", rus23_g),
                 ("Est 2020", est20_g), ("Est 2023", est23_g)]:
    p = polarization(s)
    print(f"  {label}: N={p['N']:4d}  M={p['M']:.3f}  SD={p['SD']:.3f}  "
          f"IQR={p['IQR']:.3f}  skew={p['skew']:+.3f}  kurt(excess)={p['kurt']:+.3f}")

# Levene's test for equality of variance (Russians 2020 vs 2023)
lev_s = stats.levene(rus20_s, rus23_s, center="median").pvalue
lev_g = stats.levene(rus20_g, rus23_g, center="median").pvalue
print(f"\nLevene's test (Russians, 2020 vs 2023):")
print(f"  Superordinate Identity: p = {lev_s:.4f}  ({'sig variance change' if lev_s < .05 else 'no sig variance change'})")
print(f"  Group ID Patterns:      p = {lev_g:.4f}  ({'sig variance change' if lev_g < .05 else 'no sig variance change'})")


# ---------- Plot ---------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST = "#2563eb"
RUS = "#d97706"
LINE_2020 = "#9ca3af"
LINE_2023 = "#1f2937"

fig, axes = plt.subplots(2, 2, figsize=(8.5, 6.0), dpi=300, sharey="row")

def kde_overlay(ax, s2020, s2023, color2020, color2023, x_grid, label2020, label2023):
    """KDE overlay with rug-like histogram for a single panel."""
    # Histogram (faint background, normalized)
    bins = np.arange(min(x_grid)-0.05, max(x_grid)+0.05, 0.1)
    ax.hist(s2020, bins=bins, density=True, alpha=0.18, color=color2020,
            label=None, zorder=1)
    ax.hist(s2023, bins=bins, density=True, alpha=0.18, color=color2023,
            label=None, zorder=1)
    # KDE
    if len(s2020) > 5:
        k20 = stats.gaussian_kde(s2020)
        ax.plot(x_grid, k20(x_grid), color=color2020, linewidth=1.6,
                linestyle=(0, (3, 2)), label=label2020, zorder=3)
    if len(s2023) > 5:
        k23 = stats.gaussian_kde(s2023)
        ax.plot(x_grid, k23(x_grid), color=color2023, linewidth=1.8,
                linestyle="-", label=label2023, zorder=3)
    # Means as vertical lines
    ax.axvline(s2020.mean(), color=color2020, linewidth=0.9,
               linestyle=":", alpha=0.7, zorder=2)
    ax.axvline(s2023.mean(), color=color2023, linewidth=0.9,
               linestyle=":", alpha=0.9, zorder=2)


# Top row: Superordinate Identity (1-4 scale)
xg_s = np.linspace(0.8, 4.2, 400)
kde_overlay(axes[0,0], rus20_s, rus23_s, LINE_2020, RUS, xg_s,
            "Russian 2020", "Russian 2023")
axes[0,0].set_title("Russian respondents — Superordinate Identity",
                    fontsize=10, fontweight="bold", loc="left")
axes[0,0].set_xlim(0.8, 4.2)
axes[0,0].legend(frameon=False, fontsize=8, loc="upper left")

kde_overlay(axes[0,1], est20_s, est23_s, LINE_2020, EST, xg_s,
            "Estonian 2020", "Estonian 2023")
axes[0,1].set_title("Estonian respondents — Superordinate Identity",
                    fontsize=10, fontweight="bold", loc="left")
axes[0,1].set_xlim(0.8, 4.2)
axes[0,1].legend(frameon=False, fontsize=8, loc="upper left")

# Bottom row: Group ID Patterns (1-5 scale)
xg_g = np.linspace(0.5, 5.5, 400)
kde_overlay(axes[1,0], rus20_g, rus23_g, LINE_2020, RUS, xg_g,
            "Russian 2020", "Russian 2023")
axes[1,0].set_title("Russian respondents — Group ID Patterns",
                    fontsize=10, fontweight="bold", loc="left")
axes[1,0].set_xlim(0.5, 5.5)
axes[1,0].legend(frameon=False, fontsize=8, loc="upper right")

kde_overlay(axes[1,1], est20_g, est23_g, LINE_2020, EST, xg_g,
            "Estonian 2020", "Estonian 2023")
axes[1,1].set_title("Estonian respondents — Group ID Patterns",
                    fontsize=10, fontweight="bold", loc="left")
axes[1,1].set_xlim(0.5, 5.5)
axes[1,1].legend(frameon=False, fontsize=8, loc="upper right")

# Bottom-row x-axis labels
axes[1,0].set_xlabel("Score (1–5: 1 = own nationality only, 5 = Estonian only)",
                     fontsize=8.5, color="#444")
axes[1,1].set_xlabel("Score (1–5: 1 = own nationality only, 5 = Estonian only)",
                     fontsize=8.5, color="#444")
axes[0,0].set_xlabel("Score (1–4 inverted: 1 = weak, 4 = strong belonging)",
                     fontsize=8.5, color="#444")
axes[0,1].set_xlabel("Score (1–4 inverted: 1 = weak, 4 = strong belonging)",
                     fontsize=8.5, color="#444")

for ax in axes.flat:
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="both", labelsize=7.5, color="#888")
    ax.set_ylabel("Density", fontsize=8.5, color="#444")

# Title and footnote
fig.text(0.05, 0.970, "Polarization Check — Distribution Shapes 2020 → 2023",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.05, 0.948,
         "If 2023 distributions show heavier tails or bimodality not present in 2020,",
         fontsize=8.5, color="#444")
fig.text(0.05, 0.932,
         "within-group SD increases reflect polarization rather than uniform attitude shift.",
         fontsize=8.5, color="#444")

fig.text(0.05, 0.020,
         f"Levene's test for equality of variance (Russians, 2020 vs 2023): "
         f"Superordinate Identity p = {lev_s:.3f}; Group ID Patterns p = {lev_g:.3f}.",
         fontsize=7, color="#555")
fig.text(0.05, 0.006,
         "Dotted vertical lines = group means. Faint bars = histograms (probability density). "
         "Curves = Gaussian KDE.",
         fontsize=7, color="#555")

plt.subplots_adjust(left=0.08, right=0.97, top=0.86, bottom=0.10,
                    wspace=0.18, hspace=0.55)

out = ROOT / "viz" / "fig_polarization_density.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
