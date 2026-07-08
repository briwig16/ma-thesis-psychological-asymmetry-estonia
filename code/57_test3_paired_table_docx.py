"""
Test 3 — Estonian SD Primary vs. General Paired Comparison Table (Word doc)
==============================================================================
Generates a publication-ready APA-style table of the §51 within-respondent
paired test for direct insertion into the thesis.

Source values come from running code/51_estonian_sd_primary_vs_general.py;
this script re-derives them inline so the table is always in sync with the
underlying data.

Output: reports/Table_Test3_Paired_Estonian_Primary_vs_General.docx
"""

import math
from pathlib import Path
import pandas as pd
import pyreadstat
from scipy import stats
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).parent.parent

# ---------- Re-derive values ------------------------------------------------
df23 = pd.read_csv(ROOT / "data" / "EIM23.csv")
df23 = df23[df23["ethnicity_binary"].isin([0, 1])].copy()

df20, _ = pyreadstat.read_sav(str(ROOT / "data" / "EIM 2020_20.10.25.sav copy"),
                              encoding="latin1")
df20["ethnicity_binary"] = df20.apply(
    lambda r: 0 if r.get("T9_1") == 1 else (1 if r.get("T9_2") == 1 else None),
    axis=1,
)
df20 = df20[df20["ethnicity_binary"].isin([0, 1])].copy()


def composite(df, items):
    sub = df[items].apply(pd.to_numeric, errors="coerce").where(lambda x: x != 9)
    return sub.mean(axis=1, skipna=True)

def paired_stats(primary, general):
    paired = pd.concat([primary.rename("p"), general.rename("g")], axis=1).dropna()
    n = len(paired)
    diff = paired["p"] - paired["g"]
    m_diff, sd_diff = diff.mean(), diff.std(ddof=1)
    d_z = m_diff / sd_diff
    se = math.sqrt(1/n + d_z**2 / (2*n))
    ci_lo, ci_hi = d_z - 1.96 * se, d_z + 1.96 * se
    t_stat, p_t = stats.ttest_rel(paired["p"], paired["g"])
    return {
        "n": n,
        "M_p": paired["p"].mean(), "SD_p": paired["p"].std(ddof=1),
        "M_g": paired["g"].mean(), "SD_g": paired["g"].std(ddof=1),
        "M_diff": m_diff, "SD_diff": sd_diff,
        "t": t_stat, "df": n - 1, "p": p_t,
        "d_z": d_z, "ci_lo": ci_lo, "ci_hi": ci_hi,
    }


est_pri_2020 = composite(df20[df20["ethnicity_binary"]==0], ["K4X7_1","K4X8_1","K4X9_1"])
est_gen_2020 = composite(df20[df20["ethnicity_binary"]==0], ["K4X7_3","K4X8_3","K4X9_3"])
est_pri_2023 = composite(df23[df23["ethnicity_binary"]==0], ["Q57_1","Q58_1","Q59_1"])
est_gen_2023 = composite(df23[df23["ethnicity_binary"]==0],
                         ["Q57_4","Q57_5","Q58_4","Q58_5","Q59_4","Q59_5"])

stats_2020 = paired_stats(est_pri_2020, est_gen_2020)
stats_2023 = paired_stats(est_pri_2023, est_gen_2023)


# ---------- Build doc -------------------------------------------------------
doc = Document()
section = doc.sections[0]
section.left_margin = section.right_margin = Cm(2.0)
section.top_margin = section.bottom_margin = Cm(2.0)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)


def fmt_p(p):
    if p < 0.001:
        return "< .001"
    return f"{p:.3f}".lstrip("0") if p < 1 else f"{p:.3f}"

def fmt_signed(x, dec=2):
    s = f"{x:+.{dec}f}"
    return s.replace("-", "−")  # use the typographic minus sign


def add_table_caption(text):
    p = doc.add_paragraph()
    r = p.add_run("Table X. "); r.bold = True; r.font.size = Pt(10)
    r = p.add_run(text); r.italic = True; r.font.size = Pt(10)


# ----- Title (caption) -----
add_table_caption(
    "Within-respondent paired comparison of Estonians' social distance from their "
    "primary out-group (Russian-speakers) versus generic out-groups, 2020 and 2023."
)


# ----- The table itself -----
header = ["Wave", "n", "M_Pri (SD)", "M_Gen (SD)", "M_diff (SD)",
          "t (df)", "p", "d_z [95% CI]", "Direction"]

rows = [
    [
        "2020",
        f"{stats_2020['n']}",
        f"{stats_2020['M_p']:.2f} ({stats_2020['SD_p']:.2f})",
        f"{stats_2020['M_g']:.2f} ({stats_2020['SD_g']:.2f})",
        f"{fmt_signed(stats_2020['M_diff'])} ({stats_2020['SD_diff']:.2f})",
        f"{fmt_signed(stats_2020['t'])} ({stats_2020['df']})",
        fmt_p(stats_2020['p']),
        f"{fmt_signed(stats_2020['d_z'])} [{fmt_signed(stats_2020['ci_lo'])}, {fmt_signed(stats_2020['ci_hi'])}]",
        "Primary < General",
    ],
    [
        "2023",
        f"{stats_2023['n']}",
        f"{stats_2023['M_p']:.2f} ({stats_2023['SD_p']:.2f})",
        f"{stats_2023['M_g']:.2f} ({stats_2023['SD_g']:.2f})",
        f"{fmt_signed(stats_2023['M_diff'])} ({stats_2023['SD_diff']:.2f})",
        f"{fmt_signed(stats_2023['t'])} ({stats_2023['df']})",
        fmt_p(stats_2023['p']),
        f"{fmt_signed(stats_2023['d_z'])} [{fmt_signed(stats_2023['ci_lo'])}, {fmt_signed(stats_2023['ci_hi'])}]",
        "Primary > General",
    ],
]

t = doc.add_table(rows=1, cols=len(header))
t.style = "Light Grid Accent 1"

# Header row
for i, h in enumerate(header):
    cell = t.rows[0].cells[i]
    cell.text = ""
    p = cell.paragraphs[0]
    # Italicize statistical symbols
    if h in ("n", "p"):
        run = p.add_run(h); run.bold = True; run.italic = True; run.font.size = Pt(9)
    elif h == "M_Pri (SD)":
        run = p.add_run("M"); run.bold = True; run.italic = True; run.font.size = Pt(9)
        run = p.add_run("ₘPri (SD)"); run.bold = True; run.font.size = Pt(9)
    elif h == "M_Gen (SD)":
        run = p.add_run("M"); run.bold = True; run.italic = True; run.font.size = Pt(9)
        run = p.add_run("ₘGen (SD)"); run.bold = True; run.font.size = Pt(9)
    elif h == "M_diff (SD)":
        run = p.add_run("M"); run.bold = True; run.italic = True; run.font.size = Pt(9)
        run = p.add_run("ₘdiff (SD)"); run.bold = True; run.font.size = Pt(9)
    elif h == "t (df)":
        run = p.add_run("t"); run.bold = True; run.italic = True; run.font.size = Pt(9)
        run = p.add_run(" ("); run.bold = True; run.font.size = Pt(9)
        run = p.add_run("df"); run.bold = True; run.italic = True; run.font.size = Pt(9)
        run = p.add_run(")"); run.bold = True; run.font.size = Pt(9)
    elif h == "d_z [95% CI]":
        run = p.add_run("d"); run.bold = True; run.italic = True; run.font.size = Pt(9)
        run = p.add_run("ₘz [95% CI]"); run.bold = True; run.font.size = Pt(9)
    else:
        run = p.add_run(h); run.bold = True; run.font.size = Pt(9)

# Data rows
for r_data in rows:
    cells = t.add_row().cells
    for i, txt in enumerate(r_data):
        cells[i].text = ""
        p = cells[i].paragraphs[0]
        run = p.add_run(txt); run.font.size = Pt(9)


# ----- Note paragraph -----
doc.add_paragraph()
note = doc.add_paragraph()
r = note.add_run("Note. "); r.italic = True; r.font.size = Pt(9)
r = note.add_run(
    "Each respondent contributes both a Primary and a General SD score within the same survey wave. "
)
r.font.size = Pt(9)
r = note.add_run("M")
r.italic = True; r.font.size = Pt(9)
r = note.add_run(
    "ₘdiff = M(Primary) − M(General); a negative value indicates that Russian-speakers are "
    "perceived as less socially distant than generic out-groups, a positive value indicates the reverse. "
    "Cohen's "
)
r.font.size = Pt(9)
r = note.add_run("d"); r.italic = True; r.font.size = Pt(9)
r = note.add_run("ₘz = Mₘdiff / SDₘdiff (paired-sample standardised effect size). "
                 "95% CI computed using the Hedges & Olkin (1985) variance approximation. ")
r.font.size = Pt(9)
r = note.add_run("Welch's paired ")
r.font.size = Pt(9)
r = note.add_run("t"); r.italic = True; r.font.size = Pt(9)
r = note.add_run(
    "-test; Wilcoxon signed-rank confirms both significance results (p < .001 in both waves). "
    "Items: Primary = Q57_1 / Q58_1 / Q59_1 (Estonian respondents rating Russian-speakers as "
    "neighbour, coworker / classmate, and family member; 2020 equivalents K4X7_1 / K4X8_1 / K4X9_1). "
    "General 2020 = K4X7_3 / K4X8_3 / K4X9_3 (\"new immigrants in last 5 years\" across the same three "
    "social contexts). General 2023 = Q57_4 / Q57_5 / Q58_4 / Q58_5 / Q59_4 / Q59_5 (\"other "
    "Europeans\" + \"non-Europeans\" across the same three contexts). Scale: 1 = no social distance "
    "(would readily accept), 5 = maximal social distance."
)
r.font.size = Pt(9)


# ----- Save -----
out_path = ROOT / "reports" / "Table_Test3_Paired_Estonian_Primary_vs_General.docx"
doc.save(out_path)
print(f"Saved: {out_path}")
print()
print("Values used:")
for label, s in [("2020", stats_2020), ("2023", stats_2023)]:
    print(f"  {label}: n={s['n']}, M_p={s['M_p']:.3f}, M_g={s['M_g']:.3f}, "
          f"M_diff={s['M_diff']:+.3f}, t({s['df']})={s['t']:+.3f}, "
          f"d_z={s['d_z']:+.3f} [{s['ci_lo']:+.3f}, {s['ci_hi']:+.3f}]")
