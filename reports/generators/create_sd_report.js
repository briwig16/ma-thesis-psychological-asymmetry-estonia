const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };

// Table width for US Letter with 1" margins = 9360 DXA
const TABLE_WIDTH = 9360;

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: "2E4057", type: ShadingType.CLEAR },
    margins: cellMargins,
    verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, bold: true, font: "Arial", size: 20, color: "FFFFFF" })
    ]})]
  });
}

function dataCell(text, width, bold = false, shading = null) {
  const opts = {
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, bold, font: "Arial", size: 20 })
    ]})]
  };
  if (shading) opts.shading = { fill: shading, type: ShadingType.CLEAR };
  return opts;
}

function labelCell(text, width, bold = false, shading = null) {
  const opts = {
    borders,
    width: { size: width, type: WidthType.DXA },
    margins: cellMargins,
    verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.LEFT, children: [
      new TextRun({ text, bold, font: "Arial", size: 20 })
    ]})]
  };
  if (shading) opts.shading = { fill: shading, type: ShadingType.CLEAR };
  return opts;
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160 },
    ...opts,
    children: [new TextRun({ text, font: "Arial", size: 22, ...opts.run })]
  });
}

function heading(text, level) {
  return new Paragraph({
    heading: level,
    spacing: { before: 300, after: 200 },
    children: [new TextRun({ text, font: "Arial", bold: true, size: level === HeadingLevel.HEADING_1 ? 32 : (level === HeadingLevel.HEADING_2 ? 26 : 22) })]
  });
}

function boldItalicParagraph(parts) {
  return new Paragraph({
    spacing: { after: 160 },
    children: parts.map(p => new TextRun({ text: p.text, font: "Arial", size: 22, bold: p.bold || false, italics: p.italics || false }))
  });
}

// ── Between-group tables ──
const colWidths_bg = [1800, 600, 1560, 1560, 1000, 900, 940, 1000];

function betweenGroupTable(title, rows) {
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths_bg,
    rows: [
      // Header
      new TableRow({ children: [
        headerCell("Composite", 1800), headerCell("Year", 600),
        headerCell("Estonian M (SD)", 1560), headerCell("Russian M (SD)", 1560),
        headerCell("Cohen\u2019s d", 1000), headerCell("t", 900),
        headerCell("p", 940), headerCell("Sig.", 1000)
      ]}),
      ...rows.map(r => {
        const shade = r.highlight ? "FFF3CD" : null;
        return new TableRow({ children: [
          new TableCell(labelCell(r.comp, 1800, false, shade)),
          new TableCell(dataCell(r.year, 600, false, shade)),
          new TableCell(dataCell(r.est, 1560, false, shade)),
          new TableCell(dataCell(r.rus, 1560, false, shade)),
          new TableCell(dataCell(r.d, 1000, r.highlight, shade)),
          new TableCell(dataCell(r.t, 900, false, shade)),
          new TableCell(dataCell(r.p, 940, false, shade)),
          new TableCell(dataCell(r.sig, 1000, false, shade)),
        ]});
      })
    ]
  });
}

// ── Within-group tables ──
const colWidths_wg = [1800, 1000, 1560, 1560, 1000, 900, 940, 600];

function withinGroupTable(rows) {
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths_wg,
    rows: [
      new TableRow({ children: [
        headerCell("Composite", 1800), headerCell("Group", 1000),
        headerCell("2020 M (SD)", 1560), headerCell("2023 M (SD)", 1560),
        headerCell("Cohen\u2019s d", 1000), headerCell("t", 900),
        headerCell("p", 940), headerCell("Sig.", 600)
      ]}),
      ...rows.map(r => {
        const shade = r.highlight ? "FFF3CD" : null;
        return new TableRow({ children: [
          new TableCell(labelCell(r.comp, 1800, false, shade)),
          new TableCell(dataCell(r.group, 1000, false, shade)),
          new TableCell(dataCell(r.m2020, 1560, false, shade)),
          new TableCell(dataCell(r.m2023, 1560, false, shade)),
          new TableCell(dataCell(r.d, 1000, r.highlight, shade)),
          new TableCell(dataCell(r.t, 900, false, shade)),
          new TableCell(dataCell(r.p, 940, false, shade)),
          new TableCell(dataCell(r.sig, 600, false, shade)),
        ]});
      })
    ]
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 200, after: 200 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 22, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 160, after: 160 }, outlineLevel: 2 } },
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
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "EIM Social Distance Analysis", font: "Arial", size: 18, italics: true, color: "888888" })]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Page ", font: "Arial", size: 18, color: "888888" }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "888888" })]
      })] })
    },
    children: [
      // ── TITLE ──
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 100 },
        children: [new TextRun({ text: "Social Distance Composite Analysis", font: "Arial", size: 36, bold: true })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 100 },
        children: [new TextRun({ text: "The Effect of Ukrainian Refugee Items on Composite Structure", font: "Arial", size: 26, color: "555555" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 400 },
        children: [new TextRun({ text: "Estonian Integration Monitoring 2020 & 2023", font: "Arial", size: 22, color: "777777" })]
      }),

      // ── SECTION 1: OVERVIEW ──
      heading("1. Overview", HeadingLevel.HEADING_1),
      p("This report examines social distance composites measuring how Estonians and Russians in Estonia feel about out-group members. A principal components analysis of the full 11-item social distance battery in the 2023 EIM data revealed two distinct factors: attitudes toward the primary ethno-linguistic out-group (Russian-speakers for Estonians, Estonian-speakers for Russians) and attitudes toward general out-groups (Ukrainians, other Europeans, and non-Europeans). This led to the creation of two sub-composites."),
      p("We compare results from two versions of the general out-group sub-composite: one including Ukrainian refugee items (8 items) and one excluding them (5 items). The primary out-group sub-composite (3 items) remains unchanged across both versions. All items use a 1\u20135 scale where higher scores indicate more negative attitudes (greater social distance)."),

      // ── SECTION 2: COMPOSITE DEFINITIONS ──
      heading("2. Composite Definitions", HeadingLevel.HEADING_1),

      heading("2.1 Primary Out-group Social Distance (3 items)", HeadingLevel.HEADING_2),
      p("Measures attitudes toward the primary ethno-linguistic out-group across three social contexts:"),
      boldItalicParagraph([{ text: "Estonians: ", bold: true }, { text: "Q57_1 (neighbors), Q58_1 (work/study), Q59_1 (marriage) \u2014 all targeting Russian-speakers" }]),
      boldItalicParagraph([{ text: "Russians: ", bold: true }, { text: "Q57_2 (neighbors), Q58_2 (work/study), Q59_2 (marriage) \u2014 all targeting Estonian-speakers" }]),

      heading("2.2 General Out-group Social Distance", HeadingLevel.HEADING_2),
      boldItalicParagraph([{ text: "With Ukrainian items (8 items): ", bold: true }, { text: "Q57_3, Q57_4, Q57_5, Q58_3, Q58_4, Q58_5, Q59_3, Q59_4 \u2014 covering Ukrainian refugees, other Europeans, and people from outside Europe across all three social contexts." }]),
      boldItalicParagraph([{ text: "Without Ukrainian items (5 items): ", bold: true }, { text: "Q57_4, Q57_5, Q58_4, Q58_5, Q59_4 \u2014 covering other Europeans and people from outside Europe only." }]),

      heading("2.3 2020 Equivalents", HeadingLevel.HEADING_2),
      p("The 2020 EIM data contains only 3 general out-group items (K4X7_3, K4X8_3, K4X9_3) measuring attitudes toward new immigrants (arrived in the last 5 years). There are no separate Ukrainian, European, or non-European categories. The primary out-group items (K4X7_1/2, K4X8_1/2, K4X9_1/2) are directly comparable across years."),

      // ── SECTION 3: WITH UKRAINE ──
      heading("3. Results: With Ukrainian Refugee Items", HeadingLevel.HEADING_1),

      heading("3.1 Between-Group Comparisons (Estonian vs Russian)", HeadingLevel.HEADING_2),
      betweenGroupTable("With Ukrainian Items", [
        { comp: "General Out-group", year: "2020", est: "2.91 (1.01)", rus: "3.12 (1.02)", d: "\u22120.21", t: "\u22123.60", p: ".0003", sig: "***", highlight: false },
        { comp: "General Out-group", year: "2023", est: "2.65 (0.86)", rus: "2.73 (0.83)", d: "\u22120.10", t: "\u22121.76", p: ".079", sig: "ns", highlight: false },
        { comp: "Primary Out-group", year: "2020", est: "2.51 (0.88)", rus: "1.90 (0.80)", d: "+0.74", t: "12.42", p: "<.0001", sig: "***", highlight: true },
        { comp: "Primary Out-group", year: "2023", est: "2.91 (1.04)", rus: "1.83 (0.77)", d: "+1.18", t: "21.30", p: "<.0001", sig: "***", highlight: true },
      ]),
      p(""),

      heading("3.2 Within-Group Change: 2020 \u2192 2023", HeadingLevel.HEADING_2),
      withinGroupTable([
        { comp: "General Out-group", group: "Estonian", m2020: "2.91 (1.01)", m2023: "2.65 (0.86)", d: "\u22120.28", t: "5.34", p: "<.0001", sig: "***", highlight: false },
        { comp: "General Out-group", group: "Russian", m2020: "3.12 (1.02)", m2023: "2.73 (0.83)", d: "\u22120.42", t: "6.79", p: "<.0001", sig: "***", highlight: false },
        { comp: "Primary Out-group", group: "Estonian", m2020: "2.51 (0.88)", m2023: "2.91 (1.04)", d: "+0.42", t: "\u22128.10", p: "<.0001", sig: "***", highlight: true },
        { comp: "Primary Out-group", group: "Russian", m2020: "1.90 (0.80)", m2023: "1.83 (0.77)", d: "\u22120.08", t: "1.27", p: ".205", sig: "ns", highlight: false },
      ]),
      p(""),

      // ── SECTION 4: WITHOUT UKRAINE ──
      heading("4. Results: Without Ukrainian Refugee Items", HeadingLevel.HEADING_1),

      heading("4.1 Between-Group Comparisons (Estonian vs Russian)", HeadingLevel.HEADING_2),
      betweenGroupTable("Without Ukrainian Items", [
        { comp: "General Out-group", year: "2020", est: "2.91 (1.01)", rus: "3.12 (1.02)", d: "\u22120.21", t: "\u22123.60", p: ".0003", sig: "***", highlight: false },
        { comp: "General Out-group", year: "2023", est: "2.70 (0.90)", rus: "2.60 (0.81)", d: "+0.11", t: "1.97", p: ".049", sig: "*", highlight: true },
        { comp: "Primary Out-group", year: "2020", est: "2.51 (0.88)", rus: "1.90 (0.80)", d: "+0.74", t: "12.42", p: "<.0001", sig: "***", highlight: false },
        { comp: "Primary Out-group", year: "2023", est: "2.91 (1.04)", rus: "1.83 (0.77)", d: "+1.18", t: "21.30", p: "<.0001", sig: "***", highlight: true },
      ]),
      p(""),

      heading("4.2 Within-Group Change: 2020 \u2192 2023", HeadingLevel.HEADING_2),
      withinGroupTable([
        { comp: "General Out-group", group: "Estonian", m2020: "2.91 (1.01)", m2023: "2.70 (0.90)", d: "\u22120.23", t: "4.29", p: "<.0001", sig: "***", highlight: false },
        { comp: "General Out-group", group: "Russian", m2020: "3.12 (1.02)", m2023: "2.60 (0.81)", d: "\u22120.56", t: "8.75", p: "<.0001", sig: "***", highlight: true },
        { comp: "Primary Out-group", group: "Estonian", m2020: "2.51 (0.88)", m2023: "2.91 (1.04)", d: "+0.42", t: "\u22128.10", p: "<.0001", sig: "***", highlight: true },
        { comp: "Primary Out-group", group: "Russian", m2020: "1.90 (0.80)", m2023: "1.83 (0.77)", d: "\u22120.08", t: "1.27", p: ".205", sig: "ns", highlight: false },
      ]),
      p(""),

      // ── SECTION 5: KEY DIFFERENCES ──
      heading("5. How Ukrainian Refugee Items Affect the Results", HeadingLevel.HEADING_1),

      heading("5.1 The Direction Flip in 2023 Between-Group Comparisons", HeadingLevel.HEADING_2),
      p("The most notable difference between the two versions is the reversal of the between-group gap on the general out-group composite in 2023:"),
      boldItalicParagraph([{ text: "With Ukrainian items: ", bold: true }, { text: "Russians are slightly more distant than Estonians (2.73 vs 2.65, d = \u22120.10, p = .079, non-significant). The groups appear statistically equivalent." }]),
      boldItalicParagraph([{ text: "Without Ukrainian items: ", bold: true }, { text: "Estonians are now more distant than Russians (2.70 vs 2.60, d = +0.11, p = .049, significant). The direction reverses." }]),
      p("This reversal indicates that Russians hold relatively more negative attitudes toward Ukrainian refugees specifically, which masks their otherwise more positive attitudes toward other Europeans and non-Europeans. When the Ukrainian items are removed, the underlying pattern becomes visible: Russians are actually more welcoming of general out-groups than Estonians in 2023."),

      heading("5.2 Amplified Russian Improvement Over Time", HeadingLevel.HEADING_2),
      p("Removing the Ukrainian items sharpens the magnitude of the Russian shift toward openness on general out-groups:"),
      boldItalicParagraph([{ text: "With Ukrainian items: ", bold: true }, { text: "d = \u22120.42 (2020 \u2192 2023)" }]),
      boldItalicParagraph([{ text: "Without Ukrainian items: ", bold: true }, { text: "d = \u22120.56 (2020 \u2192 2023)" }]),
      p("The Ukrainian items dampen what is actually a substantial increase in Russian openness toward non-Ukrainian out-groups. This is a meaningful difference\u2014the effect size increases by 33% when the Ukrainian items are excluded."),

      heading("5.3 Unchanged Findings", HeadingLevel.HEADING_2),
      p("Several core findings remain robust regardless of whether Ukrainian items are included:"),
      boldItalicParagraph([{ text: "1. ", bold: true }, { text: "Estonians became significantly more negative toward Russian-speakers from 2020 to 2023 (d = +0.43, p < .0001). This is the only composite that moved in the negative direction for either group." }]),
      boldItalicParagraph([{ text: "2. ", bold: true }, { text: "Russian attitudes toward Estonian-speakers did not change (d = \u22120.05, p = .428). This stability stands in stark contrast to the Estonian shift." }]),
      boldItalicParagraph([{ text: "3. ", bold: true }, { text: "The Estonian\u2013Russian gap on primary out-group social distance widened substantially from 2020 (d = 0.74) to 2023 (d = 1.18), representing a very large effect." }]),
      boldItalicParagraph([{ text: "4. ", bold: true }, { text: "Both groups became more welcoming toward general out-groups over time, regardless of Ukrainian item inclusion." }]),

      // ── SECTION 6: INTERPRETATION ──
      heading("6. Interpretation", HeadingLevel.HEADING_1),
      p("The divergent trajectories reveal a targeted rather than generalized shift in Estonian attitudes. Between 2020 and 2023, Estonians became more open to other Europeans, non-Europeans, and (when included) Ukrainian refugees, while simultaneously becoming substantially more negative toward Russian-speakers. This pattern is consistent with a response to post-2022 geopolitical events rather than a broad increase in xenophobia."),
      p("For Russians in Estonia, the pattern is one of general warming toward out-groups across the board, with the notable exception of Ukrainian refugees\u2014where attitudes are relatively more negative, likely reflecting the complex position of Russian-speakers in Estonia vis-\u00e0-vis the war in Ukraine. Their attitudes toward Estonian-speakers, meanwhile, remained entirely stable."),
      p("The practical implication for composite construction is clear: including Ukrainian refugee items in the general out-group composite obscures meaningful group differences by conflating two distinct attitudinal patterns. Researchers should consider analyzing Ukrainian attitudes separately or reporting results both with and without these items to provide a complete picture."),

      // ── SECTION 7: RELIABILITY ──
      heading("7. Reliability Summary", HeadingLevel.HEADING_1),

      new Table({
        width: { size: TABLE_WIDTH, type: WidthType.DXA },
        columnWidths: [2800, 900, 1100, 1100, 1100, 1180, 1180],
        rows: [
          new TableRow({ children: [
            headerCell("Composite", 2800), headerCell("Group", 900),
            headerCell("\u03B1", 1100), headerCell("KMO", 1100),
            headerCell("PC1 Var%", 1100), headerCell("N", 1180), headerCell("Items", 1180)
          ]}),
          ...[
            ["General (with Ukraine)", "Estonian", ".927", ".799", "66.4%", "652", "8"],
            ["General (with Ukraine)", "Russian", ".920", ".831", "64.9%", "384", "8"],
            ["General (no Ukraine)", "Estonian", ".897", ".703", "71.1%", "679", "5"],
            ["General (no Ukraine)", "Russian", ".879", ".743", "67.8%", "416", "5"],
            ["Primary Out-group", "Estonian", ".827", ".701", "74.4%", "699", "3"],
            ["Primary Out-group", "Russian", ".772", ".698", "68.7%", "436", "3"],
          ].map(r => new TableRow({ children: [
            new TableCell(labelCell(r[0], 2800)),
            new TableCell(dataCell(r[1], 900)),
            new TableCell(dataCell(r[2], 1100)),
            new TableCell(dataCell(r[3], 1100)),
            new TableCell(dataCell(r[4], 1100)),
            new TableCell(dataCell(r[5], 1180)),
            new TableCell(dataCell(r[6], 1180)),
          ]}))
        ]
      }),
      p(""),
      p("All composites demonstrate good to excellent reliability (\u03B1 > .77). The 8-item general composite has slightly higher alpha than the 5-item version due to the additional items, but both versions are well above conventional thresholds. The 3-item primary out-group composite shows the highest variance explained by a single factor (68.7\u201374.4%), confirming its unidimensional structure."),

      // ── CAVEAT ──
      heading("8. Caveats", HeadingLevel.HEADING_1),
      boldItalicParagraph([{ text: "Cross-year comparability of general out-group composites: ", bold: true }, { text: "The 2020 general out-group composite contains only 3 items measuring attitudes toward new immigrants, while the 2023 version contains 5 or 8 items with distinct target groups (Europeans, non-Europeans, and optionally Ukrainian refugees). Direct cross-year comparisons of general out-group composites should be interpreted with caution, as changes may reflect differences in composite composition as well as genuine attitudinal change." }]),
      boldItalicParagraph([{ text: "Cross-sectional design: ", bold: true }, { text: "Both surveys are independent cross-sections, not panel data. Within-group changes over time reflect population-level shifts, not individual-level change." }]),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/Users/brianwiggins/Desktop/Claude Code/EIM2/Social_Distance_Composite_Analysis.docx", buffer);
  console.log("Document created successfully.");
});
