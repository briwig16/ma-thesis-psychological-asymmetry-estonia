"""
Distribution Charts for Each Comparative Opportunity Assessment Item
======================================================================
For each of the 12 items in the Q44 / K3X1 battery (perceived comparative
opportunity by life domain), produces a two-panel distribution chart
(Russian | Estonian) showing 2020 vs 2023 KDE + histogram overlays.

This is the item-level visual companion to the composite-level decomposition
in code/29_item_decomposition.py. Where script 29 reduces each item to a
single Cohen's d, this script shows the full distributional shape — useful
for catching item-level polarization, ceiling/floor effects, or asymmetric
shifts that mean comparisons hide.

Outputs:
  viz/fig_compopp_item_<n>_<label>.jpg              (12 charts, 300 DPI)
  reports/Comparative_Opportunity_Item_Distributions.docx
                                                    (single document, all 12 charts embedded)

Q44 scale: 1 = much better for Estonians, 3 = equal, 5 = much better for
people of other nationalities. Lower = perceives Estonian advantage. Items
are inverted in the canonical analysis (5 - x); for distribution charts,
raw scale is shown so readers can interpret directly without remembering the
inversion convention.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyreadstat
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
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

# Item labels (must match Q44_1..Q44_12 / K3X1_1..K3X1_12 order)
ITEM_LABELS = [
    "Material well-being",
    "Cultural participation",
    "Education",
    "Social/political rights",
    "Entrepreneurship",
    "Career & jobs",
    "Medical care",
    "Housing",
    "Leisure & holidays",
    "Children & youth opportunities",
    "Sports & exercise",
    "State benefits/services",
]


def to_num(s, dk=9):
    s = pd.to_numeric(s, errors="coerce")
    return s.where(s != dk).dropna().astype(float)


def get_item_series(item_idx):
    """Return four series for item_idx (1..12): est20, rus20, est23, rus23."""
    v23 = f"Q44_{item_idx}"
    v20 = f"K3X1_{item_idx}"
    e23 = to_num(df23.loc[df23["ethnicity_binary"] == 0, v23])
    r23 = to_num(df23.loc[df23["ethnicity_binary"] == 1, v23])
    e20 = to_num(df20.loc[df20["ethnicity_binary"] == 0, v20])
    r20 = to_num(df20.loc[df20["ethnicity_binary"] == 1, v20])
    return e20, r20, e23, r23


# ---------- Diagnostics summary --------------------------------------------
def diag(s):
    return {"M": s.mean(), "SD": s.std(ddof=1),
            "IQR": s.quantile(.75) - s.quantile(.25), "N": len(s)}


print("="*92)
print("Q44 / K3X1 — Comparative Opportunity Assessment, item-level diagnostics")
print("Scale: 1 = much better for Estonians ... 5 = much better for other nationalities")
print("="*92)


def stars(p):
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


# ---------- Plot one item ---------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST = "#2563eb"
RUS = "#d97706"
LINE_2020 = "#9ca3af"


def plot_item(item_idx, label):
    e20, r20, e23, r23 = get_item_series(item_idx)

    # Print diagnostics
    print(f"\n  Q44_{item_idx} / K3X1_{item_idx} — {label}")
    for tag, s in [("Rus 2020", r20), ("Rus 2023", r23),
                   ("Est 2020", e20), ("Est 2023", e23)]:
        d = diag(s)
        print(f"    {tag}: N={d['N']:4d}  M={d['M']:.3f}  SD={d['SD']:.3f}  IQR={d['IQR']:.3f}")

    lev_rus = stats.levene(r20, r23, center="median").pvalue
    lev_est = stats.levene(e20, e23, center="median").pvalue
    p_rus = stats.ttest_ind(r23, r20, equal_var=False).pvalue
    p_est = stats.ttest_ind(e23, e20, equal_var=False).pvalue

    fig, axes = plt.subplots(1, 2, figsize=(8.5, 3.8), dpi=300, sharey=True)

    def kde_overlay(ax, s2020, s2023, color2023, x_grid, label2020, label2023):
        bins = np.arange(0.55, 5.55, 0.5)
        ax.hist(s2020, bins=bins, density=True, alpha=0.18, color=LINE_2020, zorder=1)
        ax.hist(s2023, bins=bins, density=True, alpha=0.18, color=color2023, zorder=1)
        if len(s2020) > 5:
            k = stats.gaussian_kde(s2020)
            ax.plot(x_grid, k(x_grid), color=LINE_2020, linewidth=1.5,
                    linestyle=(0, (3, 2)), label=label2020, zorder=3)
        if len(s2023) > 5:
            k = stats.gaussian_kde(s2023)
            ax.plot(x_grid, k(x_grid), color=color2023, linewidth=1.7,
                    linestyle="-", label=label2023, zorder=3)
        ax.axvline(s2020.mean(), color=LINE_2020, linewidth=0.9,
                   linestyle=":", alpha=0.7, zorder=2)
        ax.axvline(s2023.mean(), color=color2023, linewidth=0.9,
                   linestyle=":", alpha=0.9, zorder=2)
        # Reference at midpoint (3 = "equal")
        ax.axvline(3, color="#bbb", linewidth=0.6, linestyle="-", alpha=0.5, zorder=0)

    xg = np.linspace(0.6, 5.4, 400)

    kde_overlay(axes[0], r20, r23, RUS, xg, "Russian 2020", "Russian 2023")
    axes[0].set_title("Russian respondents", fontsize=10.5, fontweight="bold", loc="left")
    axes[0].legend(frameon=False, fontsize=8, loc="upper right")

    kde_overlay(axes[1], e20, e23, EST, xg, "Estonian 2020", "Estonian 2023")
    axes[1].set_title("Estonian respondents", fontsize=10.5, fontweight="bold", loc="left")
    axes[1].legend(frameon=False, fontsize=8, loc="upper right")

    for ax in axes:
        ax.set_xlim(0.6, 5.4)
        ax.set_xlabel("1 = better for Estonians  ·  3 = equal  ·  5 = better for others",
                      fontsize=8, color="#444")
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        ax.tick_params(axis="both", labelsize=7.5, color="#888")
    axes[0].set_ylabel("Density", fontsize=9, color="#444")

    fig.text(0.05, 0.955,
             f"Q44_{item_idx} — {label}",
             fontsize=12.5, fontweight="bold", ha="left")
    fig.text(0.05, 0.925,
             "Distribution shapes 2020 → 2023 by ethnic group. Light-grey vertical line at score = 3 marks the \"equal opportunity\" midpoint.",
             fontsize=8, color="#444")

    fig.text(0.05, 0.043,
             f"Russian: t-test p = {p_rus:.3f} {stars(p_rus)}; Levene's p = {lev_rus:.3f}.   "
             f"Estonian: t-test p = {p_est:.3f} {stars(p_est)}; Levene's p = {lev_est:.3f}.",
             fontsize=7, color="#555")
    fig.text(0.05, 0.018,
             "Dotted vertical lines = group means. Faint bars = histograms. Curves = Gaussian KDE.",
             fontsize=7, color="#555")

    plt.subplots_adjust(left=0.07, right=0.98, top=0.86, bottom=0.20, wspace=0.10)

    safe_label = label.lower().replace(" ", "_").replace("/", "_").replace("&", "and")
    out = ROOT / "viz" / f"fig_compopp_item_{item_idx:02d}_{safe_label}.jpg"
    plt.savefig(out, dpi=300, format="jpg", facecolor="white",
                pil_kwargs={"quality": 90})
    plt.close(fig)
    return out, p_rus, p_est, lev_rus, lev_est


saved = []
for i, lbl in enumerate(ITEM_LABELS, start=1):
    path, p_rus, p_est, lev_rus, lev_est = plot_item(i, lbl)
    saved.append({
        "idx": i, "label": lbl, "path": path,
        "p_rus": p_rus, "p_est": p_est,
        "lev_rus": lev_rus, "lev_est": lev_est,
    })
    print(f"    Figure: {path.name}")


# ---------- Word doc with all 12 charts embedded --------------------------
doc = Document()
section = doc.sections[0]
section.left_margin = section.right_margin = Cm(1.5)
section.top_margin = section.bottom_margin = Cm(1.8)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)

# Title page
p = doc.add_paragraph()
r = p.add_run("Comparative Opportunity Assessment — Item-Level Distribution Plots")
r.bold = True; r.font.size = Pt(15)

p = doc.add_paragraph()
r = p.add_run(
    "For each of the 12 items in the Q44 / K3X1 battery, this report shows the distribution of "
    "responses for Russian and Estonian respondents in 2020 and 2023. The visual format mirrors "
    "the polarization-check figures used for Superordinate Identity (fig_polarization_density.jpg) "
    "and Belief in Inevitable Conflict (fig_bic_density.jpg)."
); r.font.size = Pt(9.5); r.italic = True

doc.add_paragraph()

p = doc.add_paragraph()
r = p.add_run("Scale interpretation. ")
r.bold = True; r.font.size = Pt(10)
r = p.add_run(
    "All Q44 / K3X1 items use the same 1–5 response scale: 1 = \"much better for Estonians,\" "
    "3 = \"equal,\" 5 = \"much better for people of other nationalities.\" "
    "Lower scores indicate that the respondent perceives an Estonian structural advantage in that "
    "domain. The vertical light-grey line at 3 in each panel marks the \"equal opportunity\" midpoint."
); r.font.size = Pt(10)

doc.add_paragraph()

p = doc.add_paragraph()
r = p.add_run("Statistical annotations. ")
r.bold = True; r.font.size = Pt(10)
r = p.add_run(
    "Each chart's footer reports the within-group t-test p (whether the mean changed 2020 → 2023) "
    "and Levene's test p (whether the variance changed 2020 → 2023). A significant Levene's test "
    "with a non-significant t-test indicates polarization without mean shift — a finding the "
    "composite-level analysis does not surface."
); r.font.size = Pt(10)

doc.add_paragraph()

# Embed each figure with its label
for entry in saved:
    p = doc.add_paragraph()
    r = p.add_run(f"Item {entry['idx']}: {entry['label']}")
    r.bold = True; r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(0x1f, 0x29, 0x37)

    doc.add_picture(str(entry["path"]), width=Inches(6.5))

    # Brief annotation under each figure
    notable = []
    if entry["p_rus"] < .05:
        notable.append(f"Russian respondents: significant mean shift (p = {entry['p_rus']:.3f})")
    if entry["lev_rus"] < .05:
        notable.append(f"Russian respondents: significant variance change (Levene's p = {entry['lev_rus']:.3f})")
    if entry["p_est"] < .05:
        notable.append(f"Estonian respondents: significant mean shift (p = {entry['p_est']:.3f})")
    if entry["lev_est"] < .05:
        notable.append(f"Estonian respondents: significant variance change (Levene's p = {entry['lev_est']:.3f})")
    if notable:
        p = doc.add_paragraph()
        r = p.add_run("Notable: " + "; ".join(notable) + ".")
        r.font.size = Pt(8.5); r.italic = True

    doc.add_paragraph()  # spacer

# Footer note
p = doc.add_paragraph()
r = p.add_run(
    "Notes. Means are reported on the raw 1–5 Q44 scale (NOT the inverted scale used in the "
    "composite-level analysis). All t-tests are independent-samples Welch's t. Levene's tests use "
    "the median-centered version, which is robust to non-normality. Significance: *** p<.001, "
    "** p<.01, * p<.05, ns = not significant. Code 9 (\"Don't know\") was recoded to NA before "
    "computing distributions."
); r.font.size = Pt(8); r.italic = True

doc_path = ROOT / "reports" / "Comparative_Opportunity_Item_Distributions.docx"
doc.save(doc_path)
print(f"\nSaved: {doc_path}")
