"""
Full-Project Blindspot Audit (Round 4) — Word Doc Generator
================================================================
Comprehensive audit of the EIM2 project across eight layers:
  1. Research design
  2. Construct construction
  3. Analytical choices
  4. Substantive findings
  5. Theoretical framing
  6. Methodology limitations
  7. Internal consistency
  8. Documentation drift

Each finding tagged HIGH / MEDIUM / LOW for action priority. Ends with a
consolidated prioritized action checklist.

Output: reports/Blindspot_Full_Project_Audit_2026-05-03.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor

ROOT = Path(__file__).parent.parent
out_path = ROOT / "reports" / "Blindspot_Full_Project_Audit_2026-05-03.docx"

doc = Document()
section = doc.sections[0]
section.left_margin = section.right_margin = Cm(2.0)
section.top_margin = section.bottom_margin = Cm(2.0)
doc.styles["Normal"].font.name = "Calibri"
doc.styles["Normal"].font.size = Pt(10)


def H(text, size=14, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.size = Pt(size)
    if color: r.font.color.rgb = color

def H2(text, color=None):
    H(text, size=12, color=color)

def H3(text):
    H(text, size=11)

def body(text, italic=False, size=10, color=None):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size)
    if italic: r.italic = True
    if color: r.font.color.rgb = color

def bullet(text, size=10):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text); r.font.size = Pt(size)

def severity_tag(level):
    """Inline severity badge using a paragraph with colored text."""
    p = doc.add_paragraph()
    if level == "HIGH":
        color = RGBColor(0xb9, 0x1c, 0x1c); label = "[ HIGH ] "
    elif level == "MEDIUM":
        color = RGBColor(0xb4, 0x53, 0x09); label = "[ MEDIUM ] "
    else:
        color = RGBColor(0x4b, 0x55, 0x63); label = "[ LOW ] "
    r = p.add_run(label); r.bold = True; r.font.size = Pt(10); r.font.color.rgb = color
    return p

def finding(level, title, text, p_obj=None):
    """Add a severity-tagged finding. The title goes inline after the badge."""
    p = doc.add_paragraph()
    if level == "HIGH":
        color = RGBColor(0xb9, 0x1c, 0x1c); label = "[ HIGH ] "
    elif level == "MEDIUM":
        color = RGBColor(0xb4, 0x53, 0x09); label = "[ MEDIUM ] "
    else:
        color = RGBColor(0x4b, 0x55, 0x63); label = "[ LOW ] "
    r = p.add_run(label); r.bold = True; r.font.size = Pt(10); r.font.color.rgb = color
    r = p.add_run(title); r.bold = True; r.font.size = Pt(10)
    body(text)


def make_table(header, rows):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(header):
        cell = t.rows[0].cells[i]; cell.text = ""
        rr = cell.paragraphs[0].add_run(h); rr.bold = True; rr.font.size = Pt(9)
    for r_ in rows:
        cells = t.add_row().cells
        for i, txt in enumerate(r_):
            cells[i].text = ""
            rr = cells[i].paragraphs[0].add_run(txt); rr.font.size = Pt(8.5)


# ===========================================================================
# Title block
# ===========================================================================
H("Full-Project Blindspot Audit", size=16, color=RGBColor(0x1f, 0x29, 0x37))
H("EIM2 Master's Thesis — Estonian–Russian Intergroup Relations", size=11,
  color=RGBColor(0x4b, 0x55, 0x63))

p = doc.add_paragraph()
r = p.add_run("Date: "); r.bold = True; r.font.size = Pt(10)
r = p.add_run("2026-05-03"); r.font.size = Pt(10)

p = doc.add_paragraph()
r = p.add_run("Scope: "); r.bold = True; r.font.size = Pt(10)
r = p.add_run(
    "End-to-end audit of the entire project — research design, composite construction, "
    "analytical choices, substantive findings, theoretical framing, methodology limitations, "
    "internal consistency across files, and documentation drift. Differs from Rounds 2 and 3, "
    "which audited only changes since the previous round."
); r.font.size = Pt(10)

p = doc.add_paragraph()
r = p.add_run("Severity scheme: "); r.bold = True; r.font.size = Pt(10)
r = p.add_run("HIGH = act before thesis submission; MEDIUM = worth addressing; "
              "LOW = housekeeping. Findings within a layer are ordered by severity, "
              "highest first.")
r.font.size = Pt(10)

doc.add_paragraph()
body(
    "This audit was carried out by re-reading CLAUDE.md, _effect_sizes.tsv, "
    "_invariance_results.tsv, _item_decomposition.tsv, build_all.py, the reports/ "
    "folder contents, and a sample of pipeline scripts, then cross-checking claims and "
    "values against each other. It is a perceptual audit, not a code-correctness audit "
    "(those have been performed by Referee 2 in Rounds 1–3). The questions asked here "
    "are: are the project's claims internally coherent? Have any decisions silently drifted? "
    "Are there things baked into the pipeline that no longer match what is being said about it?",
    italic=True
)


# ===========================================================================
# Headline verdict
# ===========================================================================
H2("Headline Verdict")
body(
    "CONDITIONAL — the analytical core of the project is sound. Composite construction, "
    "Cohen's d formulas, missing-value handling, and significance reporting are all internally "
    "consistent and have been independently verified by Referee 2 (Round 3: 444/444 Python + "
    "440/440 R audit checks pass). The substantive findings are well-grounded in the data."
)
body(
    "However, the project has accumulated NINE actionable items that should be addressed "
    "before thesis submission. Three are genuine analytical gaps (Russian sample composition, "
    "scalar-invariance caveats not yet propagated to figure narratives, and the construct-change "
    "qualification on cross-year SD: General comparisons). Six are documentation / "
    "reproducibility issues (build pipeline staleness, sample-size inconsistencies, orphaned "
    "files, missing CLAUDE.md entries for Round 3 work, legacy regression scripts left in place, "
    "and reports-folder cleanup). None of these invalidate any finding; together they create "
    "thesis-examiner exposure that is straightforward to close."
)


# ===========================================================================
# LAYER 1 — Research design
# ===========================================================================
doc.add_paragraph()
H2("Layer 1 — Research Design", color=RGBColor(0x1f, 0x29, 0x37))

finding("LOW",
    "Sample restriction (ethnicity_binary in [0, 1]): defensible, well-documented.",
    "Excluding respondents who self-identify as neither Estonian nor Russian is an explicit "
    "design choice tied to the research question (psychological asymmetry between the two "
    "primary ethnic groups). The exclusion is documented in CLAUDE.md and applied uniformly. "
    "Acknowledged limitation: the project does not speak to other ethnic minorities in Estonia. "
    "For thesis chapter, this should be a one-sentence scope clarification."
)
finding("LOW",
    "Ethnicity classification mismatch across years (T8 in 2023 vs. T9 in 2020).",
    "Per CLAUDE.md, 2023 uses T8 ('which nationality do you consider yourself to be MAINLY?') "
    "while 2020 uses T9_1 / T9_2 (self-identified nationality checkboxes). Both measure the "
    "same construct (self-identified nationality), and the swap from T7 (communication language) "
    "was a deliberate Mar 28 correction. The cross-year construct equivalence is reasonable but "
    "not formally tested. For the thesis methods chapter, note that the two measures differ in "
    "presentation (single-select vs. checkbox) even though both target self-identification."
)
finding("LOW",
    "DK-as-NaN universal recoding: appropriate for analytical purposes.",
    "All composites recode 'don't know' (code 9, sometimes 6) to NaN before analysis. This is "
    "standard practice but it does treat 'don't know' as MCAR (missing completely at random), "
    "which is unlikely. Some composites — Institutional Trust, dropped — had ~49% DK among "
    "Russians (almost certainly MNAR). For included composites, DK rates are much lower, but "
    "the implicit MCAR assumption should be acknowledged in the methods chapter."
)


# ===========================================================================
# LAYER 2 — Construct construction
# ===========================================================================
doc.add_paragraph()
H2("Layer 2 — Construct Construction", color=RGBColor(0x1f, 0x29, 0x37))

finding("MEDIUM",
    "BiC composite recode (Apr 30, Option B): correctly applied across pipeline, but documentation in CLAUDE.md is dense and easy to mis-read.",
    "The Apr 30 recode (reverse-coding switched from Q63_3/Q63_4 to Q63_1/Q63_2) flipped the "
    "sign of every BiC d in the canonical TSV. CLAUDE.md documents this thoroughly, but the "
    "decision-table entry is one massive block of text with the substantive interpretation "
    "buried at the end. A reader skimming would miss the sign reversal. Recommend extracting "
    "the substantive consequence ('Russians DECREASED conflict belief; Estonians have HIGHER "
    "conflict belief than Russians; the gap WIDENED') into a clearly visible summary box at "
    "the top of CLAUDE.md or in the methods chapter."
)
finding("MEDIUM",
    "Q67_4 inversion bug history (Apr 30): fixed in scripts 31/32/33 but not flagged in chart titles or captions.",
    "The Q67_4 single-item charts had a single-inversion bug fixed Apr 30 (raw direction "
    "already aligns with 'higher = more belonging'; the additional 5 − raw inversion was "
    "removed). The fix is documented in SESSION_LOG §31d-bis. The current charts produced by "
    "scripts 31/32/33 are correct, but neither the chart titles nor captions flag the fix or "
    "the changed sign of the Q67_4 within-group d's. A reader comparing charts to earlier "
    "versions of the analysis (or to old Slack screenshots, etc.) could be confused."
)
finding("LOW",
    "Visualization inversions (5 − x): 5 composites flipped for HTML viz only.",
    "The dumbbell chart and mind map invert Superordinate Identity, Comparative Opportunity, "
    "Minority Support, both Contact composites, and Territorial Attachment so that 'higher = "
    "more of the construct.' These inversions apply ONLY to HTML viz, not to raw composites or "
    "SESSION_LOG tables. The convention is documented in CLAUDE.md, but a thesis examiner "
    "cross-checking a chart number against a TSV value would see different signs and could "
    "wonder whether something is wrong. Suggest adding a one-line marginal note on the inverted "
    "charts: 'Direction inverted for visualization; canonical TSV uses opposite sign.'"
)
finding("LOW",
    "SD: Primary uses group-specific items (a recurring footgun documented in CLAUDE.md).",
    "Estonians rate Russian-speakers (Q57_1/Q58_1/Q59_1); Russians rate Estonian-speakers "
    "(Q57_2/Q58_2/Q59_2). The CLAUDE.md 'Critical Gotchas' section flags this explicitly. The "
    "construction is correct everywhere it is used. No action needed beyond keeping the gotcha "
    "comment visible."
)


# ===========================================================================
# LAYER 3 — Analytical choices
# ===========================================================================
doc.add_paragraph()
H2("Layer 3 — Analytical Choices", color=RGBColor(0x1f, 0x29, 0x37))

finding("LOW",
    "Cohen's d formula (root-mean-square SD): non-standard but explicit.",
    "The project uses d = (M1 − M2) / sqrt((SD1² + SD2²)/2), the root-mean-square SD form, "
    "rather than the more common pooled-SD form. CLAUDE.md and SESSION_LOG document this "
    "choice and note the difference is 0.03–0.09 in absolute terms vs. classic Cohen's d. The "
    "choice is justified by reproducibility against the 2026-03-28 reported values. For thesis "
    "methods chapter, cite the formula explicitly and note that it differs from textbook "
    "Cohen's d so a reader recomputing from M's and SD's gets matching numbers."
)
finding("LOW",
    "Welch's t (not Student's): correct for unequal variances.",
    "Used uniformly. Appropriate given the substantial SD differences across groups (Estonian "
    "and Russian samples have visibly different dispersions on most composites, formally "
    "confirmed by the Levene's tests in SESSION_LOG §30 and the Round 3 analyses)."
)
finding("LOW",
    "Pairwise vs. listwise composite construction: rationale documented.",
    "Composite scores use pandas' default pd.DataFrame.mean(axis=1, skipna=True), i.e., "
    "pairwise deletion. PCA and Cronbach's alpha use listwise deletion. CLAUDE.md notes the "
    "difference and its implication (composite N > PCA N for the same variable). The Apr 29 "
    "decision to make pairwise the canonical approach across all effect-size computations is "
    "documented. No action."
)
finding("LOW",
    "Single-factor decisions despite 2-component Kaiser for Q44 and the contact composites: "
    "justified theoretically, all alphas > .73.",
    "The decisions to retain single-factor solutions for Q44 (alpha > .88), the in-group "
    "contact composites, and the Russian SD pooled solution are documented in CLAUDE.md "
    "decisions table (Mar 23). Each decision is paired with an alpha threshold or "
    "theoretical-coherence rationale. No action."
)


# ===========================================================================
# LAYER 4 — Substantive findings
# ===========================================================================
doc.add_paragraph()
H2("Layer 4 — Substantive Findings", color=RGBColor(0x1f, 0x29, 0x37))

finding("HIGH",
    "Item-level cross-direction divergences (Q68_3 'Understand opinions' and Q63_2 'Differences divide society') are now well-documented in figures but UNDER-INTEGRATED INTO THE NARRATIVE.",
    "Two items show Estonian and Russian within-group changes BOTH significant and OPPOSITE in "
    "direction: Q68_3 (Est −0.16 **, Rus +0.23 ***) and Q63_2 (Est +0.26 ***, Rus −0.21 ***). "
    "Both are now amber-highlighted in the item-decomposition charts (May 3). Substantively "
    "they are the strongest available evidence for 'asymmetric divergence' as a phenomenon "
    "rather than parallel-but-different change. Currently they appear only as item-level "
    "footnotes; they should be promoted to a stand-alone finding in the discussion chapter, "
    "ideally with their own table or figure."
)
finding("HIGH",
    "The §51 Estonian Primary-vs-General sign-reversal is the single sharpest finding the project has, "
    "but its current write-up presentation does not match its centrality.",
    "The §51 paired test (within-respondent) shows that the rank order between Russian-speakers "
    "(Primary) and generic out-groups (General) FLIPPED for Estonians between 2020 and 2023. "
    "The Round 3 Blindspot recommended this be promoted to a key thesis finding with a proper "
    "table (now produced as Table_Test3). The substantive interpretation chain ('rules out "
    "non-targeted hardening') is also worked out. What remains: ensure the thesis discussion "
    "chapter actually treats this as the headline result rather than as a §51 supplement."
)
finding("MEDIUM",
    "Convergent fragmentation across five Estonian dimensions: solid evidence, well-positioned for promotion.",
    "Levene's-test-significant variance growth on the Estonian side appears in: Superordinate "
    "Identity (p < .001), Group ID Patterns (variance grew), Belief in Inevitable Conflict "
    "(p < .001), Minority Inclusion Support (p = .001), and SD: Primary Out-group composite "
    "(p = .001) and Work / study item (p = .003). Five distinct intergroup constructs showing "
    "the same dispersion-grows pattern is a strong convergent signature. Currently this appears "
    "across multiple SESSION_LOG sections and one Blindspot report; it should be consolidated "
    "into a single 'fragmentation pattern' subsection in the thesis discussion."
)
finding("MEDIUM",
    "SD: Primary public-vs-intimate gradient: real sub-finding, currently missing from the writeup.",
    "Within-Estonian SD: Primary item d's are Neighbors +0.41 ***, Work / study +0.44 ***, "
    "Marriage +0.22 ***. The most intimate item (marriage) shows half the magnitude of the "
    "public/civic items. Two interpretations are viable: (i) the shift is principally about "
    "public / civic life, not personal/family relations; (ii) marriage is at floor in 2020 and "
    "has less room to grow. Round 3 Blindspot recommended a quick distribution check to "
    "discriminate, plus a one- or two-sentence sub-finding paragraph. Neither has been done."
)


# ===========================================================================
# LAYER 5 — Theoretical framing
# ===========================================================================
doc.add_paragraph()
H2("Layer 5 — Theoretical Framing", color=RGBColor(0x1f, 0x29, 0x37))

finding("HIGH",
    "The 'asymmetric divergence under external shock' reframing has been internalized but the WORD-LEVEL claim language is still inconsistent across documents.",
    "Various phrasings appear across CLAUDE.md, SESSION_LOG, and the Blindspot reports: "
    "'psychological asymmetry,' 'asymmetric attitude divergence under shock,' 'targeted "
    "hardening,' 'rules out non-targeted hardening,' 'convergent fragmentation,' 'broadly "
    "liberalizing.' These are all describing related claims, but a thesis examiner will read "
    "them as distinct theoretical propositions. Recommend: write a single one-paragraph "
    "theoretical-claim statement (the 'thesis sentence') and use that exact wording everywhere "
    "the framing is invoked."
)
finding("MEDIUM",
    "Falsification logic: now correctly scoped to 'rules out non-targeted hardening' in Round 3 Blindspot, but the Round 2 §29 framing still says 'falsifies generalized hardening.'",
    "SESSION_LOG §29 (Apr 29) frames the Estonian Primary-vs-General divergence as a "
    "falsification test for 'generalized hardening.' The Round 3 Blindspot (May 2) Flag 7 "
    "weakened this to 'rules out non-targeted hardening' (the actually-supported claim). "
    "SESSION_LOG §29 has not been updated to reflect this. Either revise §29 or add a "
    "marginal note saying 'See Blindspot Round 3 Flag 7 for revised falsification claim.'"
)
finding("MEDIUM",
    "Contact-theory connection (Russians' contact UP + conflict belief DOWN): consistent with classical Allport contact theory, but never explicitly cited.",
    "After the BiC recode (Apr 30), the within-Russian pattern of increased contact and "
    "decreased belief in inevitable conflict is exactly what contact theory predicts. This "
    "dissolves the §29 'paradox' and points toward a strong theoretical-grounding opportunity. "
    "Currently mentioned in the BiC recode entry (CLAUDE.md decisions table, Apr 30) but never "
    "developed. For the thesis discussion, this is a one-paragraph theoretical-anchoring win "
    "that should not be left on the table."
)


# ===========================================================================
# LAYER 6 — Methodology limitations
# ===========================================================================
doc.add_paragraph()
H2("Layer 6 — Methodology Limitations", color=RGBColor(0x1f, 0x29, 0x37))

finding("HIGH",
    "Russian sample composition shift (~609 → ~520) STILL UNINVESTIGATED — Round 2 FLAG 1, now eight days old.",
    "The Russian respondent N dropped from ~609 (2020, T9 classification) to ~520 (2023, T8 "
    "classification), per canonical TSV. This was raised in Round 2 Blindspot §29 FLAG 1 "
    "(Apr 29) and re-raised in Round 3 Blindspot Flag 3 (May 2). Still not closed. If "
    "conservative Russian respondents selectively dropped out between waves (e.g., due to "
    "war-related disengagement from civic surveys), every within-Russian d in the project — "
    "including the 'Russian liberalization' headline — is biased in the liberalizing direction. "
    "The minimum useful check is: (1) cross-tab age, education, and region for the Russian "
    "subsample in 2020 vs. 2023; (2) if a noticeable shift exists, re-estimate the within-"
    "Russian d's with post-stratification weights or covariate adjustment. Should be the #1 "
    "pre-submission action item."
)
finding("HIGH",
    "Scalar-invariance caveats not yet propagated to figure captions for BiC and Minority Support within-group findings.",
    "§33 measurement invariance established that scalar invariance HOLDS longitudinally for "
    "SD: Primary (both groups) but FAILS for BiC and Minority Support (both groups). The "
    "within-Russian BiC d = −0.32 *** and within-Estonian Minority Support d = −0.15 ** "
    "therefore describe observed score differences whose latent-mean comparability is not "
    "established. CLAUDE.md and the Measurement_Invariance_Per_Composite_Interpretation.docx "
    "document this; the chart captions and the discussion-chapter prose should also reflect "
    "it. Round 3 Blindspot Flag 2 recommended adding the caveat to chart captions; this has "
    "not been done."
)
finding("MEDIUM",
    "Cross-year SD: General construct change (2020: 'new immigrants' [3 items]; 2023: 'other Europeans' + 'non-Europeans' [6 items]): documented in CLAUDE.md, but not flagged consistently in chart annotations or discussion prose.",
    "Within-group SD: General d's compare a 3-item 2020 battery to a 6-item 2023 battery with "
    "a different target population. CLAUDE.md flags this as 'cross-year measures different "
    "construct.' The §50 (4×3 SD General item-density figure) handles this by overlaying the "
    "2020 baseline against both 2023 sub-targets, which is good visual practice. The §54 / §55 "
    "Primary-vs-General comparison figures inherited the caveat. The §48 / §49 charts mention "
    "it. But it is not consistently flagged in the figure captions where the within-group "
    "SD: General d is cited."
)
finding("MEDIUM",
    "Ukrainian-item exclusion: explicit and defensible, but creates a partial-truth problem in 'Russian liberalization' framing.",
    "The 2023 SD: General excludes Ukrainian items per the 2026-03-23 decision (Russians held "
    "asymmetrically negative views of Ukrainian refugees, masking otherwise positive general-"
    "out-group attitudes). Methodologically defensible. But the headline 'Russians liberalized "
    "toward general out-groups' is therefore partial — it covers generic Europeans + "
    "non-Europeans, not the most policy-salient post-2022 immigrant population. Round 3 "
    "Blindspot Flag 4 recommended either plotting the dropped Ukrainian items separately or "
    "adding a paragraph clarifying the scope. Not done."
)


# ===========================================================================
# LAYER 7 — Internal consistency
# ===========================================================================
doc.add_paragraph()
H2("Layer 7 — Internal Consistency Across Files", color=RGBColor(0x1f, 0x29, 0x37))

finding("MEDIUM",
    "Sample-size headline numbers in CLAUDE.md don't exactly match the canonical TSV per-composite max.",
    "CLAUDE.md states: '2020 N: 706 Estonian, 609 Russian; 2023 N: 870 Estonian, 522 Russian.' "
    "Canonical TSV per-composite max: 2020 N = 702 Est / 607 Rus; 2023 N = 865 Est / 521 Rus. "
    "Discrepancy of 4–5 in each cell. Likely the CLAUDE.md figure is the unfiltered "
    "ethnicity_binary count and the per-composite max is after composite-level missing-data "
    "filtering. Worth either reconciling (state both numbers in CLAUDE.md with a sentence "
    "explaining the difference) or correcting one of them. Examiner will spot this if the "
    "headline N is cited in the thesis abstract."
)
finding("MEDIUM",
    "'Minority Support Inclusion' (canonical) vs 'Minority Inclusion Support' (chart labels): half-renamed.",
    "On 2026-05-03 the chart-label name was changed to 'Minority Inclusion Support' in scripts "
    "39, 40, 41, and 58. The canonical TSV, _item_decomposition.tsv, _invariance_results.tsv, "
    "the build pipeline (24/29/etc.), and the referee2 audit scripts all still use 'Minority "
    "Support Inclusion.' This is a deliberate scope decision (renaming the canonical name "
    "would cascade through 884 audit checks), but it is not documented in CLAUDE.md. Worth "
    "either adding a one-line note in CLAUDE.md ('User-facing name = Minority Inclusion "
    "Support; canonical-pipeline name = Minority Support Inclusion') or doing a full rename "
    "with a re-audit."
)
finding("LOW",
    "Q44 has 12 items in the 2023 CSV (matches CLAUDE.md table).",
    "Header count of EIM23.csv confirms 12 Q44_* items. Matches CLAUDE.md composite #4 spec."
)
finding("LOW",
    "Invariance verdict counts in CLAUDE.md decisions table match the canonical _invariance_results.tsv.",
    "CLAUDE.md (Apr 30 entry, Pending Item #9): 'metric HOLDS in 12, PARTIAL in 5, FAILS in 11; "
    "scalar HOLDS in 8, PARTIAL in 2, FAILS in 18.' Canonical TSV recount confirms exact match."
)


# ===========================================================================
# LAYER 8 — Documentation drift
# ===========================================================================
doc.add_paragraph()
H2("Layer 8 — Documentation Drift", color=RGBColor(0x1f, 0x29, 0x37))

finding("HIGH",
    "build_all.py is STALE — 27 of the 61 numbered scripts in code/ are NOT in the build pipeline, including ALL of the May 1–3 Round 3 work (scripts 39–58).",
    "The build pipeline currently includes scripts 01–05, 10, 19–30, 36–38, plus a handful of "
    "older PCA scripts. It does NOT include scripts 06–09, 11–18, 31–35, or 39–58. That means "
    "the entire Round 3 wave of analysis — the §51 paired test, all the Primary-vs-General "
    "comparison figures, the Minority / SD Primary / SD General item-density and item-"
    "decomposition figures, the Round 3 Blindspot generator, the Test 3 paired-table generator, "
    "and the focused between-group bar chart — is not part of the reproducible CI gate. If the "
    "canonical TSV is regenerated, these outputs will not auto-rebuild. Highest priority "
    "documentation-layer fix: add the Round 3 scripts to build_all.py as Stage 8."
)
finding("HIGH",
    "CLAUDE.md decisions table has NO entries dated 2026-05 — all of Round 3 is undocumented in the canonical project ledger.",
    "Last entry in the decisions table is 2026-04-30 (BiC recode). Since then: (Round 3 work) "
    "the §51 paired test, the sign-reversal finding, the focused between-group chart, the "
    "amber-highlight scheme for divergent items, the Q68 / Q63 cross-direction divergence "
    "findings, the Test 3 publication table, and the Round 3 Blindspot have all happened. None "
    "appear in CLAUDE.md. A reader returning to the project after a break would see 'Phase: "
    "Thesis figure preparation / write-up' and assume nothing substantive has occurred since "
    "Apr 30. Recommend adding 4–6 decision-table entries summarizing the Round 3 wave."
)
finding("MEDIUM",
    "Orphaned in-group SD outputs in viz/ (3 files) — produced May 1, dropped from analysis the same day.",
    "viz/ contains fig_sd_ingroup_density.jpg, fig_sd_ingroup_item_density.jpg, and "
    "fig_item_decomp_SD_Primary_Ingroup.jpg. These were produced May 1 by scripts 45–47, then "
    "abandoned the same day after the in-group analysis was determined to be structurally "
    "non-interpretable (N = 21–51 per cell, almost certainly a survey-routing artifact). "
    "Anyone browsing viz/ might re-discover and misuse them. Recommend either deleting the "
    "JPEGs and the source scripts, or moving them to a viz/abandoned/ subfolder with a "
    "README explaining they were dropped."
)
finding("MEDIUM",
    "Legacy regression scripts in code/regression/ (4 files) — analysis dropped from thesis but scripts remain.",
    "code/regression/ contains regression_analysis.py, regression_estonian.py, "
    "regression_russian.py, and visualize_regressions.py. CLAUDE.md decisions table (Mar 28) "
    "states 'Regression analysis dropped from thesis scope. Existing regression scripts in "
    "code/regression/ are legacy.' The scripts use the OLD 4-item belonging composite (also "
    "deprecated). Anyone running them will produce wrong results that look right. Recommend "
    "either deleting the directory or adding a header comment to each script that says "
    "'DEPRECATED — uses old 4-item composite, do not run.'"
)
finding("LOW",
    "reports/ folder cleanliness: stray 'copy' files and Word lock files.",
    "reports/ contains 'Blindspot_Report_2026-04-29 copy.docx', 'Effect_Sizes_with_CI copy.docx,' "
    "and Word lock files starting with '~$'. The 'copy' files are duplicates from manual file-"
    "system operations; the lock files are from open-Word artifacts. Cleanup: delete the four "
    "stray files. Also reports/old/ contains pre-Round-3 superseded reports per the Apr 29 "
    "cleanup entry — that is intentional and well-organized."
)


# ===========================================================================
# Confirmations
# ===========================================================================
doc.add_paragraph()
H2("Confirmations — what the project does well", color=RGBColor(0x1f, 0x29, 0x37))

bullet(
    "Code-correctness audit trail: Referee 2 has run three rounds (Mar 27, Mar 28, Apr 29) "
    "and the audit infrastructure (replication scripts in code/replication/, both Python and R) "
    "is mature. Round 3 passes 444/444 Python checks and 440/440 R checks. The cross-language "
    "verification is unusual for a master's thesis and should be cited as a strength."
)
bullet(
    "Decision provenance: every substantive analytical decision has a CLAUDE.md table entry "
    "with date and rationale, including reverse-coding choices, dropped analyses, and item "
    "exclusions. Drift can be checked against this table."
)
bullet(
    "Composite-construction discipline: pairwise vs. listwise rules, scale directions, and "
    "reverse-coding decisions are uniformly applied across the 8 multi-item composites. "
    "Independent recomputation matches the canonical TSV."
)
bullet(
    "Visualization quality: the Round 3 chart wave (composite densities, item-decomposition, "
    "item densities) gives the project a publication-grade figure inventory across all major "
    "constructs. The amber-highlight scheme for cross-direction divergent items (added May 3) "
    "is a particularly useful semantic marker."
)
bullet(
    "Methodological transparency: measurement-invariance testing was added even though it "
    "produces an inconvenient result (most composites fail strict scalar invariance). The "
    "willingness to publish that result rather than suppress it is a strong methodological "
    "choice."
)


# ===========================================================================
# Prioritized action checklist
# ===========================================================================
doc.add_paragraph()
H2("Consolidated Action Checklist (priority order)", color=RGBColor(0x1f, 0x29, 0x37))

H3("Pre-submission HIGH-priority items")
bullet(
    "1. Run the Russian sample-composition robustness check (Round 2 FLAG 1, now eight days "
    "open). Cross-tab age / education / region for the 2020 vs. 2023 Russian subsamples; if "
    "shifted, re-estimate within-Russian d's with covariate adjustment. Decisively closes or "
    "qualifies the 'Russian liberalization' headline."
)
bullet(
    "2. Add scalar-invariance caveats to BiC and Minority Support figure captions, and to the "
    "discussion-chapter prose where their within-group d's are cited."
)
bullet(
    "3. Add the Round 3 scripts (39–58) to build_all.py as Stage 8. Without this, the Round 3 "
    "outputs are not part of the reproducible CI gate."
)
bullet(
    "4. Add 4–6 entries to the CLAUDE.md decisions table covering the Round 3 wave (May 1–3). "
    "At minimum: §51 paired test, sign-reversal finding, the cross-direction divergence "
    "findings on Q68_3 and Q63_2, focused between-group chart, name change to 'Minority "
    "Inclusion Support' on charts."
)
bullet(
    "5. Promote the §51 sign-reversal and the two cross-direction divergence items (Q68_3, "
    "Q63_2) to stand-alone discussion-chapter results, ideally with their own subsection or "
    "table. They are the project's sharpest substantive findings and currently sit as "
    "appendix-grade outputs."
)

H3("MEDIUM-priority items")
bullet(
    "6. Reconcile the headline sample N in CLAUDE.md with per-composite max in the canonical "
    "TSV (706 vs. 702, 870 vs. 865, etc.). Either correct or document the difference."
)
bullet(
    "7. Address the Ukrainian-item exclusion explicitly in the General-out-group narrative — "
    "either plot the dropped items separately or add a scoping paragraph."
)
bullet(
    "8. Standardize the theoretical-claim language. Pick one phrasing (e.g., 'asymmetric "
    "attitude divergence under external shock') and use it consistently across thesis chapter, "
    "CLAUDE.md, and reports."
)
bullet(
    "9. Update SESSION_LOG §29 to reflect the Round 3 falsification weakening (or add a "
    "marginal note pointing to Blindspot Round 3 Flag 7)."
)
bullet(
    "10. Add a one-paragraph contact-theory anchor (Russians' contact UP + BiC DOWN matches "
    "Allport's contact hypothesis) to the discussion."
)
bullet(
    "11. Add the SD: Primary public-vs-intimate gradient to the discussion as a sub-finding "
    "(Estonian Marriage d = +0.22 vs. Neighbors / Work +0.41 / +0.44)."
)
bullet(
    "12. Document the 'Minority Inclusion Support' vs. 'Minority Support Inclusion' name "
    "split in CLAUDE.md, OR rename the canonical variable and re-run the referee2 audit."
)

H3("LOW-priority housekeeping")
bullet(
    "13. Delete or move-aside the orphaned in-group SD outputs (viz/fig_sd_ingroup_*.jpg and "
    "scripts 45–47)."
)
bullet(
    "14. Add 'DEPRECATED' header comments to code/regression/*.py, or delete the directory."
)
bullet(
    "15. Clean up stray 'copy' files and Word lock files in reports/."
)


# ===========================================================================
# Save
# ===========================================================================
doc.save(out_path)
print(f"Saved: {out_path}")
