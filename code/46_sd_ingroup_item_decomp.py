"""
Item-Level Decomposition — SD: Primary IN-GROUP (exploratory)
==================================================================================
Mirror of script 43 (SD: Primary Out-group), with the item assignment FLIPPED:

  - Estonians (rating Estonian-speakers): Q57_2 / Q58_2 / Q59_2  (2020: K4X7_2, K4X8_2, K4X9_2)
  - Russians  (rating Russian-speakers):  Q57_1 / Q58_1 / Q59_1  (2020: K4X7_1, K4X8_1, K4X9_1)

Items paired by label across groups for the between-group d. Composite-level
d is computed inline (no canonical TSV row exists for this exploratory
variable) and shown as the red dashed reference line.

Direction: scale 1–5, no reverse coding. Higher = more in-group social distance.

Output: viz/fig_item_decomp_SD_Primary_Ingroup.jpg  (300 DPI)
"""

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
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
    return s.where(s != dk).astype(float)

def m_sd_n(s):
    s = s.dropna()
    return s.mean(), s.std(ddof=1), len(s)

def cohens_d_ci(m1, sd1, n1, m2, sd2, n2):
    if any(pd.isna(x) for x in (m1, sd1, m2, sd2)) or n1 < 2 or n2 < 2:
        return np.nan, np.nan, np.nan
    s = math.sqrt((sd1**2 + sd2**2) / 2)
    if s == 0: return np.nan, np.nan, np.nan
    d = (m1 - m2) / s
    se = math.sqrt((n1 + n2) / (n1 * n2) + d**2 / (2 * (n1 + n2 - 2)))
    return d, d - 1.96 * se, d + 1.96 * se

def welch_p(a, b):
    a = a.dropna(); b = b.dropna()
    if len(a) < 2 or len(b) < 2: return np.nan
    return float(stats.ttest_ind(a, b, equal_var=False).pvalue)

def stars(p):
    if pd.isna(p): return ""
    if p < 0.001: return "***"
    if p < 0.01:  return "**"
    if p < 0.05:  return "*"
    return "ns"


# ---------- Item series (FLIPPED group-specific) ---------------------------
ITEMS = [
    {"label": "Neighbors",
     "est23": "Q57_2", "rus23": "Q57_1",
     "est20": "K4X7_2", "rus20": "K4X7_1"},
    {"label": "Work / study",
     "est23": "Q58_2", "rus23": "Q58_1",
     "est20": "K4X8_2", "rus20": "K4X8_1"},
    {"label": "Marriage in family",
     "est23": "Q59_2", "rus23": "Q59_1",
     "est20": "K4X9_2", "rus20": "K4X9_1"},
]

def fetch(df, ethval, code):
    sub = df[df["ethnicity_binary"] == ethval]
    return to_num(sub[code])

series = {}
for it in ITEMS:
    series[(it["label"], "est20")] = fetch(df20, 0, it["est20"])
    series[(it["label"], "rus20")] = fetch(df20, 1, it["rus20"])
    series[(it["label"], "est23")] = fetch(df23, 0, it["est23"])
    series[(it["label"], "rus23")] = fetch(df23, 1, it["rus23"])


# ---------- Item-level d's --------------------------------------------------
results = []
for it in ITEMS:
    lbl = it["label"]
    e20 = series[(lbl, "est20")]; r20 = series[(lbl, "rus20")]
    e23 = series[(lbl, "est23")]; r23 = series[(lbl, "rus23")]

    me, sde, ne = m_sd_n(e20); mr, sdr, nr = m_sd_n(r20)
    d, lo, hi = cohens_d_ci(me, sde, ne, mr, sdr, nr)
    p = welch_p(e20, r20)
    results.append((lbl, "between 2020", d, lo, hi, p))

    me, sde, ne = m_sd_n(e23); mr, sdr, nr = m_sd_n(r23)
    d, lo, hi = cohens_d_ci(me, sde, ne, mr, sdr, nr)
    p = welch_p(e23, r23)
    results.append((lbl, "between 2023", d, lo, hi, p))

    m20, s20, n20 = m_sd_n(e20); m23, s23, n23 = m_sd_n(e23)
    d, lo, hi = cohens_d_ci(m23, s23, n23, m20, s20, n20)
    p = welch_p(e20, e23)
    results.append((lbl, "within Estonian", d, lo, hi, p))

    m20, s20, n20 = m_sd_n(r20); m23, s23, n23 = m_sd_n(r23)
    d, lo, hi = cohens_d_ci(m23, s23, n23, m20, s20, n20)
    p = welch_p(r20, r23)
    results.append((lbl, "within Russian", d, lo, hi, p))


df_results = pd.DataFrame(results,
    columns=["item", "comparison", "d", "CI_lo", "CI_hi", "p"])
df_results["sig"] = df_results["p"].apply(stars)
print("="*92)
print("SD: PRIMARY IN-GROUP (exploratory) — item-level d's")
print("(Higher d means more in-group social distance)")
print("="*92)
print(df_results.to_string(index=False))


# ---------- Composite-level d's (inline, no canonical TSV) -----------------
def composite(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    return sub.mean(axis=1, skipna=True).dropna()

est23_c = composite(df23[df23["ethnicity_binary"]==0], ["Q57_2","Q58_2","Q59_2"])
est20_c = composite(df20[df20["ethnicity_binary"]==0], ["K4X7_2","K4X8_2","K4X9_2"])
rus23_c = composite(df23[df23["ethnicity_binary"]==1], ["Q57_1","Q58_1","Q59_1"])
rus20_c = composite(df20[df20["ethnicity_binary"]==1], ["K4X7_1","K4X8_1","K4X9_1"])

def composite_d(s_est, s_rus):
    me, sde, ne = m_sd_n(s_est); mr, sdr, nr = m_sd_n(s_rus)
    d, lo, hi = cohens_d_ci(me, sde, ne, mr, sdr, nr)
    return d, welch_p(s_est, s_rus)

CANON = {
    "between 2020":   composite_d(est20_c, rus20_c),
    "between 2023":   composite_d(est23_c, rus23_c),
    "within Estonian": composite_d(est23_c, est20_c),
    "within Russian":  composite_d(rus23_c, rus20_c),
}
print("\nComposite-level d's (computed inline for exploratory variable):")
for k, (d, p) in CANON.items():
    print(f"  {k:<18s}  d = {d:+.3f}   p = {p:.4f}  {stars(p)}")


# ---------- Plot ------------------------------------------------------------
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size":   9,
    "axes.edgecolor": "#333",
    "axes.linewidth": 0.6,
})

EST = "#2563eb"; RUS = "#d97706"
LINE_2020 = "#9ca3af"; LINE_2023 = "#1f2937"

PANEL_ORDER = [
    ("between 2020", "Between-group, 2020", LINE_2020),
    ("between 2023", "Between-group, 2023", LINE_2023),
    ("within Estonian", "Within Estonian, 2020 → 2023", EST),
    ("within Russian",  "Within Russian, 2020 → 2023", RUS),
]

fig = plt.figure(figsize=(11.0, 6.4), dpi=300)
gs = gridspec.GridSpec(2, 2, hspace=0.55, wspace=0.55,
                       left=0.18, right=0.985, top=0.83, bottom=0.12)

finite = df_results[["d", "CI_lo", "CI_hi"]].abs().max().max()
comp_max = max(abs(CANON[k][0]) for k, *_ in PANEL_ORDER)
d_max = max(finite, comp_max, 1.0)
xmin, xmax = -d_max - 0.20, d_max + 0.20

for ax_i, (cmp_key, cmp_label, color) in enumerate(PANEL_ORDER):
    ax = fig.add_subplot(gs[ax_i // 2, ax_i % 2])
    sub = df_results[df_results["comparison"] == cmp_key].copy().reset_index(drop=True)
    ys = np.arange(len(sub))[::-1]

    for i, row in sub.iterrows():
        d = row["d"]; lo = row["CI_lo"]; hi = row["CI_hi"]
        sig = row["p"] < 0.05 if pd.notna(row["p"]) else False
        y = ys[i]
        ax.barh(y, d, height=0.55, color=color,
                alpha=0.92 if sig else 0.32,
                edgecolor=color, linewidth=0, zorder=2)
        if pd.notna(lo) and pd.notna(hi):
            ax.plot([lo, hi], [y, y], color="#333", linewidth=0.9,
                    alpha=0.6, zorder=3)
            for xx in (lo, hi):
                ax.plot([xx, xx], [y - 0.12, y + 0.12], color="#333",
                        linewidth=0.9, alpha=0.6, zorder=3)
        offset = 0.03 if d >= 0 else -0.03
        ha = "left" if d >= 0 else "right"
        col = "#111" if sig else "#777"
        weight = "bold" if sig else "normal"
        ax.text(d + offset, y, f"{d:+.2f} {row['sig']}",
                ha=ha, va="center", fontsize=7.4,
                color=col, fontweight=weight)

    cd, cp = CANON[cmp_key]
    ax.axvline(cd, color="#dc2626", linewidth=1.0,
               linestyle=(0, (4, 3)), zorder=1, alpha=0.85)
    ax.text(cd, len(sub) - 0.35, f"composite d = {cd:+.2f}",
            ha="left" if cd >= 0 else "right", va="bottom",
            fontsize=7, color="#dc2626", fontweight="bold")

    ax.axvline(0, color="#333", linewidth=0.8, zorder=1)
    ax.set_yticks(ys)
    ax.set_yticklabels(sub["item"].tolist(), fontsize=8.5)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-0.7, len(sub) - 0.2)
    ax.tick_params(axis="x", length=2.5, color="#888", labelsize=7)
    ax.tick_params(axis="y", length=0)
    for s_ in ("top", "right"):
        ax.spines[s_].set_visible(False)
    ax.spines["left"].set_color("#888")
    ax.spines["bottom"].set_color("#888")
    ax.set_title(cmp_label, fontsize=10, fontweight="bold", loc="left")

# Title and footer
fig.text(0.04, 0.945,
         "Item-Level Decomposition — Social Distance: Primary IN-Group (exploratory)",
         fontsize=12.5, fontweight="bold", ha="left")
fig.text(0.04, 0.918,
         "Each bar = item-level Cohen's d. Higher d = MORE in-group social distance. "
         "Black brackets = 95% CI. Red dashed line = composite d (computed inline; not in canonical TSV).",
         fontsize=8.5, color="#444")

fig.text(0.04, 0.045,
         "Group-specific items: Estonians use Q57_2 / Q58_2 / Q59_2 (rating Estonian-speakers); Russians use Q57_1 / Q58_1 / Q59_1 (rating Russian-speakers).",
         fontsize=7, color="#555")
fig.text(0.04, 0.030,
         "Items paired by label across groups for the between-group comparison. Scale 1–5, no reverse coding (higher = more distance).",
         fontsize=7, color="#555")
fig.text(0.04, 0.015,
         "Significance: *** p<.001, ** p<.01, * p<.05.",
         fontsize=7, color="#555")

out = ROOT / "viz" / "fig_item_decomp_SD_Primary_Ingroup.jpg"
plt.savefig(out, dpi=300, format="jpg", facecolor="white",
            pil_kwargs={"quality": 95})
print(f"\nSaved: {out}")
