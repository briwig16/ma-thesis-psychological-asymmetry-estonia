"""Insert Section 5.4 (Blindspot Perception Audit) into AI_Assisted_Analysis_Methodology.docx
before Section 6 (Decision Traceability)."""

from docx import Document
from copy import deepcopy

DOC_PATH = "../reports/AI_Assisted_Analysis_Methodology.docx"

doc = Document(DOC_PATH)

# Build the new section as a list of (text, style_hint) tuples.
# style_hint: "h2" for subheading, "h3" for sub-subheading, "body" for body text.
new_section = [
    ("5.4 Blindspot Perception Audit", "h2"),
    ("A fourth layer of quality assurance was applied at the interpretation stage using the Blindspot skill — a structured perceptual audit designed to find what the researcher can no longer see due to familiarity with their own output.", "body"),
    ("What is the Blindspot Skill?", "h3"),
    ("The Blindspot skill is documented in the project at mds/blindspot.md. It was developed from a principle articulated by Viktor Shklovsky in \u201cArt as Device\u201d (1917): that familiarity makes perception automatic and unconscious, and that a deliberate defamiliarization is needed to restore the ability to see what is right in front of you. Applied to empirical research, the problem is that by the time a researcher has spent months with a dataset, the main finding has collapsed their attention — unexplained features, missing analyses, richer patterns, and undersold strengths become invisible not because they are hidden, but because the researcher has stopped looking.", "body"),
    ("The Blindspot skill is explicitly distinguished from the Referee 2 audit protocol. Referee 2 asks whether the code is correct (a health inspector with a checklist). Blindspot asks whether the author can see what is in front of them (Shklovsky restoring perception). Referee 2 would catch a merge error; Blindspot would catch a spike in the output that nobody asked about. Both were used in this project; neither replaces the other.", "body"),
    ("The Blindspot Grid", "h3"),
    ("The audit is organized into four quadrants:", "body"),
    ("Vice 1 — The Unexplained Feature: something in the output that does not fit the story but that no one has asked about. Every visible feature is listed before any are interpreted; each is then interrogated for what could generate it, including explanations that have nothing to do with the hypothesis.", "body"),
    ("Vice 2 — The Convenient Absence: something that should be in the output but is not. Missing robustness checks, unexamined subgroups, analyses that were dropped without comment, unexplained sample size changes across specifications.", "body"),
    ("Virtue 1 — The Unasked Question: a pattern in the output suggesting something more interesting than what is being reported. Heterogeneity richer than the average, mechanism evidence hiding in the descriptives, a secondary finding that may be more important than the primary one.", "body"),
    ("Virtue 2 — The Unexploited Strength: something about the design, data, or results that the researcher is underselling. Falsification tests that were never run, identification arguments stronger than the paper claims, descriptive statistics that make the case more powerfully than reported.", "body"),
    ("How Blindspot Was Used in This Project", "h3"),
    ("The Blindspot audit was conducted on April 20, 2026, after all eight composite variables and two single-item variables had been constructed, validated, and compared across groups and years — at the point when interpretation and writing were about to begin. The audit reviewed all composite comparison tables (between-group and within-group, 2020 and 2023), the full psychometric summary, and the session log.", "body"),
    ("Key findings from the audit:", "body"),
    ("Vice 1 identified four unexplained features, including the contact-distance paradox (Estonians reporting more contact with Russian-speakers while simultaneously becoming more socially distant from them) and the Territorial Attachment convergence (Russian-speakers reporting stronger attachment to Estonia in 2023 despite a deteriorating political environment). The Territorial Attachment finding was flagged as requiring a theoretically grounded explanation before interpretation.", "body"),
    ("Vice 2 identified five convenient absences, most critically that the Belief in Conflict item-drop diagnostics had been flagged as incomplete in Session 20 but never run — despite Belief in Conflict being one of the strongest within-group effects in the dataset and one of the psychometrically weakest composites.", "body"),
    ("Virtue 1 identified a structural pattern running across the full composite battery: behavioral and affective integration indicators (contact, territorial attachment, group identity) are converging between groups, while attitudinal and structural perception indicators (social distance, conflict beliefs, perceived inequality) are diverging. This cross-composite pattern is more theoretically informative than any individual composite finding.", "body"),
    ("Virtue 2 identified three undersold strengths: the two-wave design spans the February 2022 Russian invasion of Ukraine and can be framed as a pre/post geopolitical shock comparison; the cross-language R replication is a methodological practice rare in thesis research; and the excluded Ukrainian refugee social distance items constitute substantive evidence about the political specificity of Russian-speaker out-group attitudes rather than merely a confound to be discarded.", "body"),
    ("The audit produced a ruling of Conditional — proceed to writing but address specified conditions first. A full Blindspot Audit Report was generated as a standalone document (reports/Blindspot_Audit_Report.docx) containing detailed findings, interpretive accounts, and a consolidated action checklist.", "body"),
    ("The Blindspot audit is the final step in the quality assurance sequence before writing begins: composite construction \u2192 Referee 2 audit (coding correctness) \u2192 cross-language R replication (software independence) \u2192 Blindspot audit (perceptual completeness) \u2192 writing.", "body"),
]

# Find the paragraph containing "6. Decision Traceability" to insert before it.
target_idx = None
for i, para in enumerate(doc.paragraphs):
    if para.text.strip().startswith("6. Decision Traceability"):
        target_idx = i
        break

if target_idx is None:
    raise RuntimeError("Could not find '6. Decision Traceability' heading.")

target_para = doc.paragraphs[target_idx]
target_style = target_para.style
print(f"Target paragraph style: {target_style.name}")

# Try to find a sample body paragraph style to mimic
body_style = None
subheading_style = None
# Find a plain body paragraph (not a heading) to copy style from
for p in doc.paragraphs:
    if p.style is None:
        continue
    if p.style.name.startswith("Heading 2") and subheading_style is None:
        subheading_style = p.style
    if (not p.style.name.startswith("Heading")) and body_style is None and p.text.strip():
        body_style = p.style

print(f"Body style: {body_style.name if body_style else 'None'}")
print(f"Subheading style: {subheading_style.name if subheading_style else 'None'}")

# Insert new paragraphs before the target by using lxml manipulation.
# python-docx doesn't have insert_before directly, so use element manipulation.
target_element = target_para._element

for text, hint in new_section:
    new_para = deepcopy(target_para)
    # Clear existing runs
    for run in new_para.runs:
        run._element.getparent().remove(run._element)
    # Clear any text in pPr or other elements; easier approach: create fresh paragraph
    # Actually simpler: use doc.add_paragraph semantics via element insertion
    # Reset by removing all children except pPr
    pPr = new_para._element.find(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr"
    )
    for child in list(new_para._element):
        new_para._element.remove(child)
    if pPr is not None:
        new_para._element.append(pPr)
    # Set the style
    if hint == "h2":
        # Use the target's style as a stand-in for section heading
        new_para.style = target_style
    elif hint == "h3":
        new_para.style = subheading_style if subheading_style else target_style
    else:
        if body_style is not None:
            new_para.style = body_style
    # Add the text
    run = new_para.add_run(text)
    if hint in ("h2", "h3"):
        run.bold = True
    # Insert before the target
    target_element.addprevious(new_para._element)

doc.save(DOC_PATH)
print(f"Saved. Inserted {len(new_section)} paragraphs before '6. Decision Traceability'.")
