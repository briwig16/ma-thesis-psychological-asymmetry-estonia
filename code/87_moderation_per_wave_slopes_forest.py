"""
Forest plot of per-wave contact slopes — the visual companion to script 86's
regression-line grid.

For each composite × ethnic group, the moderation regression yields two
contact slopes:
    2020 contact slope = B₂        (effect of +1 unit contact on composite, in 2020)
    2023 contact slope = B₂ + B₃   (effect of +1 unit contact on composite, in 2023)

This plot shows both slopes per cell, with 95% CIs, on a shared axis.
Within-row movement between the 2020 and 2023 dots IS the year × contact
interaction (B₃). The plot makes the moderation directly visible as a
horizontal shift, while letting you also see the absolute slope levels.

Output: viz/fig_moderation_per_wave_slopes_forest.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

# ---------- Refit moderation regressions to get B2, B2+B3, with CIs --------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)
df20, _ = pyreadstat.read_sav(
    str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"), encoding="latin1"
)
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy().reset_index(drop=True)


def clean(df, items, reverse_items=None, scale_max=None, dk_code=9):
    sub = df[items].apply(pd.to_numeric, errors="coerce")
    sub = sub.where(sub != dk_code)
    if reverse_items:
        for it in reverse_items:
            sub[it] = (scale_max + 1) - sub[it]
    return sub.mean(axis=1, skipna=True)


CONTACT_2023 = {0: [f"Q52_{i}" for i in range(1, 7)], 1: [f"Q51_{i}" for i in range(1, 7)]}
CONTACT_2020 = {0: [f"K4X2_{i}" for i in range(1, 7)], 1: [f"K4X1_{i}" for i in range(1, 7)]}


def build_cell(spec, df, year, grp_code):
    if isinstance(spec[f"items_{year}"], dict):
        grp_key = "E" if grp_code == 0 else "R"
        items = spec[f"items_{year}"][grp_key]
        rev = (spec[f"rev_{year}"][grp_key] if spec.get(f"rev_{year}") else None)
    else:
        items = spec[f"items_{year}"]
        rev = spec.get(f"rev_{year}")
    sub_df = df[df["ethnicity_binary"] == grp_code]
    composite_vals = clean(sub_df, items, rev, spec["smax"])
    if spec["inv"]:
        composite_vals = (spec["smax"] + 1) - composite_vals
    contact_items = (CONTACT_2023[grp_code] if year == 2023 else CONTACT_2020[grp_code])
    contact_vals = 6 - clean(sub_df, contact_items)
    return pd.DataFrame({
        "value": composite_vals.values, "contact": contact_vals.values,
        "year_2023": 1 if year == 2023 else 0,
    })


SPECS = [
    {"name": "Superordinate Identity", "smax": 4, "inv": True,
     "items_2023": ["Q67_2","Q67_4","Q67_5"], "rev_2023": ["Q67_4"],
     "items_2020": ["K6X5_2","K6X5_3","K6X5_4"], "rev_2020": ["K6X5_3"]},
    {"name": "SD: Primary Out-group", "smax": 5, "inv": False,
     "items_2023": {"E": ["Q57_1","Q58_1","Q59_1"], "R": ["Q57_2","Q58_2","Q59_2"]},
     "items_2020": {"E": ["K4X7_1","K4X8_1","K4X9_1"], "R": ["K4X7_2","K4X8_2","K4X9_2"]}},
    {"name": "SD: General Out-group", "smax": 5, "inv": False,
     "items_2023": ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"],
     "items_2020": ["K4X7_3","K4X8_3","K4X9_3"]},
    {"name": "Comparative Opportunity Assessment", "smax": 5, "inv": True,
     "items_2023": [f"Q44_{i}" for i in range(1,13)],
     "items_2020": [f"K3X1_{i}" for i in range(1,13)]},
    {"name": "Belief in Inevitable Conflict", "smax": 4, "inv": False,
     "items_2023": ["Q63_1","Q63_2","Q63_3","Q63_4"], "rev_2023": ["Q63_1","Q63_2"],
     "items_2020": ["K6X1_1","K6X1_2","K6X1_3","K6X1_4"], "rev_2020": ["K6X1_1","K6X1_2"]},
    {"name": "Minority Inclusion Support", "smax": 4, "inv": True,
     "items_2023": ["Q68_1","Q68_2","Q68_3"],
     "items_2020": ["K6X6_1","K6X6_2","K6X6_3"]},
]

results = []
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        s20 = build_cell(spec, df20, 2020, grp_code)
        s23 = build_cell(spec, df23, 2023, grp_code)
        long = pd.concat([s20, s23], ignore_index=True).dropna()
        long["contact_c"]    = long["contact"] - long["contact"].mean()
        long["yearXcontact"] = long["year_2023"] * long["contact_c"]
        X = sm.add_constant(long[["year_2023", "contact_c", "yearXcontact"]])
        m = sm.OLS(long["value"], X).fit(cov_type="HC3")

        # Slope at 2020 = B2 (contact_c coefficient at year=0)
        slope_20 = m.params["contact_c"]
        se_20    = m.bse["contact_c"]
        p_20     = m.pvalues["contact_c"]
        ci_20    = m.conf_int().loc["contact_c"]

        # Slope at 2023 = B2 + B3, via t_test
        tt = m.t_test("contact_c + yearXcontact = 0")
        slope_23 = float(tt.effect[0])
        se_23    = float(tt.sd[0])
        p_23     = float(tt.pvalue)
        ci_23    = (float(tt.conf_int()[0][0]), float(tt.conf_int()[0][1]))

        results.append({
            "variable": spec["name"], "group": grp_name,
            "slope_20": slope_20, "se_20": se_20, "p_20": p_20,
            "ci_20_lo": ci_20[0], "ci_20_hi": ci_20[1],
            "slope_23": slope_23, "se_23": se_23, "p_23": p_23,
            "ci_23_lo": ci_23[0], "ci_23_hi": ci_23[1],
            "B3": m.params["yearXcontact"],
            "p_B3": m.pvalues["yearXcontact"],
        })


# ---- Plot setup -----------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.7,
})

RUS = "#d97706"
EST = "#2563eb"

COMPOSITES = [s["name"] for s in SPECS]
PRETTY = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group ⁱ",
    "Comparative Opportunity Assessment": "Comparative Opportunity",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Inclusion Support",
}


def stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ("⁺" if p < .10 else "ns")


def fmt_p(p):
    if p < .001: return "< .001"
    return f"{p:.3f}".lstrip("0")


fig, ax = plt.subplots(figsize=(15.0, 9.0), dpi=300)

# Build y-positions: composite blocks of 2 group-rows (Est above Rus)
y_positions = {}
y = 13.0
for comp in COMPOSITES:
    y_positions[(comp, "Estonian")] = y; y -= 1.0
    y_positions[(comp, "Russian")]  = y; y -= 1.7

y_min, y_max = min(y_positions.values()) - 0.6, max(y_positions.values()) + 0.7

# Alternating bands per composite
for i, comp in enumerate(COMPOSITES):
    if i % 2 == 0:
        y_top = y_positions[(comp, "Estonian")] + 0.6
        y_bot = y_positions[(comp, "Russian")]  - 0.6
        ax.axhspan(y_bot, y_top, facecolor="#f7f7f7", zorder=0)

# Plot each row: 2020 (open) and 2023 (filled) dots with CIs
for r in results:
    y = y_positions[(r["variable"], r["group"])]
    color = EST if r["group"] == "Estonian" else RUS
    y20 = y + 0.20
    y23 = y - 0.20

    # 2020: open dot, faded CI
    ax.plot([r["ci_20_lo"], r["ci_20_hi"]], [y20, y20],
            color=color, linewidth=1.6, alpha=0.55,
            solid_capstyle="round", zorder=2)
    for xx in (r["ci_20_lo"], r["ci_20_hi"]):
        ax.plot([xx, xx], [y20 - 0.08, y20 + 0.08],
                color=color, linewidth=1.2, alpha=0.6, zorder=2)
    ax.scatter([r["slope_20"]], [y20], s=140, facecolor="white",
               edgecolor=color, linewidth=2.0, zorder=3)

    # Connector
    ax.plot([r["slope_20"], r["slope_23"]], [y20, y23],
            color=color, linewidth=0.8, alpha=0.45,
            linestyle=(0, (2, 2)), zorder=2)

    # 2023: filled dot, solid CI
    ax.plot([r["ci_23_lo"], r["ci_23_hi"]], [y23, y23],
            color=color, linewidth=2.2, alpha=0.9,
            solid_capstyle="round", zorder=2)
    for xx in (r["ci_23_lo"], r["ci_23_hi"]):
        ax.plot([xx, xx], [y23 - 0.08, y23 + 0.08],
                color=color, linewidth=1.6, alpha=0.95, zorder=2)
    ax.scatter([r["slope_23"]], [y23], s=160, color=color,
               edgecolor="white", linewidth=1.0, zorder=3)

    # Annotation
    delta = r["slope_23"] - r["slope_20"]
    ann = (f"{r['group']:<8}  2020 slope = {r['slope_20']:+.3f} {stars(r['p_20'])}    "
           f"2023 slope = {r['slope_23']:+.3f} {stars(r['p_23'])}    "
           f"Δ = {delta:+.3f}  (B₃ p = {fmt_p(r['p_B3'])} {stars(r['p_B3'])})")
    ax.text(max(r["ci_20_hi"], r["ci_23_hi"]) + 0.012, y,
            ann, ha="left", va="center", fontsize=8.2,
            color="#222", family="monospace")

# Reference line at 0
ax.axvline(0, color="#666", linewidth=1.0, linestyle="-", zorder=1)

# Y-axis labels at composite midpoints
yticks, yticklabels = [], []
for comp in COMPOSITES:
    y_E = y_positions[(comp, "Estonian")]
    y_R = y_positions[(comp, "Russian")]
    yticks.append((y_E + y_R) / 2)
    yticklabels.append(PRETTY[comp])
ax.set_yticks(yticks)
ax.set_yticklabels(yticklabels, fontsize=10, fontweight="bold")
ax.set_ylim(y_min, y_max)
ax.invert_yaxis()

# X-axis
all_lo = min(min(r["ci_20_lo"], r["ci_23_lo"]) for r in results)
all_hi = max(max(r["ci_20_hi"], r["ci_23_hi"]) for r in results)
ax.set_xlim(all_lo - 0.05, all_hi + 0.95)
ax.set_xlabel("Contact-on-composite slope  (B₂ at 2020; B₂ + B₃ at 2023)",
              fontsize=10, color="#444", labelpad=8)

for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color("#ccc")
ax.spines["bottom"].set_color("#666")
ax.tick_params(axis="x", length=2.5, color="#666", labelsize=9)
ax.tick_params(axis="y", length=0)

# Title block
fig.text(0.04, 0.965,
         "Per-Wave Contact Slopes — Forest Plot of Moderation Effects",
         fontsize=14, fontweight="bold", ha="left")
fig.text(0.04, 0.940,
         "Each row shows the contact-on-composite slope at 2020 (open dot, faded bracket) and 2023 (filled dot, solid bracket).",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.918,
         "The dashed connector and Δ value represent the year × contact interaction (B₃). Reference line at 0 = no contact-attitude association.",
         fontsize=9, color="#444", ha="left")

# Legend
legend_handles = [
    mlines.Line2D([], [], marker="o", color=EST, markerfacecolor="white",
                  markeredgecolor=EST, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Estonian — 2020 slope"),
    mlines.Line2D([], [], marker="o", color=EST, markerfacecolor=EST,
                  markeredgecolor="white", markersize=10,
                  linestyle="None", label="Estonian — 2023 slope"),
    mlines.Line2D([], [], marker="o", color=RUS, markerfacecolor="white",
                  markeredgecolor=RUS, markersize=10, markeredgewidth=1.8,
                  linestyle="None", label="Russian — 2020 slope"),
    mlines.Line2D([], [], marker="o", color=RUS, markerfacecolor=RUS,
                  markeredgecolor="white", markersize=10,
                  linestyle="None", label="Russian — 2023 slope"),
]
fig.legend(handles=legend_handles, loc="upper right",
           bbox_to_anchor=(0.985, 0.94),
           frameon=False, fontsize=8.5, ncol=2,
           handlelength=1.4, columnspacing=1.5)

# Footer
fig.text(0.04, 0.022,
         "Out-group contact: Estonians → Q52/K4X2 (Russian-speaker contact); Russians → Q51/K4X1 (Estonian-speaker contact). Inverted: higher = more contact. Mean-centered within group.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.008,
         "ⁱ SD: General Out-group uses different items in 2020 (3) vs 2023 (6). HC3 robust SEs. Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10, ns = ns.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.18, right=0.985, top=0.88, bottom=0.075)

out = ROOT / "viz" / "fig_moderation_per_wave_slopes_forest.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
