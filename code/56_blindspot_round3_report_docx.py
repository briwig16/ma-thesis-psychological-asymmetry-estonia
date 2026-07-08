"""
Blindspot Report (Round 3) — Word Doc Generator
================================================
Renders the 2026-05-02 Blindspot perceptual audit of post-Round-2 outputs:

  - §33 Measurement invariance results (R lavaan, 84 fit-index rows)
  - The 2026-05-01 / 2026-05-02 distribution-shape and item-decomposition
    charts for Minority Support, SD: Primary Out-group, SD: General Out-group
  - The §51 paired test of Estonian Primary vs. General SD (sign reversal)
  - The Primary-vs-General comparison figures (52-55)

Output: reports/Blindspot_Report_2026-05-02.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor

ROOT = Path(__file__).parent.parent
out_path = ROOT / "reports" / "Blindspot_Report_2026-05-02.docx"

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

def H2(text):
    H(text, size=12)

def H3(text):
    H(text, size=11)

def body(text, italic=False, size=10):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size)
    if italic: r.italic = True

def bullet(text, size=10):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text); r.font.size = Pt(size)

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


# ---------- Title block ----------------------------------------------------
H("Blindspot Report — Post-Round-2 Outputs", size=16,
  color=RGBColor(0x1f, 0x29, 0x37))

p = doc.add_paragraph()
r = p.add_run("Outputs audited: ")
r.bold = True; r.font.size = Pt(10)
r = p.add_run(
    "(1) §33 measurement-invariance pipeline (code/36/37/38, _invariance_results.tsv); "
    "(2) the 2026-05-01 / 2026-05-02 composite-density, item-decomposition, and item-density "
    "figures for Minority Support, SD: Primary Out-group, and SD: General Out-group "
    "(scripts 39–50); (3) the §51 paired Estonian Primary-vs-General test "
    "(code/51, viz/fig_sd_primary_vs_general_*.jpg); "
    "(4) the group-organized comparison figures (scripts 54-55)."
); r.font.size = Pt(10)

p = doc.add_paragraph()
r = p.add_run("Stated narrative arc since Round 2: ")
r.bold = True; r.font.size = Pt(10)
r = p.add_run(
    "(A) Estonian community is fragmenting on multiple intergroup dimensions while Russian community "
    "is broadly liberalizing; (B) Estonians' attitudinal shift is selectively targeted at Russian-speakers, "
    "not at out-groups in general — supported by the §51 sign-reversal of Estonian Primary vs. General SD."
); r.font.size = Pt(10)

p = doc.add_paragraph()
r = p.add_run("Date: "); r.bold = True; r.font.size = Pt(10)
r = p.add_run("2026-05-02"); r.font.size = Pt(10)

doc.add_paragraph()
body(
    "The Blindspot protocol is a structured perceptual audit that asks whether the author can still "
    "see what is in front of them — features in the output that have become invisible due to "
    "familiarity. It complements but does not replace the Referee 2 audit (Round 3, 2026-04-29) "
    "which checked whether the code is correct. This Round 3 Blindspot focuses on outputs produced "
    "between 2026-04-30 and 2026-05-02 — measurement invariance plus the new wave of distribution-shape "
    "visualizations and the Estonian Primary-vs-General sign-reversal claim.",
    italic=True
)


# ---------- Verdict --------------------------------------------------------
H2("Overall Verdict")
body(
    "CONDITIONAL — three substantive findings stand on solid measurement footing, two depend on "
    "a measurement caveat that has been documented but not yet propagated into the figure narratives, "
    "and one item-level pattern is being underplayed in the current write-up. No data-coding errors, "
    "no falsified claims. The single most important action item is to flag SD: General's item-set "
    "change explicitly wherever the within-General d's are cited, because the 'Russian liberalization' "
    "story leans heavily on a within-General d that is partially confounded with construct change."
)


# ---------- Flag 1: Sign-reversal claim is well-founded but framed too strongly ----
H2("FLAG 1 — Sign-reversal claim: solid on the Primary side, leakier on the General side")

body(
    "The §51 paired test established a striking sign-reversal in Estonian respondents: in 2020 "
    "Estonians rated Russian-speakers as LESS socially distant than 'new immigrants' (M_Pri = 2.51 < "
    "M_Gen = 2.91, d_z = −0.47, ***); in 2023 the rank order flipped (M_Pri = 2.92 > M_Gen = 2.70, "
    "d_z = +0.24, ***). The within-year paired tests are clean, and the §54 visualization makes the "
    "reversal immediately visible. This is a strong finding."
)

body(
    "The vulnerability is in how the reversal is being attributed. The current narrative treats both "
    "halves of the swing as substantive: Estonians became MORE distant from Russian-speakers AND "
    "MORE accepting of generic out-groups. The first half is well-supported — within-Estonian "
    "SD: Primary d = +0.42 *** is built on items that hold scalar measurement invariance "
    "longitudinally (per §33: Δχ²(2) = 4.5, ΔCFI = −0.002, ΔRMSEA = +0.0075 — well within Cheung & "
    "Rensvold thresholds). The second half — within-Estonian SD: General d = −0.23 — compares a "
    "3-item 'new immigrants' battery in 2020 against a 6-item 'other Europeans + non-Europeans' "
    "battery in 2023. CLAUDE.md flags this as 'cross-year measures different construct.' This caveat "
    "is missing from the §51 / §54 / §55 writeups."
)

body(
    "Recommended reframing: present the falsification claim as one-sided. 'Estonians selectively "
    "hardened toward Russian-speakers' is well-supported. 'Estonians simultaneously liberalized "
    "toward generic out-groups' rests on a non-comparable construct and should be qualified or "
    "demoted to a methods-chapter footnote. The cleanest version of the sign-reversal claim is: "
    "'In 2020, the rank order Primary < General held (Estonians regarded Russian-speakers as more "
    "socially proximate than abstract immigrants). In 2023, the Primary distribution had moved past "
    "the General distribution. The Primary-side movement is the substantive driver; the General-side "
    "movement may reflect both attitudinal shift and construct re-specification.'"
)


# ---------- Flag 2: Measurement invariance caveats not propagated ----------
H2("FLAG 2 — Measurement-invariance caveats are documented but not propagated to figure narratives")

body(
    "§33 measurement-invariance testing established that scalar invariance HOLDS for SD: Primary "
    "Out-group longitudinally (both groups), but FAILS for Belief in Inevitable Conflict, Minority "
    "Support Inclusion, and most other composites under longitudinal and multi-group comparison "
    "(8 HOLDS, 2 PARTIAL, 18 FAILS across 28 comparisons). The substantive implication — that some "
    "portion of the observed group-level d's may reflect intercept variation rather than purely "
    "attitudinal differences — was filed in the methods documentation. It has not made its way "
    "into how the recent figures are being interpreted."
)

body("Specific cases where this matters:")

H3("(a) BiC within-Russian d = −0.32 *** ('Russians decreased belief in inevitable conflict')")
body(
    "Longitudinal scalar invariance FAILS for Russians (Δχ²(3) = 28.7, p < .001, ΔCFI = −0.046). "
    "The 'Russians decreased conflict belief' claim — central to dissolving the §29 paradox — is "
    "robust to direction (the recoding was independently verified) but not strictly comparable as a "
    "latent-mean difference. Worth noting in the chapter."
)

H3("(b) Minority Support Inclusion within-Estonian d = −0.15 ** and within-Russian d = +0.04 (ns)")
body(
    "Longitudinal scalar invariance FAILS for both groups. The 'Russians stayed flat / Estonians "
    "modestly declined' framing rests on score differences whose measurement-intercept comparability "
    "is not established. The item-level decomposition partially compensates (it shows specific items "
    "drove the Estonian decline), but composite-level interpretation should be qualified."
)

H3("(c) SD: Primary Out-group within-Estonian d = +0.42 ***  ←  exception worth highlighting")
body(
    "Longitudinal scalar invariance HOLDS for both groups. This is the rare composite where a strong "
    "claim about latent attitude change can be made with confidence. The fact that the headline "
    "Round-3 finding (Estonians selectively hardened toward Russian-speakers) sits on the most "
    "measurement-robust composite in the project is a lucky alignment that should be cited as "
    "supporting evidence rather than left implicit."
)


# ---------- Flag 3: Russian sample composition shift still unaddressed ----
H2("FLAG 3 — Russian sample composition shift (609 → ~520) still unresolved")

body(
    "Round 2 (§29 FLAG 1) raised that the Russian respondent N dropped from 609 (2020) to ~520 (2023, "
    "varies slightly by composite due to DK patterns), and that this shift was undocumented. Eight days "
    "later, no robustness check has been performed. The 'Russians broadly liberalized' narrative — built "
    "on within-Russian d's of −0.32 (BiC), −0.56 (SD General), +0.04 (Minority Support stable), and "
    "−0.07 (SD Primary stable) — is potentially compositional rather than attitudinal: if more "
    "conservative Russian respondents selectively dropped out between waves, every within-Russian "
    "estimate is biased in the liberalizing direction."
)

body(
    "The Round 2 Russian-edu-pathway robustness check (§31) addressed within-2023 sub-group consistency, "
    "but does not test whether 2020 and 2023 Russian respondents are demographically comparable. The "
    "minimum useful check is: (i) cross-tab age, education, and region for the Russian sub-sample in "
    "2020 vs. 2023; (ii) if a noticeable shift exists, re-estimate the within-Russian d's with "
    "post-stratification weights or a covariate-adjustment regression. This has been pending since "
    "April 29 and should be closed before any of the within-Russian narratives are committed to the "
    "thesis chapter."
)


# ---------- Flag 4: Ukrainian elephant in the room ------------------------
H2("FLAG 4 — The Ukrainian dimension is structurally absent from the General out-group story")

body(
    "The 2020 → 2023 General Out-group shift — within-Russian d = −0.56 ***, within-Estonian d = "
    "−0.23 *** — is being reported as 'both groups became more accepting of general out-groups.' "
    "Two structural facts complicate this narrative:"
)
bullet(
    "The 2020 'new immigrants in last 5 years' item was administered in a period when Estonia had "
    "very few new immigrants. It measured an abstract category."
)
bullet(
    "The 2023 General battery measures 'other Europeans + non-Europeans' — and explicitly EXCLUDES "
    "the Ukrainian items per the 2026-03-23 decision (Russians held asymmetrically negative views of "
    "Ukrainian refugees, which masked otherwise positive general-out-group attitudes)."
)
body(
    "The exclusion was methodologically defensible. But it means the 'Russians liberalized toward "
    "general out-groups' claim is partial: Russians liberalized toward generic Europeans and non-"
    "Europeans, while remaining notably more negative than Estonians toward the most salient post-"
    "2022 immigrant population. A reader unfamiliar with the methods will mis-read the General SD "
    "decline as a generalized softening of attitudes — which the underlying data do not support. "
    "The Ukrainian item-level distributions are sitting in the data and could be plotted "
    "separately to make this asymmetry visible without contaminating the composite."
)


# ---------- Flag 5: Russian Minority Support item 3 — unexplored asymmetry ----
H2("FLAG 5 — Item 3 'Understand opinions' shows an asymmetric within-group divergence that has not been pursued")

body(
    "From the Minority Support item-level decomposition (script 40, May 1):"
)
make_table(
    ["Item", "Within Estonian d", "Within Russian d", "Note"],
    [
        ["Q68_1 'Involve in economy'",      "−0.01 ns", "+0.05 ns", "stable both sides"],
        ["Q68_2 'Involve in governance'",   "−0.18 ***", "−0.08 ns", "Estonians declined modestly"],
        ["Q68_3 'Understand opinions'",     "−0.16 **",  "+0.23 ***", "DIVERGENT — only opposite-sign item"],
    ]
)
body(
    "Item 3 is the only Minority Support item where Estonian and Russian respondents moved in OPPOSITE "
    "directions, both significantly. The substantive interpretation is striking: 'understanding the "
    "opinions of other nationalities' grew more important to Russians while becoming less of a priority "
    "to Estonians. From each group's own perspective, this means Russians became more open to "
    "understanding Estonian-language society while Estonians became less open to understanding "
    "Russian-language society. This is exactly the asymmetric divergence pattern that the headline "
    "Estonian-vs-Russian narrative would predict — and yet it sits in a single item-level row of an "
    "appendix figure, not in the main results discussion."
)
body(
    "Recommended action: promote Q68_3 to a stand-alone result. The item is conceptually closer to "
    "'cultural curiosity' / 'cross-language receptiveness' than the other two governance/economy items, "
    "and the divergence is qualitatively different from the broader fragmentation pattern. Worth a "
    "paragraph in the discussion."
)


# ---------- Flag 6: SD Primary item-level — Marriage moves least ----
H2("FLAG 6 — Within-Estonian SD: Primary movement is concentrated in PUBLIC contexts, not the most intimate one")

body(
    "From the SD: Primary item-level decomposition (script 43, May 1):"
)
make_table(
    ["Item", "Within Estonian d", "Within Russian d"],
    [
        ["Neighbors",          "+0.41 ***", "−0.04 ns"],
        ["Work / study",       "+0.44 ***", "−0.01 ns"],
        ["Marriage in family", "+0.22 ***", "−0.11 (p=.08)"],
    ]
)
body(
    "Estonians' increased social distance from Russian-speakers is half as large at the most intimate "
    "social-distance item (marriage in family) as at the public-civic items (neighbors, work/study). "
    "This asymmetry is consistent with two interpretations: (i) the shift is largely a public-life "
    "phenomenon — civic and workplace boundary-setting — that is less reflected in personal/family "
    "decisions; (ii) the marriage item is at floor for many Estonian respondents in both years (modal "
    "category 1 = would not accept), so there is less room for a distance increase to manifest."
)
body(
    "Both interpretations matter. (i) is theoretically interesting and worth pursuing as a sub-finding. "
    "(ii) is a measurement-floor caveat that could be checked against the item distribution. The current "
    "writeup presents the Estonian Primary-d as a single composite movement; surfacing the item-level "
    "gradient would sharpen the substantive interpretation."
)


# ---------- Flag 7: Falsification claim slightly overreaches --------------
H2("FLAG 7 — The 'Estonian shift is not generalized' falsification logic is weaker than presented")

body(
    "The §29 reframing — and the §51 paired test that operationalized it — argues that the divergence "
    "between within-Estonian SD: Primary (+0.42 ***) and SD: General (−0.23 ***) constitutes a "
    "falsification test for the war-shock hypothesis: if Estonians had simply hardened against all "
    "out-groups, both within-d's should be positive. The fact that they go in opposite directions, "
    "the argument runs, shows that the hardening is selectively targeted."
)
body(
    "The argument has two soft links:"
)
bullet(
    "The General d also goes in opposite directions for Russians (−0.56) and Estonians (−0.23). "
    "If the General item-set change drove most of the General d for both groups (a strict "
    "construct-change interpretation), then the Estonian Primary increase remains the only "
    "substantive change being reported — the falsification test is reduced to 'Estonians moved on "
    "Primary, period.' That is a weaker claim than 'Estonians moved on Primary while not moving "
    "(or moving the other way) on General.'"
)
bullet(
    "Even if the General-side d's are accepted as substantive, a 'liberalized toward generic Europeans + "
    "non-Europeans' shift while 'hardening toward the specific historically-salient out-group' is "
    "compatible with a war-shock-driven schema split (Russian-speakers tagged as threat, generic "
    "Europeans tagged as solidarity). It is not strictly disconfirming for war-shock, only for "
    "naïve generalized-hardening."
)
body(
    "Recommended action: weaken the falsification claim from 'falsifies generalized hardening' to "
    "'rules out non-targeted hardening,' which is what the design actually supports."
)


# ---------- Confirmations -------------------------------------------------
H2("Confirmations — what the new outputs do well")

bullet(
    "The §51 paired test was the missing piece behind the Round 2 §29 falsification framing. Adding "
    "a within-respondent test transforms the Round 2 'two within-group d's go opposite directions' "
    "into 'the rank order between the two out-group categories actually flipped within Estonians.' "
    "The Estonian sign-reversal is the single sharpest finding the project now has, and it now has "
    "a proper test behind it."
)
bullet(
    "The script-50 4×3 SD General item-density figure handles the awkward 2020/2023 item-set asymmetry "
    "cleanly — the 'one 2020 immigrant target splits into two 2023 sub-targets' framing is the most "
    "honest way to display a non-comparable battery, and the figure makes the asymmetry legible "
    "rather than hiding it."
)
bullet(
    "Distribution-shape figures (composite density + item-density across Minority, SD Primary, SD "
    "General) consistently surface the variance / dispersion patterns alongside the means. The "
    "Estonian dispersion-grows pattern that emerged in Round 2 (Superordinate Identity, Group ID, "
    "BiC) now also shows up in Minority Support (Levene's p = .001) and SD Primary composite (p = "
    ".001) and SD Primary Work / study item (p = .003). Five different dimensions of intergroup "
    "attitudes show the same fragmentation signature on the Estonian side. That's a strong "
    "convergent pattern."
)
bullet(
    "The exploratory in-group SD investigation (scripts 45-47) was correctly diagnosed as "
    "structurally non-interpretable (N = 21–51 per cell, almost certainly a survey-routing artifact) "
    "and dropped without further pursuit. Good ergonomics."
)


# ---------- Action checklist ----------------------------------------------
H2("Action Checklist (in priority order)")

bullet(
    "1. Reframe §51 / §54 / §55 narrative: emphasize within-Estonian Primary increase as the "
    "substantive driver; qualify the within-General decrease with the construct-change caveat."
)
bullet(
    "2. Cite the §33 longitudinal scalar-invariance HOLDS for SD: Primary as supporting evidence "
    "for the headline finding (turn the methodology lucky-alignment into a cited strength)."
)
bullet(
    "3. Add the §33 scalar-invariance FAILS caveat to the methods chapter for BiC and Minority "
    "Support within-group findings."
)
bullet(
    "4. Run the long-pending 2020 vs. 2023 Russian sample composition robustness check (Round 2 "
    "FLAG 1, still open)."
)
bullet(
    "5. Surface Q68_3 'Understand opinions' divergence (Estonians −0.16 **, Russians +0.23 ***) as "
    "a stand-alone discussion result — it is a different kind of asymmetry from the rest."
)
bullet(
    "6. Explicitly address the Ukrainian-item exclusion in the General-out-group narrative: either "
    "plot the dropped Ukrainian items separately, or add a paragraph clarifying that 'Russian "
    "liberalization toward general out-groups' excludes the most policy-salient post-2022 group."
)
bullet(
    "7. Weaken the falsification claim from 'falsifies generalized hardening' to 'rules out non-"
    "targeted hardening' — preserve the substance, sharpen the epistemic standing."
)
bullet(
    "8. (Smaller) Note the SD: Primary public-vs-intimate item gradient (Estonian Marriage d = +0.22 "
    "vs. Neighbors / Work +0.41 / +0.44) — interesting sub-finding worth one or two sentences."
)


# ---------- Save ----------------------------------------------------------
doc.save(out_path)
print(f"Saved: {out_path}")
