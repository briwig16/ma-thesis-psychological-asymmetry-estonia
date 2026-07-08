"""
Scatter + regression-fit grid for the bivariate contact regressions from
script 97.

Each panel = one outcome × group × wave cell. Within each panel:
  - Scatter of respondent-level points (contact on x, outcome on y), jittered
    for legibility because both axes are coarsely discrete (1–5 contact,
    Likert 1–4 or 1–5 outcomes).
  - OLS fit line with 95% CI band on the conditional mean.
  - In-panel annotation: β, p, R², n.

Layout: 8 outcomes (rows) × 4 cells (columns) = 32 panels.

Output: viz/fig_bivariate_scatter_fit_grid.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent

# ---------- Load data + helpers (mirrors script 97) -----------------------
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


def single_item(df, var, dk_code=9):
    s = pd.to_numeric(df[var], errors="coerce")
    return s.where(s != dk_code).astype(float)


CONTACT_2023 = {0: [f"Q52_{i}" for i in range(1, 7)], 1: [f"Q51_{i}" for i in range(1, 7)]}
CONTACT_2020 = {0: [f"K4X2_{i}" for i in range(1, 7)], 1: [f"K4X1_{i}" for i in range(1, 7)]}


def build_cell(spec, year, grp_code):
    df = df23 if year == 2023 else df20
    sub_df = df[df["ethnicity_binary"] == grp_code]
    if spec.get("single_item"):
        item = spec[f"items_{year}"]
        dk = spec.get(f"dk_{year}", 9)
        outcome = single_item(sub_df, item, dk_code=dk)
    elif isinstance(spec[f"items_{year}"], dict):
        grp_key = "E" if grp_code == 0 else "R"
        items = spec[f"items_{year}"][grp_key]
        rev = (spec[f"rev_{year}"][grp_key] if spec.get(f"rev_{year}") else None)
        outcome = clean(sub_df, items, rev, spec["smax"])
    else:
        items = spec[f"items_{year}"]
        rev = spec.get(f"rev_{year}")
        outcome = clean(sub_df, items, rev, spec["smax"])
    if spec["inv"]:
        outcome = (spec["smax"] + 1) - outcome
    contact_items = CONTACT_2023[grp_code] if year == 2023 else CONTACT_2020[grp_code]
    contact = 6 - clean(sub_df, contact_items)
    return pd.DataFrame({"value": outcome.values, "contact": contact.values}).dropna()


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
    {"name": "Group ID Patterns", "smax": 5, "inv": False, "single_item": True,
     "items_2023": "Q66", "items_2020": "K6X4",
     "dk_2023": 9, "dk_2020": 6},
    {"name": "Territorial Attachment", "smax": 4, "inv": True, "single_item": True,
     "items_2023": "Q67_1", "items_2020": "K6X5_1"},
]


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


# ---------- Plot setup ----------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.5,
})

EST_COLOR = "#2563eb"
RUS_COLOR = "#d97706"

OUTCOMES = [s["name"] for s in SPECS]
PRETTY = {
    "Superordinate Identity":             "Superordinate Identity",
    "SD: Primary Out-group":              "SD: Primary Out-group",
    "SD: General Out-group":              "SD: General Out-group",
    "Comparative Opportunity Assessment": "Comparative Opportunity",
    "Belief in Inevitable Conflict":      "Belief in Inevitable Conflict",
    "Minority Inclusion Support":         "Minority Inclusion Support",
    "Group ID Patterns":                  "Group ID Patterns",
    "Territorial Attachment":             "Territorial Attachment",
}
CELLS = [("Estonian", 2020), ("Estonian", 2023), ("Russian", 2020), ("Russian", 2023)]

fig, axes = plt.subplots(8, 4, figsize=(16.0, 22.0), dpi=300, sharex=True)

for i, spec in enumerate(SPECS):
    for j, (group, year) in enumerate(CELLS):
        ax = axes[i, j]
        grp_code = 0 if group == "Estonian" else 1
        data = build_cell(spec, year, grp_code)
        if len(data) < 10:
            ax.set_visible(False); continue

        # OLS fit
        X = sm.add_constant(data["contact"])
        m = sm.OLS(data["value"], X).fit(cov_type="HC3")
        B0, B1 = m.params["const"], m.params["contact"]
        sd_x = data["contact"].std(ddof=1)
        sd_y = data["value"].std(ddof=1)
        beta = B1 * sd_x / sd_y if sd_y > 0 else float("nan")
        p_val = m.pvalues["contact"]
        R2 = m.rsquared
        n = int(m.nobs)

        color = EST_COLOR if group == "Estonian" else RUS_COLOR

        # Scatter with jitter
        rng = np.random.default_rng(42 + i * 4 + j)
        jx = rng.uniform(-0.12, 0.12, size=len(data))
        jy = rng.uniform(-0.08, 0.08, size=len(data))
        ax.scatter(data["contact"] + jx, data["value"] + jy,
                   s=4, color=color, alpha=0.18, edgecolor="none", zorder=2)

        # Fit line + CI band
        x_grid = np.linspace(1, 5, 50)
        pred = m.get_prediction(sm.add_constant(pd.Series(x_grid, name="contact")))
        ci = pred.summary_frame(alpha=0.05)
        ax.plot(x_grid, ci["mean"], color="#111", linewidth=1.6, zorder=4)
        ax.fill_between(x_grid, ci["mean_ci_lower"], ci["mean_ci_upper"],
                        color="#111", alpha=0.10, zorder=3)

        # Annotation
        ax.text(0.02, 0.97,
                f"β = {beta:+.2f}{stars(p_val)}\nR² = {R2:.3f}\nn = {n}",
                transform=ax.transAxes, ha="left", va="top",
                fontsize=7, color="#222", family="monospace",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#aaa", linewidth=0.4, alpha=0.93))

        # Axis settings
        ax.set_xlim(0.5, 5.5)
        ax.set_xticks([1, 2, 3, 4, 5])
        smax = spec["smax"]
        ax.set_ylim(0.5, smax + 0.5)
        ax.set_yticks(list(range(1, smax + 1)))
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.tick_params(axis="both", labelsize=7, color="#888")

        # Column titles (first row only)
        if i == 0:
            ax.set_title(f"{group} {year}", fontsize=10, fontweight="bold",
                         pad=6, color="#333")

# Row labels (outcome name)
for i, outcome in enumerate(OUTCOMES):
    axes[i, 0].set_ylabel(PRETTY[outcome], fontsize=9, fontweight="bold",
                          color="#222", labelpad=8)

# X-axis label on bottom row
for j in range(4):
    axes[7, j].set_xlabel("Out-group contact (1 = no comm. … 5 = daily)",
                          fontsize=8, color="#555")

# Global title
fig.text(0.04, 0.985,
         "Bivariate Regression of Each Outcome on Out-group Contact — Scatter + Fit by Cell",
         fontsize=15, fontweight="bold", ha="left")
fig.text(0.04, 0.973,
         "Each panel: respondent-level scatter (jittered) of out-group contact (x) against the outcome (y), with OLS fit line and 95% CI band.",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.963,
         "Estonian respondents (blue dots), Russian respondents (orange dots). Black line = OLS fit. Shaded band = 95% CI on the conditional mean.",
         fontsize=9, color="#444", ha="left")

fig.text(0.04, 0.015,
         "Out-group contact: Estonian respondents → Russian speakers (Q52/K4X2); Russian respondents → Estonian speakers (Q51/K4X1). Inverted so higher = more frequent contact.",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.005,
         "Significance: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10. β = standardized slope. R² = proportion of variance explained.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.12, right=0.985, top=0.95, bottom=0.025,
                    wspace=0.18, hspace=0.30)

out = ROOT / "viz" / "fig_bivariate_scatter_fit_grid.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
