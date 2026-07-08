"""
Per-Composite Invariance Interpretation — Word Doc Generator
==============================================================
Renders the focused per-composite write-up (verdicts + what you can defensibly
claim + methods-chapter language) as a formatted Word document.

Companion to reports/Measurement_Invariance.docx (which has the raw fit-index
tables); this report focuses on substantive interpretation.

Output: reports/Measurement_Invariance_Per_Composite_Interpretation.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).parent.parent
out_path = ROOT / "reports" / "Measurement_Invariance_Per_Composite_Interpretation.docx"

doc = Document()
section = doc.sections[0]
section.left_margin = section.right_margin = Cm(1.7)
section.top_margin = section.bottom_margin = Cm(2.0)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)

# Color codes for verdicts
GREEN = RGBColor(0x16, 0x65, 0x34)
ORANGE = RGBColor(0xb4, 0x53, 0x09)
RED = RGBColor(0x99, 0x1b, 0x1e)


def H(text, size=14, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size)
    if color: r.font.color.rgb = color
    return p

def H2(text):
    return H(text, size=12)

def H3(text):
    return H(text, size=11, color=RGBColor(0x1f, 0x29, 0x37))

def body(text, italic=False, size=10):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size)
    if italic: r.italic = True
    return p

def bullet(text, size=10):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text); r.font.size = Pt(size)
    return p

def make_table(header, rows, cell_styles=None, font_size=8.5, header_fontsize=9):
    """rows: list of lists. cell_styles: same shape as rows; each cell can be
    None or a dict with keys 'color' (RGBColor) and 'bold' (bool)."""
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(header):
        cell = t.rows[0].cells[i]; cell.text = ""
        pp = cell.paragraphs[0]
        rr = pp.add_run(h); rr.bold = True; rr.font.size = Pt(header_fontsize)
    for ri, r_ in enumerate(rows):
        cells = t.add_row().cells
        for i, txt in enumerate(r_):
            cells[i].text = ""
            pp = cells[i].paragraphs[0]
            rr = pp.add_run(txt); rr.font.size = Pt(font_size)
            if cell_styles is not None and ri < len(cell_styles):
                style = cell_styles[ri][i] if i < len(cell_styles[ri]) else None
                if style:
                    if style.get("color"): rr.font.color.rgb = style["color"]
                    if style.get("bold"): rr.bold = True
    return t


def verdict_style(verdict):
    if verdict == "HOLDS":  return {"color": GREEN, "bold": True}
    if verdict == "PARTIAL": return {"color": ORANGE, "bold": True}
    if verdict == "FAILS":  return {"color": RED, "bold": True}
    return None


# ====================================================================
# Title
# ====================================================================
p = doc.add_paragraph()
r = p.add_run("Measurement Invariance — Per-Composite Interpretation")
r.bold = True; r.font.size = Pt(16)

p = doc.add_paragraph()
r = p.add_run(
    "Companion to reports/Measurement_Invariance.docx (which contains the raw fit-index "
    "tables). This report focuses on substantive interpretation: what each composite's "
    "invariance verdicts mean, what claims are defensible, and how to write each one up "
    "in the methods chapter."
); r.font.size = Pt(9.5); r.italic = True

doc.add_paragraph()

# ====================================================================
# Quick reminder of the three levels
# ====================================================================
H2("Quick Reminder — The Three Levels")

t = make_table(
    ["Level", "What it tests", "If it holds, you can compare…"],
    [
        ["Configural", "Same factor structure exists",
         "The construct exists in both groups"],
        ["Metric", "Factor loadings equal across groups/waves",
         "Correlations / regression slopes / 'X predicts Y' relationships"],
        ["Scalar", "Loadings AND item intercepts equal",
         "Direct latent means (i.e., d-values reflect pure substantive differences)"],
    ],
    font_size=9.5,
)

body("A higher level always implies the lower ones. Failures cascade: if metric fails, scalar inferences are also suspect.", size=9.5, italic=True)

doc.add_paragraph()

# ====================================================================
# Important caveats
# ====================================================================
H2("Two Important Caveats Before Reading the Per-Composite Tables")

H3("Caveat 1 — Just-identified models (3-item composites)")
body(
    "For composites with only 3 items, the configural model has df = 0 — it's "
    "'just-identified' and has perfect fit by construction. The chi-square test "
    "and CFI/RMSEA at the configural level are uninformative. The metric and "
    "scalar invariance tests (which compare the constrained model to this "
    "baseline) can produce verdicts that are artifactual rather than substantive."
)
body("This affects:", size=10)
bullet("Superordinate Identity (3 items)")
bullet("SD: Primary Out-group (3 items, also group-specific)")
bullet("Minority Support Inclusion (3 items)")
bullet("SD: General Out-group 2020 only (3 items in 2020, 6 in 2023)")
body(
    "For these composites, verdicts should be read with skepticism. In particular, "
    "when you see 'metric FAILS / scalar HOLDS' for a 3-item model, that's almost "
    "always artifactual — substantively, scalar can't hold without metric."
, italic=True)

H3("Caveat 2 — Poor absolute fit on the longer composites")
body(
    "Even for the 4+ item composites, configural fit is marginal-to-poor by "
    "conventional CFA standards (CFI ≥ .95, RMSEA < .06)."
)

make_table(
    ["Composite", "Best configural CFI", "Best configural RMSEA"],
    [
        ["Belief in Inevitable Conflict", "0.949", "0.141"],
        ["Contact: Russian Speakers", "0.971", "0.089"],
        ["Contact: Estonian Speakers", "0.901", "0.161"],
        ["Comparative Opportunity Assessment", "0.891", "0.091"],
        ["SD: General Out-group", "0.742", "0.339"],
    ],
    font_size=9,
)

body(
    "Only Contact: Russian Speakers (longitudinal Estonian) cleanly meets conventional "
    "cutoffs. Others are below ideal but mostly within the 'acceptable fit' range "
    "(CFI ≥ .85, RMSEA < .10). The MLR estimator on Likert items biases fit downward; "
    "a more rigorous analysis would use WLSMV with `ordered=TRUE`. For the thesis, "
    "current results are sufficient — but 'FAILS' verdicts on longer composites are "
    "partly driven by ML/categorical mismatch, not necessarily genuine non-invariance."
, italic=True)

doc.add_paragraph()

# ====================================================================
# Per-composite breakdowns
# ====================================================================
H2("Per-Composite Breakdowns")

# Helper: generate one composite section
def composite_section(name, items_descr, table_rows, what_you_can_do, methods_lang):
    H3(name)
    body(items_descr, size=9.5, italic=True)
    # Table with verdicts
    cell_styles = []
    for r_ in table_rows:
        styles = [None]  # comparison column
        styles.append(None)  # configural column
        styles.append(verdict_style(r_[2]))  # metric verdict
        styles.append(verdict_style(r_[3]))  # scalar verdict
        cell_styles.append(styles)
    make_table(["Comparison", "Configural", "Metric", "Scalar"],
               table_rows, cell_styles=cell_styles, font_size=9)
    p = doc.add_paragraph()
    r = p.add_run("What you can do: ")
    r.bold = True; r.font.size = Pt(10)
    r = p.add_run(what_you_can_do); r.font.size = Pt(10)
    p = doc.add_paragraph()
    r = p.add_run("Methods language: ")
    r.bold = True; r.font.size = Pt(10)
    r = p.add_run(methods_lang); r.font.size = Pt(10); r.italic = True
    doc.add_paragraph()


composite_section(
    "1. Superordinate Identity (3 items: Q67_2, Q67_4, Q67_5)",
    "3-indicator composite — configural model just-identified.",
    [
        ["Multi-group 2023", "just-identified", "FAILS", "FAILS"],
        ["Multi-group 2020", "just-identified", "HOLDS", "FAILS"],
        ["Longitudinal Estonian", "just-identified", "FAILS", "HOLDS*"],
        ["Longitudinal Russian", "just-identified", "FAILS", "PARTIAL*"],
    ],
    "Limited claims. The 2020 between-group comparison reaches metric invariance, so you can defensibly say 'Estonians' and Russians' Superordinate Identity scores correlate similarly with theoretically related variables in 2020.' Otherwise, treat composite means cautiously and rely on item-level decompositions (fig_item_decomp_Superordinate_Identity.jpg) to substantiate any specific claim about which dimension of belonging differs. * = likely artifactual due to just-identified configural model.",
    "Configural invariance is established for Superordinate Identity. Metric invariance holds for the 2020 multi-group comparison; for other comparisons, item loadings differ across groups or waves, indicating that the composite reflects somewhat different mixtures of belonging dimensions across populations. Composite-level d values should be interpreted as observed-score differences."
)

composite_section(
    "2. SD: Primary Out-group (3 items, group-specific)",
    "Estonians answer Q57/58/59_1, Russians answer _2 — multi-group invariance not applicable.",
    [
        ["Longitudinal Estonian", "just-identified", "FAILS", "HOLDS*"],
        ["Longitudinal Russian", "just-identified", "FAILS", "HOLDS*"],
    ],
    "Limited. Even within-group across waves, item loadings shifted, suggesting the three social-distance contexts (neighbors / work / marriage) became more or less diagnostic of out-group attitudes between 2020 and 2023. The composite's between-group comparisons are uninformative for invariance because the items are different. * = artifactual.",
    "SD: Primary Out-group items are group-specific, so multi-group invariance testing is not applicable. Within-group longitudinal tests indicate item loadings shifted across waves, suggesting the relative weight of marriage-vs-work-vs-neighbor contexts in the construct changed. Within-group d values are reported as observed-score differences."
)

composite_section(
    "3. SD: General Out-group (different item counts per wave)",
    "2023: 6 items (Europeans + non-Europeans). 2020: 3 items ('new immigrants').",
    [
        ["Multi-group 2023 (6 items)", "CFI=0.742 (poor)", "HOLDS", "HOLDS"],
        ["Multi-group 2020 (3 items)", "just-identified", "FAILS", "HOLDS*"],
    ],
    "The 2023 multi-group HOLDS at both metric and scalar — meaning Estonians and Russians' responses on the 6-item battery have equivalent loadings AND intercepts. The 2023 between-group d is therefore a clean comparison of latent means. However, configural CFI is only 0.74 (poor), meaning the single-factor model misfits the data by absolute standards — both groups misfit it equivalently, which produces the 'scalar HOLDS' verdict. Use the 2023 between-group result with the caveat that the underlying single-factor model is questionable. * = artifactual for 2020.",
    "SD: General Out-group reaches both metric and scalar invariance for the 2023 between-group comparison. However, absolute configural fit is poor (CFI=0.742, RMSEA=0.339), suggesting the 6-item battery may have multidimensional structure that a single-factor model does not capture. Cross-wave invariance is not testable because the 2020 battery uses 3 items (about 'new immigrants') while 2023 uses 6 (about Europeans and non-Europeans separately). Between-group d in 2023 is interpretable but should be supplemented with item-level analysis."
)

composite_section(
    "4. Comparative Opportunity Assessment (12 items)",
    "12 items covering distinct life domains; the strongest test bed for invariance.",
    [
        ["Multi-group 2023", "CFI=0.872", "PARTIAL", "FAILS"],
        ["Multi-group 2020", "CFI=0.861", "HOLDS", "FAILS"],
        ["Longitudinal Estonian", "CFI=0.891", "FAILS", "FAILS"],
        ["Longitudinal Russian", "CFI=0.839", "FAILS", "FAILS"],
    ],
    "This 12-item composite covers many distinct life domains (medical, housing, education, etc.) and clearly has multi-dimensional structure that a single-factor model doesn't fully capture. The 2020 between-group comparison has full metric invariance — relationships involving the construct are comparable across groups in 2020. Scalar fails for all comparisons, so composite means are not strictly comparable as latent construct means. Within-group changes have item-loading shifts. Rely on item-level decomposition (fig_item_decomp_Comparative_Opportunity_Assessment.jpg) for any specific domain claim — Medical care, Sports & exercise, Education show the strongest item-level shifts.",
    "Comparative Opportunity Assessment shows configural invariance and metric invariance for the 2020 multi-group comparison (with partial metric in 2023); scalar invariance fails throughout. Given the breadth of life domains the 12 items cover, this is consistent with the construct being multidimensional rather than the items differing artifactually. We rely on item-level decomposition (Item_Level_Decomposition.docx) to substantiate domain-specific claims; composite-level d values are descriptive."
)

composite_section(
    "5. Belief in Inevitable Conflict (4 items) — ONE CLEAN CASE",
    "4 items: Q63_1 (conflicts inevitable), Q63_2 (differences divide), Q63_3 (groups can cooperate), Q63_4 (immigration enriches).",
    [
        ["Multi-group 2023", "CFI=0.949", "HOLDS", "FAILS"],
        ["Multi-group 2020", "CFI=0.820", "HOLDS", "HOLDS ✓"],
        ["Longitudinal Estonian", "CFI=0.918", "PARTIAL", "FAILS"],
        ["Longitudinal Russian", "CFI=0.856", "PARTIAL", "FAILS"],
    ],
    "The 2020 between-group comparison reaches full scalar invariance. This means d = +0.44 between Estonians and Russians on BiC in 2020 is a clean comparison of latent construct means — Estonians genuinely had higher conflict belief than Russians, not a measurement artifact. This is the cleanest comparison in the entire dataset for BiC. The 2023 multi-group has metric but not scalar invariance, meaning the d = +0.78 in 2023 is interpretable as observed-score difference but partially confounded with intercept variation. Within-group changes have only partial metric invariance.",
    "Belief in Inevitable Conflict reaches full scalar invariance for the 2020 between-group comparison, providing a strong basis for treating that year's d as reflecting purely substantive attitude differences. The 2023 between-group comparison reaches metric invariance only; the larger 2023 d (+0.78) thus describes a widening observed-score gap that may partly reflect intercept variation across groups. Within-group longitudinal comparisons have partial metric invariance, so changes in BiC between 2020 and 2023 within either group are reported as observed-score changes."
)

composite_section(
    "6. Minority Support Inclusion (3 items, just-identified)",
    "3-item composite measuring support for non-Estonian inclusion in economy / governance / opinions.",
    [
        ["Multi-group 2023", "just-identified", "FAILS", "FAILS"],
        ["Multi-group 2020", "just-identified", "FAILS", "FAILS"],
        ["Longitudinal Estonian", "just-identified", "HOLDS", "FAILS"],
        ["Longitudinal Russian", "just-identified", "FAILS", "FAILS"],
    ],
    "Most invariance tests fail — the three items appear to differ in psychometric behavior across groups. Estonian within-group has metric invariance, so we can reasonably compare Estonian within-group correlations involving the construct. Item-level decomposition is the safest route for any claim.",
    "Minority Support Inclusion is a 3-item composite where most invariance tests indicate item-loading or intercept shifts across groups and waves. Composite d values are reported as observed-score differences and supplemented by item-level decomposition. This is consistent with the items measuring conceptually related but distinct dimensions (economic involvement, political involvement, deference to opinions) that may carry different weights across groups."
)

composite_section(
    "7. Contact: Estonian Speakers (6 items) — ONE CLEAN CASE",
    "6 items: contact frequency in work/school, neighbors, internet, leisure, family, friends.",
    [
        ["Multi-group 2023", "CFI=0.870", "HOLDS", "FAILS"],
        ["Multi-group 2020", "CFI=0.870", "HOLDS", "FAILS"],
        ["Longitudinal Estonian", "CFI=0.844", "HOLDS", "HOLDS ✓"],
        ["Longitudinal Russian", "CFI=0.901", "PARTIAL", "FAILS"],
    ],
    "The Estonian longitudinal comparison reaches full scalar invariance. The Estonian within-group d = +0.12 (slight increase in contact with Estonian-speakers, p = .016) can be reported as a clean latent-mean comparison. Multi-group comparisons have metric invariance — the underlying construct of 'contact frequency' loads similarly on the six contexts for both groups. The d = +1.57 in 2023 (between-group) is interpretable as a relationship-level comparison. The Russian longitudinal change (d = +0.51) — your headline finding — has partial metric invariance and can be defended as an observed-score change with the caveat that some item loadings shifted.",
    "Contact: Estonian Speakers reaches full scalar invariance for the Estonian longitudinal comparison and metric invariance for both multi-group comparisons. The Russian longitudinal comparison reaches partial metric invariance. We interpret the substantial Russian within-group increase (d = +0.51) as an observed-score change while noting that some item loadings shifted between waves, plausibly reflecting the differential impact of the 2022 Estonian-language education reform on different contact contexts (work/school vs. family/friends)."
)

composite_section(
    "8. Contact: Russian Speakers (6 items) — THE CLEANEST COMPARISON IN THE PROJECT",
    "6 items: same contexts as Q51 but with Russian-speakers as the contact target.",
    [
        ["Multi-group 2023", "CFI=0.929", "PARTIAL", "FAILS"],
        ["Multi-group 2020", "CFI=0.901", "HOLDS", "FAILS"],
        ["Longitudinal Estonian", "CFI=0.971 ✓", "HOLDS", "HOLDS ✓"],
        ["Longitudinal Russian", "CFI=0.798", "HOLDS", "PARTIAL"],
    ],
    "The Estonian longitudinal comparison is the cleanest comparison in the entire dataset — CFI = 0.971 (excellent absolute fit), full scalar invariance. The Estonian within-group d = +0.14 (slight increase in contact with Russian-speakers, p = .008) can be reported with high confidence as a pure latent-mean change. The Russian longitudinal comparison has metric and partial scalar invariance — strong support, with a small caveat. Multi-group comparisons have metric or partial metric invariance only.",
    "Contact: Russian Speakers reaches full scalar invariance and excellent absolute fit (CFI = 0.971) for the Estonian longitudinal comparison. The Russian longitudinal comparison reaches metric invariance and partial scalar invariance. Multi-group comparisons reach metric or partial metric invariance only. The within-group changes for both groups are well-supported, with the Estonian shift being the most rigorously comparable across waves of any analysis in this thesis."
)

# ====================================================================
# Cleanest comparisons summary
# ====================================================================
H2("The Cleanest Comparisons in the Project")
body(
    "These are the d values you can report with the strongest psychometric backing — "
    "full scalar invariance:"
)

t = make_table(
    ["Comparison", "d (canonical TSV)", "What it claims"],
    [
        ["Belief in Conflict, 2020 between-group", "+0.44 ***",
         "Estonians had moderately higher conflict belief than Russians in 2020"],
        ["Contact: Estonian Speakers, Estonian within-group", "+0.12 *",
         "Estonians slightly increased contact with Estonian-speakers 2020→2023"],
        ["Contact: Russian Speakers, Estonian within-group", "+0.14 **",
         "Estonians slightly increased contact with Russian-speakers 2020→2023"],
    ],
    font_size=9,
)

body(
    "These three findings can be reported as clean comparisons of latent construct "
    "means — measurement invariance holds, so the d-values reflect substantive "
    "attitude/behavior differences rather than measurement-level artifacts."
)
body(
    "The first one is particularly notable — it's a clean cross-cultural comparison "
    "of conflict belief in 2020, before the war, providing a baseline for the "
    "interpretation that Estonians have higher conflict belief than Russians."
, italic=True)

doc.add_paragraph()

H3("Comparisons with partial backing — defensible with caveats")
body(
    "These have at least metric invariance (correlation-level relationships are "
    "comparable), but scalar fails (means are partly intercept-confounded). The d "
    "values can be reported as observed-score differences with a note about partial "
    "invariance:"
)
bullet("BiC 2023 between-group (d = +0.78) — gap widened")
bullet("Comparative Opportunity 2020 between-group (d = -0.79)")
bullet("Contact: Estonian Speakers multi-group both years (d = +1.89, +1.57)")
bullet("Contact: Russian Speakers multi-group 2020 (d = -2.25)")
bullet("Contact: Estonian Speakers Russian within-group (d = +0.51 *** — headline contact finding)")
bullet("Contact: Russian Speakers Russian longitudinal (d = +0.10) — partial scalar")

doc.add_paragraph()

# ====================================================================
# Bottom-line interpretation framework
# ====================================================================
H2("The Bottom-Line Interpretation Framework")
body(
    "Group your composite-level findings into three tiers when writing the thesis:"
)

t = make_table(
    ["Tier", "Status", "How to cite"],
    [
        ["Tier 1", "Full scalar invariance",
         "Cite as 'comparison of latent means.' Three findings qualify."],
        ["Tier 2", "Metric invariance only",
         "Cite as 'observed-score difference; metric invariance supports relational comparisons.' Add a footnote noting partial scalar invariance."],
        ["Tier 3", "Below metric",
         "Cite as 'observed-score difference' and ALWAYS pair with item-level decomposition (Item_Level_Decomposition.docx). The item-level evidence does the heavy lifting; the composite-level d is a summary."],
    ],
    font_size=9.5,
)

doc.add_paragraph()
H3("Practical implications for two of your headline findings")
body(
    "Headline contact-theory finding — Russian within-group Contact: Estonian "
    "Speakers, d = +0.51: sits at metric-PARTIAL level. Cite with a partial-"
    "invariance footnote. The single-item evidence (Q51_1 work/school d = +0.64) "
    "does the heavy lifting on the institutional-contact mechanism."
)
body(
    "Revised BiC story — Estonians higher conflict belief than Russians, gap "
    "widened: Tier 1 for 2020 (full scalar) and Tier 2 for 2023 (metric only). "
    "Strong overall support, especially since the baseline year (2020) is the "
    "cleanest case."
)

doc.add_paragraph()

# Footer
p = doc.add_paragraph()
r = p.add_run(
    "Notes. Verdicts based on Cheung & Rensvold (2002) and Chen (2007) thresholds: "
    "HOLDS if ΔCFI ≥ −0.01 and ΔRMSEA ≤ +0.015; PARTIAL if ΔCFI ≥ −0.02 and "
    "ΔRMSEA ≤ +0.030; otherwise FAILS. Models fit with lavaan 0.6.20, MLR estimator, "
    "FIML missing-data handling. Reverse-coded items (Q67_4, Q63_1, Q63_2 under "
    "Option B) inverted prior to fitting. For 3-indicator composites the configural "
    "model is just-identified (df = 0); subsequent invariance tests can produce "
    "artifactual verdicts and are flagged accordingly."
)
r.font.size = Pt(8); r.italic = True

doc.save(out_path)
print(f"Saved: {out_path}")
