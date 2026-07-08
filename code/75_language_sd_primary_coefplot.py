"""
Out-group Language → SD: Primary Out-group — Coefficient (Forest) Plot
=======================================================================
Companion visualization to script 74's 2×2 scatter+fit panels. Same four
regressions, but the slopes (b₁) are shown as horizontal dots with 95% CI
brackets aligned on a common axis, making cross-cell comparison direct.

Layout:
  - Y-axis: 4 rows (Russian 2020, Russian 2023, Estonian 2020, Estonian 2023)
  - X-axis: slope coefficient on the PC1 scale per +1 unit of language ability
  - Vertical reference line at 0 (no association)
  - Within-group lines connect 2020 and 2023 dots so the year change is visible
  - Color-coded by group (orange Russian, blue Estonian)

Output: viz/fig_language_sd_primary_coefplot.jpg  (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
from sklearn.decomposition import PCA

ROOT = Path(__file__).parent.parent

# ---------- Load ------------------------------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)
df23["__year__"] = 2023

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)
df20["__year__"] = 2020


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).astype(float)


def clean_items(df, items, dk=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    return sub.where(sub != dk)


def recode_lang(s):
    return 7 - to_num(s, dk=9)


def fit_pc1_oriented(items_df):
    mask = items_df.notna().all(axis=1)
    X = items_df[mask].to_numpy()
    pca = PCA(n_components=1).fit(X)
    scores = pca.transform(X)[:, 0]
    pc1 = pd.Series(index=items_df.index, dtype=float)
    pc1.loc[mask] = scores
    if pc1.corr(items_df.mean(axis=1)) < 0:
        pc1 = -pc1
    return pc1


SPECS = {
    "Estonian": {
        "items_23": ["Q57_1", "Q58_1", "Q59_1"],
        "items_20": ["K4X7_1", "K4X8_1", "K4X9_1"],
        "lang_23": "Q71_2", "lang_20": "K5_2",
    },
    "Russian": {
        "items_23": ["Q57_2", "Q58_2", "Q59_2"],
        "items_20": ["K4X7_2", "K4X8_2", "K4X9_2"],
        "lang_23": "Q71_1", "lang_20": "K5_1",
    },
}


def stars(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"


# ---------- Build cells + run regressions ---------------------------------
results = []
for grp_name, spec in SPECS.items():
    grp_code = 0 if grp_name == "Estonian" else 1
    cols = ["i1", "i2", "i3"]

    sub23 = df23[df23["ethnicity_binary"] == grp_code].copy().reset_index(drop=True)
    sub20 = df20[df20["ethnicity_binary"] == grp_code].copy().reset_index(drop=True)

    items_23 = clean_items(sub23, spec["items_23"]).rename(columns=dict(zip(spec["items_23"], cols)))
    items_20 = clean_items(sub20, spec["items_20"]).rename(columns=dict(zip(spec["items_20"], cols)))
    pooled = pd.concat([items_23, items_20], ignore_index=True)
    pc1 = fit_pc1_oriented(pooled)

    pooled_meta = pd.concat([
        sub23[["__year__"]].assign(lang=recode_lang(sub23[spec["lang_23"]])),
        sub20[["__year__"]].assign(lang=recode_lang(sub20[spec["lang_20"]])),
    ], ignore_index=True)
    pooled_meta["pc1"] = pc1.values

    for yr in (2020, 2023):
        df_pair = (pooled_meta[pooled_meta["__year__"] == yr]
                   [["pc1", "lang"]].rename(columns={"pc1": "SD", "lang": "Lang"})
                   .dropna())
        X = sm.add_constant(df_pair["Lang"])
        m = sm.OLS(df_pair["SD"], X).fit(cov_type="HC3")
        b1 = m.params["Lang"]
        ci_lo, ci_hi = m.conf_int().loc["Lang"]
        p = m.pvalues["Lang"]; r2 = m.rsquared; n = int(m.nobs)
        results.append({
            "label": f"{grp_name} {yr}",
            "group": grp_name.lower(),
            "b1": b1, "ci_lo": ci_lo, "ci_hi": ci_hi,
            "p": p, "sig": stars(p), "r2": r2, "n": n,
        })


# Reorder for plotting: Russian 2020, Russian 2023, Estonian 2020, Estonian 2023
order = ["Russian 2020", "Russian 2023", "Estonian 2020", "Estonian 2023"]
results = sorted(results, key=lambda r: order.index(r["label"]))


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

# Within-group connector lines (2020 → 2023)
ax.plot([results[0]["b1"], results[1]["b1"]],
        [y_positions["Russian 2020"], y_positions["Russian 2023"]],
        color=RUS, linewidth=1.4, alpha=0.6, zorder=1, linestyle=(0, (3, 2)))
ax.plot([results[2]["b1"], results[3]["b1"]],
        [y_positions["Estonian 2020"], y_positions["Estonian 2023"]],
        color=EST, linewidth=1.4, alpha=0.6, zorder=1, linestyle=(0, (3, 2)))

# CI brackets and dots
for r in results:
    y = y_positions[r["label"]]
    is_2020 = "2020" in r["label"]
    is_rus  = r["group"] == "russian"
    color = RUS if is_rus else EST

    # 95% CI bracket
    ax.plot([r["ci_lo"], r["ci_hi"]], [y, y],
            color=color, linewidth=2.2, alpha=0.85, zorder=2,
            solid_capstyle="round")
    # endcaps
    for xx in (r["ci_lo"], r["ci_hi"]):
        ax.plot([xx, xx], [y - 0.10, y + 0.10],
                color=color, linewidth=1.6, alpha=0.9, zorder=2)
    # point estimate
    if is_2020:
        ax.scatter([r["b1"]], [y], s=160, facecolor="white",
                   edgecolor=color, linewidth=2.0, zorder=3)
    else:
        ax.scatter([r["b1"]], [y], s=170, color=color,
                   edgecolor="white", linewidth=1.0, zorder=3)

    ann_text = (f"b₁ = {r['b1']:+.3f} {r['sig']}    "
                f"95% CI [{r['ci_lo']:+.3f}, {r['ci_hi']:+.3f}]    "
                f"R² = {r['r2']:.3f}    n = {r['n']}")
    ax.text(r["ci_hi"] + 0.012, y, ann_text,
            ha="left", va="center", fontsize=8,
            color="#222", family="monospace")

ax.axvline(0, color="#666", linewidth=1.0, linestyle="-", zorder=0)

ax.set_yticks(list(y_positions.values()))
ax.set_yticklabels(list(y_positions.keys()), fontsize=10, fontweight="bold")
ax.set_ylim(1.0, 4.5)
ax.invert_yaxis()

# x-axis range: extend right so the annotation fits
all_hi = max(r["ci_hi"] for r in results)
all_lo = min(r["ci_lo"] for r in results)
ax.set_xlim(all_lo - 0.05, max(0.20, all_hi + 0.40))
ax.set_xticks(np.arange(-0.4, 0.21, 0.1))
ax.set_xlabel("Slope b₁ — change in SD: Primary Out-group PC1 per +1 unit of out-group language ability",
              fontsize=9.5, color="#444", labelpad=8)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#666")
ax.tick_params(axis="x", length=2.5, color="#666", labelsize=8)
ax.tick_params(axis="y", length=0)

for x in np.arange(-0.4, 0.21, 0.1):
    ax.axvline(x, color="#eee", linewidth=0.5, zorder=0)

fig.text(0.04, 0.965,
         "Out-group Language → SD: Primary Out-group — Slopes with 95% Confidence Intervals",
         fontsize=13, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Bivariate OLS of SD: Primary Out-group PC1 on out-group language ability (1 = none … 6 = native), within each group × year cell.",
         fontsize=8.5, color="#444", ha="left")
fig.text(0.04, 0.918,
         "Negative slope = contact-theory direction (more language ability predicts less social distance).",
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
                     label="0 = no language–distance association")
fig.legend(handles=[y20, y23, zero],
           loc="upper right", bbox_to_anchor=(0.97, 0.918),
           frameon=False, fontsize=8, ncol=3, handlelength=2.0,
           columnspacing=2.0)

fig.text(0.04, 0.025,
         "Dashed within-group lines connect 2020 → 2023. HC3 robust standard errors. Cross-sectional associations; no causal interpretation.",
         fontsize=7.0, color="#555", ha="left")
fig.text(0.04, 0.010,
         "Significance: *** p<.001, ** p<.01, * p<.05, ns = not significant.",
         fontsize=7.0, color="#555", ha="left")

plt.subplots_adjust(left=0.13, right=0.985, top=0.86, bottom=0.16)

out_path = ROOT / "viz" / "fig_language_sd_primary_coefplot.jpg"
plt.savefig(out_path, dpi=300, format="jpg",
            facecolor="white", pil_kwargs={"quality": 95})
print(f"Saved: {out_path}")
