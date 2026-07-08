"""
Contact-Theory Regression — Coefficient (Forest) Plot
=======================================================
Companion visualization to script 63's 2×2 scatter panels. Same four
regressions, but the slopes (b₁) are shown as horizontal dots with 95% CI
brackets aligned on a common axis, making cross-cell comparison direct.

Layout:
  - Y-axis: 4 rows (Russian 2020, Russian 2023, Estonian 2020, Estonian 2023)
  - X-axis: slope coefficient on the SD scale per +1 unit of contact
  - Vertical reference line at 0 (no association)
  - Within-group lines connect 2020 and 2023 dots so the year change is visible
  - Color-coded by group (orange Russian, blue Estonian)

Output: viz/fig_contact_theory_coefplot.jpg  (300 DPI)
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

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


def composite_pairwise(df, items, dk=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != dk)
    return sub.mean(axis=1, skipna=True)


def build_pair(df, eth_val, sd_items, contact_items):
    sub = df[df["ethnicity_binary"] == eth_val]
    sd      = composite_pairwise(sub, sd_items)
    contact = composite_pairwise(sub, contact_items)
    return pd.DataFrame({"SD": sd, "Contact": 6 - contact}).dropna()


# ---------- Specs -----------------------------------------------------------
SD_RUS_2023 = ["Q57_2", "Q58_2", "Q59_2"]
SD_EST_2023 = ["Q57_1", "Q58_1", "Q59_1"]
CONTACT_RUS_2023 = [f"Q51_{i}" for i in range(1, 7)]
CONTACT_EST_2023 = [f"Q52_{i}" for i in range(1, 7)]
SD_RUS_2020 = ["K4X7_2", "K4X8_2", "K4X9_2"]
SD_EST_2020 = ["K4X7_1", "K4X8_1", "K4X9_1"]
CONTACT_RUS_2020 = [f"K4X1_{i}" for i in range(1, 7)]
CONTACT_EST_2020 = [f"K4X2_{i}" for i in range(1, 7)]


CELLS = [
    ("Russian 2020",  build_pair(df20, 1, SD_RUS_2020, CONTACT_RUS_2020), "russian"),
    ("Russian 2023",  build_pair(df23, 1, SD_RUS_2023, CONTACT_RUS_2023), "russian"),
    ("Estonian 2020", build_pair(df20, 0, SD_EST_2020, CONTACT_EST_2020), "estonian"),
    ("Estonian 2023", build_pair(df23, 0, SD_EST_2023, CONTACT_EST_2023), "estonian"),
]


def stars(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


# ---------- Run regressions -------------------------------------------------
results = []
for label, df_pair, group in CELLS:
    X = sm.add_constant(df_pair["Contact"])
    model = sm.OLS(df_pair["SD"], X).fit()
    b1 = model.params["Contact"]
    ci_lo, ci_hi = model.conf_int().loc["Contact"]
    p = model.pvalues["Contact"]
    r2 = model.rsquared
    n = int(model.nobs)
    results.append({
        "label": label, "group": group,
        "b1": b1, "ci_lo": ci_lo, "ci_hi": ci_hi,
        "p": p, "sig": stars(p), "r2": r2, "n": n,
    })


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.7,
})

RUS = "#d97706"
RUS_OPEN = "#fcd34d"
EST = "#2563eb"
EST_OPEN = "#93c5fd"

fig, ax = plt.subplots(figsize=(13.0, 5.2), dpi=300)

# Y positions: top → bottom = Russian 2020, Russian 2023, gap, Estonian 2020, Estonian 2023
y_positions = {
    "Russian 2020":  4.0,
    "Russian 2023":  3.5,
    "Estonian 2020": 2.0,
    "Estonian 2023": 1.5,
}

# Within-group connector lines (showing 2020 → 2023 movement)
ax.plot([results[0]["b1"], results[1]["b1"]],
        [y_positions["Russian 2020"], y_positions["Russian 2023"]],
        color=RUS, linewidth=1.4, alpha=0.6, zorder=1, linestyle=(0, (3, 2)))
ax.plot([results[2]["b1"], results[3]["b1"]],
        [y_positions["Estonian 2020"], y_positions["Estonian 2023"]],
        color=EST, linewidth=1.4, alpha=0.6, zorder=1, linestyle=(0, (3, 2)))

# Plot CI brackets and dots
for r in results:
    y = y_positions[r["label"]]
    is_2020 = "2020" in r["label"]
    is_rus = (r["group"] == "russian")

    color = RUS if is_rus else EST
    fillcolor = (RUS_OPEN if is_2020 else RUS) if is_rus else (EST_OPEN if is_2020 else EST)

    # 95% CI bracket
    ax.plot([r["ci_lo"], r["ci_hi"]], [y, y],
            color=color, linewidth=2.2, alpha=0.85, zorder=2,
            solid_capstyle="round")
    # CI endcaps
    for xx in (r["ci_lo"], r["ci_hi"]):
        ax.plot([xx, xx], [y - 0.10, y + 0.10],
                color=color, linewidth=1.6, alpha=0.9, zorder=2)
    # Point estimate dot (open for 2020, filled for 2023)
    if is_2020:
        ax.scatter([r["b1"]], [y], s=160, facecolor="white",
                   edgecolor=color, linewidth=2.0, zorder=3)
    else:
        ax.scatter([r["b1"]], [y], s=170, color=color,
                   edgecolor="white", linewidth=1.0, zorder=3)

    # Numeric annotation: b₁, sig, R², n — placed to the right of the CI
    ann_text = (f"b₁ = {r['b1']:+.3f} {r['sig']}    "
                f"95% CI [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]    "
                f"R² = {r['r2']:.3f}    n = {r['n']}")
    # Use axis transform with x in data coords + text offset to the right of the CI
    ax.text(r["ci_hi"] + 0.012, y, ann_text,
            ha="left", va="center", fontsize=8,
            color="#222", family="monospace")

# Reference line at 0
ax.axvline(0, color="#666", linewidth=1.0, linestyle="-", zorder=0)

# Y-axis labels
ax.set_yticks(list(y_positions.values()))
ax.set_yticklabels(list(y_positions.keys()), fontsize=10, fontweight="bold")
ax.set_ylim(1.0, 4.5)
ax.invert_yaxis()  # Russian 2020 (highest y) appears on top

# X-axis — extended right so annotations fit
ax.set_xlim(-0.42, 0.50)
ax.set_xticks(np.arange(-0.4, 0.31, 0.1))
ax.set_xlabel("Slope b₁ — change in SD: Primary Out-group composite per +1 unit of contact frequency",
              fontsize=9.5, color="#444", labelpad=8)

# Spines
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#666")
ax.tick_params(axis="x", length=2.5, color="#666", labelsize=8)
ax.tick_params(axis="y", length=0)

# Light grid
for x in np.arange(-0.4, 0.31, 0.1):
    ax.axvline(x, color="#eee", linewidth=0.5, zorder=0)

# Title
fig.text(0.04, 0.965,
         "Contact-Theory Regression — Slopes with 95% Confidence Intervals",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Bivariate OLS regression of SD: Primary Out-group on Contact (inverted: higher = more contact), within each group × year cell.",
         fontsize=8.5, color="#444", ha="left")
fig.text(0.04, 0.918,
         "Negative slope = contact-theory direction (more contact predicts less social distance).",
         fontsize=8.5, color="#444", ha="left")

# Legend
y20 = mlines.Line2D([], [], marker="o", color="white",
                    markerfacecolor="white", markeredgecolor="#444",
                    markersize=10, markeredgewidth=2.0,
                    linestyle="None", label="2020 (open dot)")
y23 = mlines.Line2D([], [], marker="o", color="white",
                    markerfacecolor="#444", markeredgecolor="white",
                    markersize=10, linestyle="None", label="2023 (filled dot)")
zero = mlines.Line2D([], [], color="#666", linewidth=1.0,
                     label="0 = no contact–distance association")
fig.legend(handles=[y20, y23, zero],
           loc="upper right", bbox_to_anchor=(0.97, 0.918),
           frameon=False, fontsize=8, ncol=3, handlelength=2.0,
           columnspacing=2.0)

# Footer
fig.text(0.04, 0.025,
         "Dashed within-group lines connect 2020 → 2023. Cross-sectional associations; no causal interpretation. EIM is a repeated cross-section, not a panel.",
         fontsize=7.0, color="#555", ha="left")
fig.text(0.04, 0.010,
         "Significance: *** p<.001, ** p<.01, * p<.05, ns = not significant.",
         fontsize=7.0, color="#555", ha="left")

plt.subplots_adjust(left=0.13, right=0.985, top=0.86, bottom=0.16)

out_path = ROOT / "viz" / "fig_contact_theory_coefplot.jpg"
plt.savefig(out_path, dpi=300, format="jpg",
            facecolor="white", pil_kwargs={"quality": 95})
print(f"Saved: {out_path}")
