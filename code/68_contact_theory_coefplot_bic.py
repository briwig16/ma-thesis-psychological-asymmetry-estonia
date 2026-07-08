"""
Contact-Theory Regression Coefficient Plot — Belief in Inevitable Conflict
============================================================================
Coefficient (forest) plot variant of script 67. Same four regressions; slopes
aligned on a common axis with 95% CI brackets.

Direction reminder:
  - BiC composite (Option B): higher = more belief in conflict.
  - Contact: higher = more frequent contact.
  - Contact theory predicts NEGATIVE slope (same convention as the SD: Primary
    coefficient plot in script 64).

Output: viz/fig_contact_theory_coefplot_bic.jpg  (300 DPI)
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


def bic_composite(df, items, reverse_items, scale_max=4):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    for it in reverse_items:
        sub[it] = (scale_max + 1) - sub[it]
    return sub.mean(axis=1, skipna=True)


def contact_composite(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    return 6 - sub.mean(axis=1, skipna=True)


BIC_2023 = ["Q63_1", "Q63_2", "Q63_3", "Q63_4"]
BIC_2023_REV = ["Q63_1", "Q63_2"]
BIC_2020 = ["K6X1_1", "K6X1_2", "K6X1_3", "K6X1_4"]
BIC_2020_REV = ["K6X1_1", "K6X1_2"]

CONTACT_RUS_2023 = [f"Q51_{i}" for i in range(1, 7)]
CONTACT_EST_2023 = [f"Q52_{i}" for i in range(1, 7)]
CONTACT_RUS_2020 = [f"K4X1_{i}" for i in range(1, 7)]
CONTACT_EST_2020 = [f"K4X2_{i}" for i in range(1, 7)]


def build_pair(df, eth_val, contact_items, year):
    sub = df[df["ethnicity_binary"] == eth_val]
    if year == 2020:
        bic = bic_composite(sub, BIC_2020, BIC_2020_REV)
    else:
        bic = bic_composite(sub, BIC_2023, BIC_2023_REV)
    contact = contact_composite(sub, contact_items)
    return pd.DataFrame({"BiC": bic, "Contact": contact}).dropna()


CELLS = [
    ("Russian 2020",  build_pair(df20, 1, CONTACT_RUS_2020, 2020), "russian"),
    ("Russian 2023",  build_pair(df23, 1, CONTACT_RUS_2023, 2023), "russian"),
    ("Estonian 2020", build_pair(df20, 0, CONTACT_EST_2020, 2020), "estonian"),
    ("Estonian 2023", build_pair(df23, 0, CONTACT_EST_2023, 2023), "estonian"),
]


def stars(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


# ---------- Regressions -----------------------------------------------------
results = []
for label, df_pair, group in CELLS:
    X = sm.add_constant(df_pair["Contact"])
    model = sm.OLS(df_pair["BiC"], X).fit()
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
EST = "#2563eb"

fig, ax = plt.subplots(figsize=(13.0, 5.2), dpi=300)

y_positions = {
    "Russian 2020":  4.0,
    "Russian 2023":  3.5,
    "Estonian 2020": 2.0,
    "Estonian 2023": 1.5,
}

ax.plot([results[0]["b1"], results[1]["b1"]],
        [y_positions["Russian 2020"], y_positions["Russian 2023"]],
        color=RUS, linewidth=1.4, alpha=0.6, zorder=1, linestyle=(0, (3, 2)))
ax.plot([results[2]["b1"], results[3]["b1"]],
        [y_positions["Estonian 2020"], y_positions["Estonian 2023"]],
        color=EST, linewidth=1.4, alpha=0.6, zorder=1, linestyle=(0, (3, 2)))

for r in results:
    y = y_positions[r["label"]]
    is_2020 = "2020" in r["label"]
    is_rus = (r["group"] == "russian")
    color = RUS if is_rus else EST

    ax.plot([r["ci_lo"], r["ci_hi"]], [y, y],
            color=color, linewidth=2.2, alpha=0.85, zorder=2,
            solid_capstyle="round")
    for xx in (r["ci_lo"], r["ci_hi"]):
        ax.plot([xx, xx], [y - 0.10, y + 0.10],
                color=color, linewidth=1.6, alpha=0.9, zorder=2)
    if is_2020:
        ax.scatter([r["b1"]], [y], s=160, facecolor="white",
                   edgecolor=color, linewidth=2.0, zorder=3)
    else:
        ax.scatter([r["b1"]], [y], s=170, color=color,
                   edgecolor="white", linewidth=1.0, zorder=3)

    ann_text = (f"b₁ = {r['b1']:+.3f} {r['sig']}    "
                f"95% CI [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]    "
                f"R² = {r['r2']:.3f}    n = {r['n']}")
    ax.text(r["ci_hi"] + 0.008, y, ann_text,
            ha="left", va="center", fontsize=8,
            color="#222", family="monospace")

ax.axvline(0, color="#666", linewidth=1.0, linestyle="-", zorder=0)

ax.set_yticks(list(y_positions.values()))
ax.set_yticklabels(list(y_positions.keys()), fontsize=10, fontweight="bold")
ax.set_ylim(1.0, 4.5)
ax.invert_yaxis()

ax.set_xlim(-0.30, 0.50)
ax.set_xticks(np.arange(-0.25, 0.55, 0.05))
ax.set_xlabel("Slope b₁ — change in Belief in Inevitable Conflict per +1 unit of contact frequency",
              fontsize=9.5, color="#444", labelpad=8)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#666")
ax.tick_params(axis="x", length=2.5, color="#666", labelsize=8)
ax.tick_params(axis="y", length=0)

for x in np.arange(-0.25, 0.55, 0.05):
    ax.axvline(x, color="#eee", linewidth=0.5, zorder=0)

# Title
fig.text(0.04, 0.965,
         "Contact-Theory Regression — Slopes with 95% Confidence Intervals (Belief in Inevitable Conflict)",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Bivariate OLS regression of BiC (Option B: higher = more conflict belief) on Contact (inverted: higher = more contact), within each group × year cell.",
         fontsize=8.5, color="#444", ha="left")
fig.text(0.04, 0.918,
         "Negative slope = contact-theory direction (more contact predicts less belief in inevitable conflict).",
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
                     label="0 = no contact–conflict-belief association")
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

out_path = ROOT / "viz" / "fig_contact_theory_coefplot_bic.jpg"
plt.savefig(out_path, dpi=300, format="jpg",
            facecolor="white", pil_kwargs={"quality": 95})
print(f"Saved: {out_path}")
