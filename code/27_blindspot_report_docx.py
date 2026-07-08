"""
Blindspot Report (Round 2) — Word Doc Generator
================================================
Renders the 2026-04-29 Blindspot perceptual audit of the Round-3 effect-size
pipeline as a formatted Word document for the thesis appendix and the
correspondence/blindspot/ archive.

Output: reports/Blindspot_Report_2026-04-29.docx
"""

from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).parent.parent
out_path = ROOT / "reports" / "Blindspot_Report_2026-04-29.docx"

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
    return p

def H2(text):
    return H(text, size=12)

def H3(text):
    return H(text, size=11)

def body(text, italic=False, size=10):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.size = Pt(size)
    if italic: r.italic = True
    return p

def bullet(text, size=10):
    p = doc.add_paragraph(style="List Bullet")
    r = p.add_run(text); r.font.size = Pt(size)
    return p

def make_table(header, rows, col_widths=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(header):
        cell = t.rows[0].cells[i]
        cell.text = ""
        pp = cell.paragraphs[0]
        rr = pp.add_run(h); rr.bold = True; rr.font.size = Pt(9)
    for r_ in rows:
        cells = t.add_row().cells
        for i, txt in enumerate(r_):
            cells[i].text = ""
            pp = cells[i].paragraphs[0]
            rr = pp.add_run(txt); rr.font.size = Pt(8.5)
    return t


# ---------- Title block ----------------------------------------------------
H("Blindspot Report — Round-3 Effect-Size Pipeline", size=16,
  color=RGBColor(0x1f, 0x29, 0x37))

p = doc.add_paragraph()
r = p.add_run("Output audited: ")
r.bold = True; r.font.size = Pt(10)
r = p.add_run(
    "code/_effect_sizes.tsv, reports/Effect_Sizes_with_CI.docx, and the five JPEG figures "
    "(fig_within_group_change, fig_between_group_gap, fig_between_group_dumbbell, "
    "fig_between_group_dumbbell_d, fig_contact_breakdown)."
); r.font.size = Pt(10)

p = doc.add_paragraph()
r = p.add_run("Stated main finding: ")
r.bold = True; r.font.size = Pt(10)
r = p.add_run(
    "Psychological asymmetry between Estonian-majority and Russian-minority respondents, "
    "with patterns shifting between 2020 and 2023."
); r.font.size = Pt(10)

p = doc.add_paragraph()
r = p.add_run("Date: "); r.bold = True; r.font.size = Pt(10)
r = p.add_run("2026-04-29"); r.font.size = Pt(10)

doc.add_paragraph()
body(
    "The Blindspot protocol (mds/blindspot.md) is a structured perceptual audit that asks whether the "
    "author can still see what is in front of them — features in the output that have become invisible "
    "due to familiarity. It complements but does not replace the Referee 2 audit (Round 3, 2026-04-29) "
    "which checked whether the code is correct. Both have been run on this analysis.",
    italic=True
)

doc.add_paragraph()


# ---------- Vice 1: Unexplained Feature -----------------------------------
H2("Vice 1 — The Unexplained Feature")
body("Features in the output that don't fit the preferred narrative or were never addressed. "
     "14 features were inspected. Each is marked DONE (explained) or FLAG (open question).",
     italic=True)

vice1_rows = [
    ("1", "Superordinate Identity 2023 between-group gap narrowed (1.08 → 0.79) without either group's mean changing meaningfully", "FLAG"),
    ("2", "Russian SDs increased on Superordinate Identity (0.66 → 0.79) and Group ID (0.81 → 0.84) — the Russian community's responses became more dispersed", "FLAG"),
    ("3", "Russians SIMULTANEOUSLY increased contact with Estonians (d=+0.51) AND increased belief in inevitable conflict (d=+0.32) — direction-of-effect contradicts contact theory", "FLAG"),
    ("4", "Estonian SD: Primary Out-group jumped d=+0.42 — the only composite where Estonians moved AWAY from Russian-speakers — while simultaneously becoming more accepting of OTHER out-groups", "FLAG"),
    ("5", "Comparative Opportunity moved in the SAME direction for both groups (both d≈−0.30) — partial CONVERGENCE in perceived structural fairness, undersold", "DONE"),
    ("6", "SD: General 2023 between p = .049, CI [−0.001, +0.218] — significance hangs on the third decimal", "DONE"),
    ("7", "Contact: Out-group 2020 between p=.054 ns, 2023 between p<.0001 *** — appearance of significance driven by Russian movement, not Estonian", "DONE"),
    ("8", "Russian within-group shift on Q51_1 (work/school contact) is −1.07 on a 1-5 scale — far larger than any other item-level shift in the dataset", "FLAG"),
    ("9", "Estonian Territorial Attachment mean is 3.76/3.77 on a 1-4 scale — at ceiling. Within-group stability partly an artifact", "FLAG"),
    ("10", "Group ID Patterns 2023 between gap halved — Russians moved to dual identity (2.69 → 2.81); Estonians flat", "DONE"),
    ("11", "Belief in Inevitable Conflict 2020 SDs equal across groups (0.57 each); 2023 SDs diverge (Est 0.67, Rus 0.58) — Estonians' beliefs DISPERSED", "FLAG"),
    ("12", "Contact: Russian Speakers between-group gap is 2.25 SD — largest effect in the entire study, stable across both years", "DONE"),
    ("13", "2023 sample's ETHNIC COMPOSITION shifted: Russian share 46% (609/1315) → 38% (522/1392)", "FLAG"),
    ("14", "Russian DK rate on Q66 / K6X4 (Group ID) edged from 3.0% → 4.6% — small but present", "DONE"),
]
make_table(["#", "Feature", "Status"], vice1_rows)

doc.add_paragraph()
H3("Hardest feature to explain under the preferred narrative")
body(
    "Russians simultaneously increasing cross-group contact AND increasing belief in inevitable conflict "
    "(item #3 above). Standard intergroup contact theory (Allport 1954, Pettigrew & Tropp 2006) predicts "
    "contact should reduce conflict perception — not increase it. Russian Q51_1 (contact with Estonian-"
    "speakers at work/school) jumped from 3.02 → 1.96 on a 1-5 scale (≈1 SD shift), AND Russian Belief in "
    "Inevitable Conflict rose from 3.03 → 3.21 (d=+0.32 ***)."
)
body(
    "The most plausible reconciliation is that the contact is institutional/coercive rather than voluntary. "
    "Estonia announced its language reform — making Estonian the primary language of instruction — in 2022, "
    "with phase-in starting 2024. This forces contact in work/school contexts. Forced contact under perceived "
    "threat does NOT reduce prejudice; in some specifications it amplifies it (Pettigrew 2008 on conditional "
    "contact effects). The war in Ukraine (Feb 2022) is a plausible third variable driving both."
)
body("Resolved? FLAG — needs explicit treatment in the interpretation chapter.", italic=True)

doc.add_paragraph()


# ---------- Vice 2: Convenient Absence ------------------------------------
H2("Vice 2 — The Convenient Absence")
body("What's missing that should be there. The dog that didn't bark.", italic=True)

H3("Missing checks")
bullet("No subgroup analysis. ethnicity_binary, parents_birthplace, edu_language are derived in scripts 01–03 but the comparison tables collapse everything to ethnic group. Russian-school graduates probably look very different from Estonian-school graduates — published-paper-grade moderator left untouched.")
bullet("No geographic split. Russian-speakers in Estonia are concentrated in Ida-Virumaa. Effects could be driven by that region or attenuated by it. T4/T5 (settlement type / county) are in the codebook.")
bullet("No age × wave interaction. Younger Russians may be moving toward integration; older Russians may not. Headline d collapses both.")
bullet("No analysis of the Ukrainian-refugee items (Q57_3, Q58_3, Q59_3). Excluded from SD: General with good reason — but the asymmetric Russian negativity toward Ukrainian refugees is itself a substantive finding currently buried.")
bullet("No measurement invariance testing across waves or groups. PCA + α validate composites separately by group, but invariance across time/group has not been tested. Without it, d values across groups/waves may not be psychometrically comparable.")
bullet("No pre-trend. Two waves means no test of whether 2020→2023 changes are continuation or discontinuity. Acknowledge as a limitation.")
bullet("No distributional plots. Means hide the polarization signal flagged in Vice 1 #2 and #11.")

H3("Unexplained N changes")
bullet("Russian sample DROPPED from 609 → 522 (−14%) while total survey size grew slightly. Estonian share grew from 706 → 870 (+23%). 2023 sample is structurally less Russian. Whatever the cause (out-migration after Feb 2022, survey targeting, differential response), this is currently undocumented and matters because if 2023 Russians are a self-selected subset, within-group comparisons confound true attitude change with sample composition change.")

doc.add_paragraph()


# ---------- Virtue 1: Unasked Question ------------------------------------
H2("Virtue 1 — The Unasked Question")
body("A pattern in the output that suggests something more interesting than the headline finding.", italic=True)

H3("Heterogeneity opportunities")
bullet("The Russian community is plausibly fragmenting along the war. Increasing within-Russian SDs on identity measures (Vice 1 items #2 and #11) is the signature of polarization. If a density plot reveals bimodality, the headline 'Russians are integrating' splits into 'some Russians are integrating, others are pulling away.'")

H3("Mechanism evidence")
bullet("The contact breakdown chart already pointed at the mechanism, but the thesis hasn't claimed it. Russian Q51_1 shift of −1.07 (work/school contact) is roughly 4× the next largest within-group item shift. The signal is screaming 'institutional contact via the Estonian-language education reform announced in 2022.' The thesis can frame this as a natural-experiment finding about the boundary conditions of intergroup contact theory.")

H3("Secondary findings")
bullet("Estonian selective rejection. Estonians became more open to general out-groups (d=−0.23) and more closed specifically to Russian-speakers (d=+0.42). This is not 'Estonians becoming nationalist' — it's 'Estonians becoming MORE selective in their out-group acceptance, with Russian-speakers as the specifically rejected category.'")
bullet("Convergence on perceived structural fairness. Both groups perceive LESS Estonian advantage in 2023 than in 2020 — same direction, similar magnitude (d ≈ −0.30 each). Convergence not currently in the headline.")

H3("Is there a paper inside this paper?")
bullet("Yes — the institutional-contact paper. 'Forced linguistic contact under conditions of geopolitical threat: Russian-Estonian relations 2020-2023.' A specific theoretical contribution to contact theory's boundary conditions, broader than a thesis chapter, plausibly publishable.")

doc.add_paragraph()


# ---------- Virtue 2: Unexploited Strength --------------------------------
H2("Virtue 2 — The Unexploited Strength")
body("Something about the design, data, or results that the author is underselling.", italic=True)

H3("Undersold design features")
bullet("The 2020-2023 wave structure spans Feb 24, 2022. The war is exogenous to Estonian intergroup attitudes. This is essentially a natural before/after of an unprecedented external shock. The thesis currently presents this as cross-sectional comparison; it could be reframed as quasi-experimental.")
bullet("The Round-3 audit-grade replication infrastructure: 444/444 Python checks, 440/440 R cross-language checks, full audit report. Rare in master's theses, sometimes absent from published papers. Worth a methods-chapter paragraph.")
bullet("The pairwise-deletion methodology is documented and audited. Reviewers who object to pairwise can be answered with the audit; this is a strength not currently highlighted.")

H3("Unused falsification tests")
bullet("A placebo across non-Russian-speaker out-groups: if the Estonian SD: Primary shift is real war-driven anti-Russian-speaker hostility, then SD toward NON-Russian out-groups should NOT show the same shift. The data already say this — Estonian SD: General WENT THE OTHER WAY (d=−0.23, MORE accepting). This IS the falsification test, and it passes — but is currently buried. Calling this out turns 'Estonians moved' into 'Estonians selectively moved AGAINST Russian-speakers specifically, not against out-groups in general — exactly what a war-shock interpretation predicts.'")

H3("Positioning opportunities")
bullet("Possible reframe: from 'psychological asymmetry' to 'cross-group attitude divergence under forced contact: how Russia's invasion of Ukraine and Estonia's institutional response reshaped intergroup relations.'")

doc.add_paragraph()


# ---------- Ruling -------------------------------------------------------
H2("Ruling")

p = doc.add_paragraph()
r = p.add_run("CONDITIONAL — proceed but acknowledge open questions explicitly. ")
r.bold = True; r.font.size = Pt(11)
r = p.add_run(
    "No fatal vices, but two FLAGs are substantive enough that the interpretation chapter "
    "should address them explicitly."
); r.font.size = Pt(10)

doc.add_paragraph()
H3("FLAGs requiring explicit interpretation")
flag_rows = [
    ("Russian sample composition shift (609 → 522, −14%)",
     "Document explicitly. Run robustness check (region weights, age weights), or at minimum acknowledge."),
    ("Contact ↑ + Conflict-belief ↑ paradox",
     "Frame as institutional/coercive contact via the 2022 language reform. Cite Pettigrew's conditional-contact-effects literature."),
    ("Within-Russian SD increases (polarization signal)",
     "Add density plots. If bimodality is visible, the 'Russians integrating' framing must be split."),
]
make_table(["Flag", "Recommended action"], flag_rows)

doc.add_paragraph()
H3("Recommended additions (low-cost, high-yield)")
bullet("Density plot for Russian Superordinate Identity 2020 vs 2023 — addresses polarization question directly.")
bullet("Subgroup analysis by edu_language for Russian respondents — separates Russian-school graduates from those with Estonian-school exposure.")
bullet("Acknowledge the Russian sample-size drop in the methods chapter; present at least one robustness statement.")

H3("Reframings worth considering")
bullet("From 'psychological asymmetry' → 'asymmetric attitude divergence under external shock'.")
bullet("Estonian SD: Primary vs SD: General contrast IS the falsification test for a war-driven mechanism — promote it from a row in a table to a key finding.")
bullet("Both groups converging on Comparative Opportunity is an underplayed parallel result — worth a sentence.")

doc.add_paragraph()

p = doc.add_paragraph()
r = p.add_run("— Blindspot, 2026-04-29")
r.font.size = Pt(9); r.italic = True

doc.save(out_path)
print(f"Saved: {out_path}")
