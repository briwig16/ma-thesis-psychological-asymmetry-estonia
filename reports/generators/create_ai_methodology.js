const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak, LevelFormat } = require("docx");

// ── Shared styles ──
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };
const TABLE_WIDTH = 9360;

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: "2B4C7E", type: ShadingType.CLEAR },
    margins: cellMargins,
    verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.LEFT,
      children: [new TextRun({ text, bold: true, font: "Arial", size: 20, color: "FFFFFF" })] })]
  });
}

function cell(text, width, opts = {}) {
  const runs = [];
  if (opts.bold) {
    runs.push(new TextRun({ text, bold: true, font: "Arial", size: 20 }));
  } else {
    // Handle inline bold markers **text**
    const parts = text.split(/(\*\*[^*]+\*\*)/);
    for (const part of parts) {
      if (part.startsWith("**") && part.endsWith("**")) {
        runs.push(new TextRun({ text: part.slice(2, -2), bold: true, font: "Arial", size: 20 }));
      } else {
        runs.push(new TextRun({ text: part, font: "Arial", size: 20 }));
      }
    }
  }
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: opts.shading ? { fill: opts.shading, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({ children: runs })]
  });
}

function heading(text, level) {
  return new Paragraph({
    heading: level,
    spacing: { before: level === HeadingLevel.HEADING_1 ? 360 : 240, after: 200 },
    children: [new TextRun({ text, font: "Arial", bold: true,
      size: level === HeadingLevel.HEADING_1 ? 32 : level === HeadingLevel.HEADING_2 ? 26 : 22 })]
  });
}

function para(text, opts = {}) {
  const runs = [];
  // Split on bold markers
  const parts = text.split(/(\*\*[^*]+\*\*)/);
  for (const part of parts) {
    if (part.startsWith("**") && part.endsWith("**")) {
      runs.push(new TextRun({ text: part.slice(2, -2), bold: true, font: "Arial", size: 21,
        ...(opts.italic ? { italics: true } : {}) }));
    } else {
      runs.push(new TextRun({ text: part, font: "Arial", size: 21,
        ...(opts.italic ? { italics: true } : {}),
        ...(opts.color ? { color: opts.color } : {}) }));
    }
  }
  return new Paragraph({
    spacing: { after: opts.spacingAfter || 160, before: opts.spacingBefore || 0 },
    alignment: opts.alignment || AlignmentType.LEFT,
    children: runs
  });
}

function bulletItem(text, ref) {
  const parts = text.split(/(\*\*[^*]+\*\*)/);
  const runs = [];
  for (const part of parts) {
    if (part.startsWith("**") && part.endsWith("**")) {
      runs.push(new TextRun({ text: part.slice(2, -2), bold: true, font: "Arial", size: 21 }));
    } else {
      runs.push(new TextRun({ text: part, font: "Arial", size: 21 }));
    }
  }
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 100 },
    children: runs
  });
}

// ── Build Document ──
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "2B4C7E" },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "3A6BA5" },
        paragraph: { spacing: { before: 240, after: 180 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial", color: "4A4A4A" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 } },
    ]
  },
  numbering: {
    config: [
      { reference: "bullets1", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets2", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets3", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets4", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets5", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets6", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets7", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "bullets8", levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers1", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "2B4C7E", space: 4 } },
          children: [new TextRun({ text: "AI-Assisted Research Methodology", font: "Arial", size: 18, color: "999999", italics: true })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: "CCCCCC", space: 4 } },
          children: [
            new TextRun({ text: "Page ", font: "Arial", size: 18, color: "999999" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "999999" })
          ]
        })]
      })
    },
    children: [
      // ══════════════════════════════════════════
      // TITLE
      // ══════════════════════════════════════════
      new Paragraph({ spacing: { before: 600, after: 0 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Use of AI-Assisted Analysis", font: "Arial", size: 44, bold: true, color: "2B4C7E" })] }),
      new Paragraph({ spacing: { after: 80 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "in the Estonian Integration Monitoring Study", font: "Arial", size: 44, bold: true, color: "2B4C7E" })] }),

      new Paragraph({ spacing: { before: 200, after: 40 }, alignment: AlignmentType.CENTER,
        border: { top: { style: BorderStyle.SINGLE, size: 6, color: "2B4C7E", space: 8 } },
        children: [] }),

      new Paragraph({ spacing: { after: 40 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Methodology, Documentation, and Quality Assurance", font: "Arial", size: 24, color: "666666", italics: true })] }),
      new Paragraph({ spacing: { after: 40 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Brian Wiggins", font: "Arial", size: 22 })] }),
      new Paragraph({ spacing: { after: 400 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "March 2026", font: "Arial", size: 22, color: "666666" })] }),

      // ══════════════════════════════════════════
      // 1. INTRODUCTION
      // ══════════════════════════════════════════
      heading("1. Introduction", HeadingLevel.HEADING_1),

      para("This document describes how Claude Code, an AI-powered coding assistant developed by Anthropic, was used as a research tool during the quantitative analysis phase of my master\u2019s thesis examining Estonian-Russian intergroup relations using Estonian Integration Monitoring (EIM) survey data from 2020 and 2023."),

      para("The purpose of this document is to provide transparency about the role AI played in the research process, the safeguards that were put in place to ensure analytical integrity, and the systematic audit and replication procedures used to verify all results."),

      heading("1.1 What is Claude Code?", HeadingLevel.HEADING_2),

      para("Claude Code is a command-line AI assistant that operates directly within a project\u2019s file system. Unlike chat-based AI tools, Claude Code reads and writes files, executes scripts, and maintains persistent context about the project through structured documentation files. It functions as a collaborative partner in the coding and analysis workflow rather than as a standalone question-answering tool."),

      para("Critically, Claude Code does not have access to the internet during analysis sessions, cannot retrieve external data, and operates only on the files present in the project directory. All statistical computations are performed by standard scientific Python libraries (pandas, NumPy, scikit-learn, statsmodels, pingouin) and R packages \u2014 the AI assists in writing and executing these scripts, not in performing the mathematics itself."),

      // ══════════════════════════════════════════
      // 2. SCOPE OF AI INVOLVEMENT
      // ══════════════════════════════════════════
      heading("2. Scope of AI Involvement", HeadingLevel.HEADING_1),

      para("Claude Code was used for the following tasks during the analysis phase:"),

      bulletItem("**Script development:** Writing Python and R scripts for data cleaning, composite variable construction, PCA validation, reliability analysis (Cronbach\u2019s alpha), and group comparisons (Welch\u2019s t-tests, Cohen\u2019s d effect sizes)", "bullets1"),
      bulletItem("**Data exploration:** Investigating variable distributions, identifying coding schemes (e.g., \u201CDon\u2019t know\u201D codes), and mapping item names between the 2020 and 2023 survey waves", "bullets1"),
      bulletItem("**Visualization creation:** Building HTML-based interactive charts (dumbbell charts, radar charts, mind maps) for between-group and within-group comparisons", "bullets1"),
      bulletItem("**Report generation:** Producing formatted Word documents summarizing composite statistics, comparison tables, and detailed analyses of individual constructs", "bullets1"),
      bulletItem("**Documentation maintenance:** Maintaining a living project specification and detailed session log of all analytical decisions", "bullets1"),

      para("Claude Code was **not** used for:", { spacingBefore: 160 }),

      bulletItem("**Theoretical framing or literature review** \u2014 all theoretical choices (variable selection, construct definitions, interpretive frameworks) were made by the researcher based on the intergroup relations literature", "bullets2"),
      bulletItem("**Research design decisions** \u2014 the choice to focus on descriptive/comparative analysis, the selection of the two ethnic groups, and the decision to examine cross-year change were all researcher-driven", "bullets2"),
      bulletItem("**Interpretation of results** \u2014 the AI was explicitly instructed not to interpret findings as \u201Cgood\u201D or \u201Cbad\u201D and to focus only on whether the analytical specification was correct (see Section 4)", "bullets2"),
      bulletItem("**Data collection** \u2014 both EIM datasets were collected by independent survey organizations prior to this analysis", "bullets2"),

      // ══════════════════════════════════════════
      // 3. DOCUMENTATION SYSTEM
      // ══════════════════════════════════════════
      heading("3. Documentation System", HeadingLevel.HEADING_1),

      para("A two-file documentation system was maintained throughout the project to ensure traceability and reproducibility of all analytical decisions."),

      heading("3.1 CLAUDE.md \u2014 Living Project Specification", HeadingLevel.HEADING_2),

      para("This file serves as the project\u2019s \u201Csingle source of truth.\u201D Claude Code reads it at the start of every session, which means it functions as persistent memory across conversations. It contains:"),

      bulletItem("**Key decisions table** \u2014 every consequential analytical decision recorded with date and rationale (e.g., dropping Q67_1 from the Superordinate Identity composite, switching 2020 ethnicity classification from T7 to T9)", "bullets3"),
      bulletItem("**Composite variable quick reference** \u2014 items, scales, coding direction, and reverse-coding requirements for all 8 composites and 2 single-item variables", "bullets3"),
      bulletItem("**Critical gotchas** \u2014 documented pitfalls such as the asymmetric item assignment in Social Distance (Estonians rate Russian-speakers, Russians rate Estonian-speakers), the non-obvious Q44 scale direction, and the contact scale inversion", "bullets3"),
      bulletItem("**Dropped analyses** \u2014 record of analyses that were attempted and abandoned, with reasons (e.g., Perceived Cultural Threat composite, Institutional Trust composite)", "bullets3"),
      bulletItem("**Scale inversions for visualizations** \u2014 explicit documentation of which variables are inverted in charts versus reported in their original metric", "bullets3"),
      bulletItem("**Sample restrictions and missing value handling** \u2014 pairwise vs. listwise deletion rules, composite N vs. PCA N differences", "bullets3"),

      para("Because the AI reads this file at session start, it cannot \u201Cforget\u201D a prior decision or inadvertently contradict an earlier choice. If a decision is revised, both the old and new entries remain visible in the log."),

      heading("3.2 SESSION_LOG.md \u2014 Detailed Analytical Record", HeadingLevel.HEADING_2),

      para("This file provides a chronological, session-by-session record of all analytical work performed. Each session entry includes:"),

      bulletItem("Specific analyses run (with script names and output)", "bullets4"),
      bulletItem("PCA results (eigenvalues, variance explained, Kaiser criterion, factor loadings)", "bullets4"),
      bulletItem("Reliability statistics (Cronbach\u2019s alpha with 95% CIs, RMSR)", "bullets4"),
      bulletItem("Group comparison tables (means, SDs, Cohen\u2019s d, p-values)", "bullets4"),
      bulletItem("Between-group and within-group comparison results across years", "bullets4"),
      bulletItem("Decisions made during the session with rationale", "bullets4"),

      para("The SESSION_LOG currently contains 20 numbered sections spanning 4 working sessions (March 10\u201331, 2026), documenting the full evolution from initial data preparation through final composite validation."),

      // ══════════════════════════════════════════
      // 4. ESTIMATION PHILOSOPHY
      // ══════════════════════════════════════════
      heading("4. Estimation Philosophy", HeadingLevel.HEADING_1),

      para("A guiding principle was established at the outset and embedded in the AI\u2019s instructions:"),

      new Paragraph({
        spacing: { before: 120, after: 120 },
        indent: { left: 720, right: 720 },
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: "2B4C7E", space: 8 } },
        children: [new TextRun({ text: "Design before results. ", font: "Arial", size: 21, bold: true, italics: true }),
          new TextRun({ text: "Do not express concern or excitement about point estimates. Do not interpret results as \u201Cgood\u201D or \u201Cbad\u201D until the design is intentional. Focus entirely on whether the specification is correct. Results are meaningless until we\u2019re confident the \u201Cexperiment\u201D is designed on purpose.", font: "Arial", size: 21, italics: true })]
      }),

      para("This philosophy meant that when the AI produced output \u2014 for example, a Cohen\u2019s d showing a large between-group difference \u2014 it would not comment on whether this was a \u201Csurprising\u201D or \u201Cinteresting\u201D finding. Instead, it would focus on whether the items were correctly assigned, whether reverse-coding had been applied properly, whether \u201CDon\u2019t know\u201D responses had been excluded, and whether the composite was psychometrically sound. Interpretation was reserved entirely for the researcher."),

      para("This approach also guarded against a specific risk of AI-assisted analysis: the temptation to let striking results drive design choices. By separating specification from interpretation, the analytical pipeline was built on methodological grounds rather than being steered toward particular findings."),

      // ══════════════════════════════════════════
      // 5. QUALITY ASSURANCE
      // ══════════════════════════════════════════
      heading("5. Quality Assurance and Audit Process", HeadingLevel.HEADING_1),

      para("Three independent layers of verification were used to ensure the accuracy and reproducibility of all results."),

      heading("5.1 Referee 2 Audit Protocol", HeadingLevel.HEADING_2),

      para("A formal audit protocol was established in which Claude Code was given the role of \u201CReferee 2\u201D \u2014 a simulated independent reviewer tasked with systematically verifying every composite variable. The protocol operated under a strict rule: **the referee could never modify the author\u2019s code.** It could only read files, run scripts, and create its own independent replication scripts in a separate directory."),

      para("The audit proceeded in two rounds:"),

      para("**Round 1 (March 27, 2026):** The referee independently replicated all 8 composite variables for 2023, verifying:", { spacingBefore: 120 }),
      bulletItem("Cronbach\u2019s alpha values and 95% confidence intervals", "bullets5"),
      bulletItem("PCA eigenvalues and variance explained", "bullets5"),
      bulletItem("Group means and standard deviations for Estonians and Russians", "bullets5"),
      bulletItem("Cohen\u2019s d effect sizes and significance levels", "bullets5"),
      bulletItem("Correct handling of \u201CDon\u2019t know\u201D recoding (code 9 \u2192 NaN)", "bullets5"),
      bulletItem("Correct reverse-coding of Q67_4, Q63_3, and Q63_4", "bullets5"),
      bulletItem("Correct asymmetric item assignment for Social Distance Primary Out-group", "bullets5"),

      para("The Round 1 verdict was **Minor Revisions** \u2014 all values were verified, with organizational recommendations for improving replication readiness."),

      para("**Round 2 (March 28, 2026):** After addressing Round 1 feedback, the referee verified:", { spacingBefore: 120 }),
      bulletItem("The updated 3-item Superordinate Identity composite (Q67_1 dropped)", "bullets6"),
      bulletItem("All 8 composites rebuilt from the 2020 SPSS data using T9 ethnicity classification", "bullets6"),
      bulletItem("The Social Distance two-factor varimax rotation and split into Primary and General Out-group", "bullets6"),

      para("Round 2 result: **33/33 verification checks passed.** Verdict: **Accept.**"),

      heading("5.2 Cross-Language Replication in R", HeadingLevel.HEADING_2),

      para("To verify that results were not artifacts of a specific software implementation, the entire analysis was independently replicated in R using different statistical libraries (prcomp for PCA, psych::alpha for reliability, t.test for group comparisons)."),

      para("Results of the cross-language replication:"),

      new Table({
        width: { size: TABLE_WIDTH, type: WidthType.DXA },
        columnWidths: [3120, 3120, 3120],
        rows: [
          new TableRow({ children: [
            headerCell("Metric Category", 3120),
            headerCell("Checks", 3120),
            headerCell("Result", 3120),
          ]}),
          new TableRow({ children: [
            cell("Cronbach\u2019s alpha (both years)", 3120),
            cell("16", 3120),
            cell("16/16 PASS", 3120),
          ]}),
          new TableRow({ children: [
            cell("Group means", 3120, { shading: "F5F5F5" }),
            cell("48", 3120, { shading: "F5F5F5" }),
            cell("48/48 PASS", 3120, { shading: "F5F5F5" }),
          ]}),
          new TableRow({ children: [
            cell("Cohen\u2019s d effect sizes", 3120),
            cell("16", 3120),
            cell("16/16 PASS", 3120),
          ]}),
          new TableRow({ children: [
            cell("PCA variance explained", 3120, { shading: "F5F5F5" }),
            cell("80 (total)", 3120, { shading: "F5F5F5" }),
            cell("70/80 PASS", 3120, { shading: "F5F5F5" }),
          ]}),
        ]
      }),

      para("The 10 non-passing checks were all PCA variance percentage comparisons with differences \u2264 0.05 percentage points \u2014 rounding artifacts arising from differences between R\u2019s prcomp (SVD-based) and Python\u2019s sklearn PCA implementations. **All substantive statistics (alphas, means, and effect sizes) matched exactly across languages.**", { spacingBefore: 160 }),

      heading("5.3 Reproducible Script Pipeline", HeadingLevel.HEADING_2),

      para("All analysis scripts are numbered sequentially (01 through 18) and can be executed as a full pipeline via a single build command. Each script:"),

      bulletItem("Loads data from a common source file", "bullets7"),
      bulletItem("Applies consistent \u201CDon\u2019t know\u201D recoding (code 9 \u2192 NaN)", "bullets7"),
      bulletItem("Documents its purpose and item mapping in comments", "bullets7"),
      bulletItem("Outputs results to the console for verification", "bullets7"),

      para("The pipeline is deterministic \u2014 running it from scratch on the original data files reproduces all reported values exactly."),

      // ══════════════════════════════════════════
      // 6. DECISION TRACEABILITY
      // ══════════════════════════════════════════
      heading("6. Decision Traceability", HeadingLevel.HEADING_1),

      para("Every analytical decision in the project is traceable through the documentation system. The following table illustrates representative examples:"),

      new Table({
        width: { size: TABLE_WIDTH, type: WidthType.DXA },
        columnWidths: [1560, 3200, 2400, 2200],
        rows: [
          new TableRow({ children: [
            headerCell("Date", 1560),
            headerCell("Decision", 3200),
            headerCell("Rationale", 2400),
            headerCell("Verification", 2200),
          ]}),
          new TableRow({ children: [
            cell("Mar 19", 1560),
            cell("Dropped Q67_1 from Superordinate Identity", 3200),
            cell("Weakened Russian scale; 3-item version cleaner", 2400),
            cell("PCA by ethnicity confirmed", 2200),
          ]}),
          new TableRow({ children: [
            cell("Mar 23", 1560, { shading: "F5F5F5" }),
            cell("Split Social Distance into Primary and General", 3200, { shading: "F5F5F5" }),
            cell("Varimax rotation revealed 2 factors (r ~ .52\u2013.62)", 2400, { shading: "F5F5F5" }),
            cell("Referee 2 verified split", 2200, { shading: "F5F5F5" }),
          ]}),
          new TableRow({ children: [
            cell("Mar 23", 1560),
            cell("Excluded Ukrainian refugee items from SD General", 3200),
            cell("Asymmetric Russian bias masked general attitudes", 2400),
            cell("With/without comparison documented", 2200),
          ]}),
          new TableRow({ children: [
            cell("Mar 28", 1560, { shading: "F5F5F5" }),
            cell("Switched 2020 ethnicity from T7 to T9", 3200, { shading: "F5F5F5" }),
            cell("T7 = language (wrong construct); T9 = nationality", 2400, { shading: "F5F5F5" }),
            cell("Full cascade: all values recomputed", 2200, { shading: "F5F5F5" }),
          ]}),
          new TableRow({ children: [
            cell("Mar 30", 1560),
            cell("Confirmed Perceived Cultural Threat drop", 3200),
            cell("Items exist in 2020 only; no 2023 equivalents", 2400),
            cell("2020 SPSS file inspected", 2200),
          ]}),
        ]
      }),

      para("In total, the CLAUDE.md key decisions table contains 15 documented decisions, and the SESSION_LOG contains over 800 lines of detailed analytical narrative.", { spacingBefore: 160 }),

      // ══════════════════════════════════════════
      // 7. WHAT THE AI DID vs. WHAT I DID
      // ══════════════════════════════════════════
      heading("7. Division of Responsibility", HeadingLevel.HEADING_1),

      new Table({
        width: { size: TABLE_WIDTH, type: WidthType.DXA },
        columnWidths: [4680, 4680],
        rows: [
          new TableRow({ children: [
            headerCell("Researcher (Brian Wiggins)", 4680),
            headerCell("AI Assistant (Claude Code)", 4680),
          ]}),
          new TableRow({ children: [
            cell("Selected research question and theoretical framework", 4680),
            cell("Wrote Python/R scripts implementing the specified analyses", 4680),
          ]}),
          new TableRow({ children: [
            cell("Chose which survey items map to which constructs", 4680, { shading: "F5F5F5" }),
            cell("Executed scripts and reported raw statistical output", 4680, { shading: "F5F5F5" }),
          ]}),
          new TableRow({ children: [
            cell("Made all inclusion/exclusion decisions (item drops, scale choices, sample restrictions)", 4680),
            cell("Maintained documentation files per researcher instructions", 4680),
          ]}),
          new TableRow({ children: [
            cell("Interpreted results in the context of intergroup relations theory", 4680, { shading: "F5F5F5" }),
            cell("Built visualizations to researcher specifications", 4680, { shading: "F5F5F5" }),
          ]}),
          new TableRow({ children: [
            cell("Decided when psychometric evidence was sufficient to retain or drop a composite", 4680),
            cell("Performed audit/replication checks as instructed", 4680),
          ]}),
          new TableRow({ children: [
            cell("Wrote all thesis prose (introduction, methods, results, discussion)", 4680, { shading: "F5F5F5" }),
            cell("Generated formatted summary tables and reports", 4680, { shading: "F5F5F5" }),
          ]}),
        ]
      }),

      // ══════════════════════════════════════════
      // 8. LIMITATIONS AND SAFEGUARDS
      // ══════════════════════════════════════════
      heading("8. Limitations and Safeguards", HeadingLevel.HEADING_1),

      para("Several limitations of AI-assisted analysis were identified and actively mitigated:"),

      bulletItem("**Coding errors:** Mitigated by the Referee 2 audit protocol, which independently replicated all composites, and by cross-language replication in R. Both checks confirmed all values.", "bullets8"),
      bulletItem("**Variable mapping errors:** The most common error source in this project was getting the Social Distance item assignments backwards (which group rates which out-group). This was documented as a \u201Ccritical gotcha\u201D in CLAUDE.md so the AI would flag it in every session.", "bullets8"),
      bulletItem("**Confirmation bias:** The \u201Cdesign before results\u201D philosophy and the instruction not to interpret results prevented the AI from reinforcing any particular narrative. When the T7\u2192T9 ethnicity switch changed a significant result to non-significant, the AI updated all documentation without commentary.", "bullets8"),
      bulletItem("**Session discontinuity:** Because AI sessions have finite context windows, the CLAUDE.md specification ensures no prior decision is lost between sessions. The AI re-reads this file at every session start.", "bullets8"),
      bulletItem("**Transparency:** All scripts, documentation files, and replication code are included in the project repository. Any reported value can be traced back to a specific script, verified against the SESSION_LOG, and independently reproduced.", "bullets8"),

      // ══════════════════════════════════════════
      // 9. FILE INVENTORY
      // ══════════════════════════════════════════
      heading("9. Project File Inventory", HeadingLevel.HEADING_1),

      para("The following files constitute the analytical record:"),

      new Table({
        width: { size: TABLE_WIDTH, type: WidthType.DXA },
        columnWidths: [2200, 4360, 2800],
        rows: [
          new TableRow({ children: [
            headerCell("Category", 2200),
            headerCell("Files", 4360),
            headerCell("Purpose", 2800),
          ]}),
          new TableRow({ children: [
            cell("Documentation", 2200),
            cell("CLAUDE.md, SESSION_LOG.md", 4360),
            cell("Project spec + detailed analytical log", 2800),
          ]}),
          new TableRow({ children: [
            cell("Analysis scripts", 2200, { shading: "F5F5F5" }),
            cell("code/01\u201318 (Python)", 4360, { shading: "F5F5F5" }),
            cell("Full numbered pipeline", 2800, { shading: "F5F5F5" }),
          ]}),
          new TableRow({ children: [
            cell("Replication", 2200),
            cell("code/replication/ (3 Python + 1 R script)", 4360),
            cell("Referee 2 audit + R replication", 2800),
          ]}),
          new TableRow({ children: [
            cell("Audit reports", 2200, { shading: "F5F5F5" }),
            cell("correspondence/referee2/ (2 reports)", 4360, { shading: "F5F5F5" }),
            cell("Round 1 + Round 2 verdicts", 2800, { shading: "F5F5F5" }),
          ]}),
          new TableRow({ children: [
            cell("Visualizations", 2200),
            cell("viz/ (3 HTML interactive charts)", 4360),
            cell("Dumbbell, radar, mind map", 2800),
          ]}),
          new TableRow({ children: [
            cell("Summary reports", 2200, { shading: "F5F5F5" }),
            cell("reports/ (5 Word documents)", 4360, { shading: "F5F5F5" }),
            cell("Composite stats and comparisons", 2800, { shading: "F5F5F5" }),
          ]}),
          new TableRow({ children: [
            cell("Data", 2200),
            cell("data/ (2023 CSV, 2020 SPSS, 2020 composites CSV)", 4360),
            cell("Source and derived datasets", 2800),
          ]}),
        ]
      }),

      // ══════════════════════════════════════════
      // 10. CONCLUSION
      // ══════════════════════════════════════════
      heading("10. Conclusion", HeadingLevel.HEADING_1),

      para("Claude Code served as an analytical assistant \u2014 accelerating the implementation of statistical procedures, maintaining rigorous documentation, and enabling systematic verification of results. All theoretical and interpretive decisions remained with the researcher. The combination of a living project specification, a detailed session log, a formal audit protocol with separation of author and reviewer roles, and cross-language replication provides a level of traceability and verifiability that exceeds what is typically achievable in manual analysis workflows."),

      para("The complete project directory, including all scripts, documentation, audit reports, and replication code, is available for inspection."),
    ]
  }]
});

// ── Write file ──
Packer.toBuffer(doc).then(buffer => {
  const path = __dirname + "/../AI_Assisted_Analysis_Methodology.docx";
  fs.writeFileSync(path, buffer);
  console.log("Created: " + path);
});
