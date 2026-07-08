"""
Simple-slopes visualization of the INTERACTION MLR results from script 99
(Table 2 of MLR_Contact_Language_APA.docx).

Each panel shows three contact-slope lines — one at each of three language
levels: −1 SD (low), mean (average), +1 SD (high). The fan-out (or
convergence) of the three lines visually represents the Contact × Language
interaction (B₃):

  - If B₃ ≈ 0: the three lines are PARALLEL → no moderation; language doesn't
    affect contact's slope.
  - If B₃ > 0 on a positive-direction outcome: high-language line steeper
    upward than low-language line → language AMPLIFIES contact's effect.
  - If B₃ < 0: high-language line shallower than low-language line →
    language DAMPENS contact's effect.

Plotted in standardized units (β scale) so panels are directly comparable.

Output: viz/fig_mlr_interaction_simple_slopes.jpg (300 DPI)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

ROOT = Path(__file__).parent.parent

# ---------- Reload data, refit interaction MLR per cell, capture SDs ------
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


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).astype(float)


CONTACT_2023 = {0: [f"Q52_{i}" for i in range(1, 7)], 1: [f"Q51_{i}" for i in range(1, 7)]}
CONTACT_2020 = {0: [f"K4X2_{i}" for i in range(1, 7)], 1: [f"K4X1_{i}" for i in range(1, 7)]}
LANG_2023 = {0: "Q71_2", 1: "Q71_1"}
LANG_2020 = {0: "K5_2",  1: "K5_1"}


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
    lang_col = LANG_2023[grp_code] if year == 2023 else LANG_2020[grp_code]
    lang = 7 - to_num(sub_df[lang_col])
    return pd.DataFrame({"value": outcome.values, "contact": contact.values,
                          "language": lang.values}).dropna()


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

# Refit each cell's interaction model and store β values for plotting
fits = {}
for spec in SPECS:
    for grp_code, grp_name in [(0, "Estonian"), (1, "Russian")]:
        for year in (2020, 2023):
            data = build_cell(spec, year, grp_code)
            if len(data) < 10: continue
            data["contact_c"]  = data["contact"]  - data["contact"].mean()
            data["language_c"] = data["language"] - data["language"].mean()
            data["cxl"] = data["contact_c"] * data["language_c"]
            sd_y = data["value"].std(ddof=1)
            sd_c = data["contact_c"].std(ddof=1)
            sd_l = data["language_c"].std(ddof=1)
            X = sm.add_constant(data[["contact_c", "language_c", "cxl"]])
            m = sm.OLS(data["value"], X).fit(cov_type="HC3")
            beta1 = m.params["contact_c"]  * sd_c / sd_y
            beta2 = m.params["language_c"] * sd_l / sd_y
            beta3 = m.params["cxl"] * sd_c * sd_l / sd_y
            fits[(spec["name"], grp_name, year)] = {
                "beta1": beta1, "beta2": beta2, "beta3": beta3,
                "p3": m.pvalues["cxl"],
            }


# ---------- Plot setup ----------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.5,
})

# Color gradient for language levels (using a sequential green palette)
LOW_LANG_COLOR  = "#86efac"   # light green
MID_LANG_COLOR  = "#15803d"   # medium green (matches script 100)
HIGH_LANG_COLOR = "#052e16"   # dark green

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


def stars(p):
    if pd.isna(p): return ""
    if p < .001: return "***"
    if p < .01:  return "**"
    if p < .05:  return "*"
    if p < .10:  return "⁺"
    return ""


# Compute global y-axis range from predicted values
y_max = 0.0
for f in fits.values():
    # Predicted values at corners (contact = ±1, language = ±1)
    for c in (-1, 1):
        for l in (-1, 0, 1):
            y_val = f["beta1"]*c + f["beta2"]*l + f["beta3"]*c*l
            y_max = max(y_max, abs(y_val))
y_max *= 1.25
y_lim = (-y_max, y_max)

fig, axes = plt.subplots(8, 4, figsize=(15.0, 22.0), dpi=300,
                          sharex=True, sharey=True)

for i, outcome in enumerate(OUTCOMES):
    for j, (group, year) in enumerate(CELLS):
        ax = axes[i, j]
        key = (outcome, group, year)
        if key not in fits:
            ax.set_visible(False); continue
        f = fits[key]

        # Three lines: language at -1 SD, 0, +1 SD
        contact_range = np.linspace(-1, 1, 30)
        for language_z, color, label_lvl, lw in [
            (-1, LOW_LANG_COLOR,  "Low Lang.",  1.6),
            ( 0, MID_LANG_COLOR,  "Mean Lang.", 2.0),
            ( 1, HIGH_LANG_COLOR, "High Lang.", 2.4),
        ]:
            y_pred = (f["beta1"] * contact_range
                      + f["beta2"] * language_z
                      + f["beta3"] * contact_range * language_z)
            ax.plot(contact_range, y_pred, color=color, linewidth=lw,
                    solid_capstyle="round", zorder=3,
                    label=label_lvl if (i == 0 and j == 0) else None)

        # Reference lines
        ax.axhline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)
        ax.axvline(0, color="#999", linewidth=0.5, linestyle="--", zorder=1)

        # Annotation: B₃ standardized + significance
        p_val = f["p3"]
        if p_val < .001:
            p_str = "p < .001"
        else:
            p_str = f"p = {p_val:.3f}".replace("0.", ".")
        ax.text(0.98, 0.97,
                f"β₃ = {f['beta3']:+.3f}\n{stars(p_val)} ({p_str})",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=7, color="#222", family="monospace",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                          edgecolor="#aaa", linewidth=0.4, alpha=0.92))

        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(y_lim)
        ax.set_xticks([-1, 0, 1])
        ax.set_xticklabels(["−1 SD", "0", "+1 SD"], fontsize=7)
        ax.tick_params(axis="both", labelsize=7, color="#888")
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.grid(True, axis="y", linestyle=":", linewidth=0.3, color="#eee",
                zorder=0)

        if i == 0:
            ax.set_title(f"{group} {year}", fontsize=10, fontweight="bold",
                         pad=6, color="#333")

# Row labels
for i, outcome in enumerate(OUTCOMES):
    axes[i, 0].set_ylabel(PRETTY[outcome], fontsize=9, fontweight="bold",
                          color="#222", labelpad=8)

# Bottom x-label
for j in range(4):
    axes[7, j].set_xlabel("Standardized Contact (SD)",
                          fontsize=8, color="#555")

# Global title block
fig.text(0.04, 0.985,
         "MLR with Contact × Language Interaction — Simple Slopes by Cell",
         fontsize=15, fontweight="bold", ha="left")
fig.text(0.04, 0.973,
         "Each panel shows contact's predicted standardized effect on the outcome at three language levels: low (−1 SD), mean, and high (+1 SD).",
         fontsize=9, color="#444", ha="left")
fig.text(0.04, 0.963,
         "Parallel lines = no Contact × Language moderation. Fan-out = language amplifies contact's slope. Convergence = language dampens contact's slope. β₃ standardized; p-value reported.",
         fontsize=9, color="#444", ha="left")

# Legend
handles = [
    mlines.Line2D([], [], color=LOW_LANG_COLOR,  linewidth=1.6, label="Low Language (−1 SD)"),
    mlines.Line2D([], [], color=MID_LANG_COLOR,  linewidth=2.0, label="Mean Language"),
    mlines.Line2D([], [], color=HIGH_LANG_COLOR, linewidth=2.4, label="High Language (+1 SD)"),
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.973),
           frameon=False, fontsize=9, ncol=1, handlelength=2.0)

fig.text(0.04, 0.015,
         "Predicted outcome plotted in standardized (β) units. y = β₁ × Contact_z + β₂ × Language_z + β₃ × (Contact_z × Language_z).",
         fontsize=7.5, color="#555", ha="left")
fig.text(0.04, 0.005,
         "Significance for B₃ Contact × Language: *** p<.001, ** p<.01, * p<.05, ⁺ p<.10. HC3 robust SEs.",
         fontsize=7.5, color="#555", ha="left")

plt.subplots_adjust(left=0.13, right=0.985, top=0.95, bottom=0.025,
                    wspace=0.15, hspace=0.30)

out = ROOT / "viz" / "fig_mlr_interaction_simple_slopes.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"Saved: {out}")
