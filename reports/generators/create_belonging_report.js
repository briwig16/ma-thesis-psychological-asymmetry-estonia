const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 60, bottom: 60, left: 100, right: 100 };
const TABLE_WIDTH = 9360;

function headerCell(text, width) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: { fill: "2E4057", type: ShadingType.CLEAR },
    margins: cellMargins, verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, bold: true, font: "Arial", size: 20, color: "FFFFFF" })
    ]})]
  });
}

function dataCell(text, width, bold = false, shading = null) {
  const opts = {
    borders, width: { size: width, type: WidthType.DXA },
    margins: cellMargins, verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, bold, font: "Arial", size: 20 })
    ]})]
  };
  if (shading) opts.shading = { fill: shading, type: ShadingType.CLEAR };
  return opts;
}

function labelCell(text, width, bold = false, shading = null) {
  const opts = {
    borders, width: { size: width, type: WidthType.DXA },
    margins: cellMargins, verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.LEFT, children: [
      new TextRun({ text, bold, font: "Arial", size: 20 })
    ]})]
  };
  if (shading) opts.shading = { fill: shading, type: ShadingType.CLEAR };
  return opts;
}

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160 }, ...opts,
    children: [new TextRun({ text, font: "Arial", size: 22, ...opts.run })]
  });
}

function heading(text, level) {
  return new Paragraph({
    heading: level, spacing: { before: 300, after: 200 },
    children: [new TextRun({ text, font: "Arial", bold: true,
      size: level === HeadingLevel.HEADING_1 ? 32 : (level === HeadingLevel.HEADING_2 ? 26 : 22) })]
  });
}

function bp(parts) {
  return new Paragraph({
    spacing: { after: 160 },
    children: parts.map(p => new TextRun({ text: p.text, font: "Arial", size: 22,
      bold: p.bold || false, italics: p.italics || false }))
  });
}

// Simple table builder
function makeTable(headers, rows, colWidths) {
  return new Table({
    width: { size: TABLE_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({ children: headers.map((h, i) => headerCell(h, colWidths[i])) }),
      ...rows.map(r => new TableRow({
        children: r.map((cell, i) => {
          if (i === 0) return new TableCell(labelCell(cell, colWidths[i], false, r.shade));
          return new TableCell(dataCell(cell, colWidths[i], false, r.shade));
        })
      }))
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
        children: [new TextRun({ text: "EIM Superordinate Identity Analysis", font: "Arial", size: 18, italics: true, color: "888888" })]
      })] })
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Page ", font: "Arial", size: 18, color: "888888" }),
                   new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "888888" })]
      })] })
    },
    children: [
      // TITLE
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
        children: [new TextRun({ text: "Superordinate Identity Patterns", font: "Arial", size: 36, bold: true })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
        children: [new TextRun({ text: "Composite Construction, Validation, and Group Comparisons", font: "Arial", size: 26, color: "555555" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
        children: [new TextRun({ text: "Estonian Integration Monitoring 2020 & 2023", font: "Arial", size: 22, color: "777777" })] }),

      // 1. CONSTRUCT OVERVIEW
      heading("1. Construct Overview", HeadingLevel.HEADING_1),
      p("The superordinate identity patterns variable captures the degree to which respondents identify with Estonia as an overarching national community, regardless of their ethnic or linguistic background. It reflects a sense of belonging to the broader Estonian polity\u2014feeling part of the society, taking pride in national symbols, and perceiving oneself as a full member rather than a marginalized outsider."),
      p("This composite was constructed from the Q67 battery in the 2023 EIM data and its equivalent (K6X5) in the 2020 data. The scale runs from 1 (strongly agree) to 4 (strongly disagree), so lower scores indicate stronger superordinate identification."),

      // 2. ITEM SELECTION
      heading("2. Item Selection", HeadingLevel.HEADING_1),

      heading("2.1 Initial 4-Item Battery", HeadingLevel.HEADING_2),
      p("The Q67 battery contains four candidate items measuring national belonging:"),

      makeTable(
        ["Item", "Text", "Coding"],
        [
          ["Q67_1", "You feel a connection with Estonia", "As-is (1\u20134)"],
          ["Q67_2", "You feel proud when you see the Estonian flag flying", "As-is (1\u20134)"],
          ["Q67_4", "You feel like a second-class citizen in Estonian society", "Reverse-coded (5 \u2212 Q67_4)"],
          ["Q67_5", "You feel part of Estonian society", "As-is (1\u20134)"],
        ],
        [1200, 5960, 2200]
      ),
      p(""),

      heading("2.2 Decision to Drop Q67_1", HeadingLevel.HEADING_2),
      p("PCA and reliability analyses conducted separately by ethnicity revealed that Q67_1 (\u201CYou feel a connection with Estonia\u201D) weakened the scale for Russian respondents. This item likely captures a different dimension of attachment\u2014an affective or sentimental bond with the country\u2014that does not load cleanly with the other items measuring societal membership and status for the Russian-speaking population. Q67_1 was therefore excluded, yielding a final 3-item composite."),

      heading("2.3 Final 3-Item Composite", HeadingLevel.HEADING_2),

      makeTable(
        ["Item", "Text", "Coding", "2020 Equivalent"],
        [
          ["Q67_2", "You feel proud when you see the Estonian flag flying", "As-is", "K6X5_2"],
          ["Q67_4", "You feel like a second-class citizen in Estonian society", "Reversed", "K6X5_3"],
          ["Q67_5", "You feel part of Estonian society", "As-is", "K6X5_4"],
        ],
        [1000, 4360, 1200, 2800]
      ),
      p(""),
      p("The composite is computed as the mean of the three items (with Q67_4 / K6X5_3 reverse-coded). Lower values indicate stronger superordinate identification."),

      // 3. PCA AND RELIABILITY
      heading("3. PCA and Reliability Validation", HeadingLevel.HEADING_1),

      heading("3.1 2023 Results by Ethnicity", HeadingLevel.HEADING_2),

      makeTable(
        ["Metric", "Estonian (N = 807)", "Russian (N = 423)"],
        [
          ["Eigenvalue (PC1)", "1.893", "2.051"],
          ["Variance explained", "63.1%", "68.4%"],
          ["Cronbach\u2019s \u03B1", ".698", ".760"],
          ["\u03B1 95% CI", "[.665, .729]", "[.718, .797]"],
          ["RMSR", ".189", ".165"],
          ["Kaiser components", "1", "1"],
          ["Avg. inter-item r", ".442", ".524"],
        ],
        [3120, 3120, 3120]
      ),
      p(""),

      p("Factor loadings for both groups ranged from .68 to .88, confirming that all three items load substantially on a single component. The Kaiser criterion retained exactly one component in both groups, supporting unidimensionality."),

      heading("3.2 2020 Results by Ethnicity", HeadingLevel.HEADING_2),

      makeTable(
        ["Metric", "Estonian", "Russian"],
        [
          ["Eigenvalue (PC1)", "1.840", "1.731"],
          ["Variance explained", "61.3%", "57.7%"],
          ["Cronbach\u2019s \u03B1", ".614", ".618"],
          ["RMSR", "\u2014", "\u2014"],
          ["Kaiser components", "1", "1"],
        ],
        [3120, 3120, 3120]
      ),
      p(""),

      p("The 2020 composites show weaker but still acceptable reliability. The lower alpha values (\u03B1 \u2248 .61) reflect approximately 39% error variance, which attenuates effect sizes and inflates standard errors. This is partly a mechanical consequence of having only 3 items\u2014with an average inter-item correlation of .40, three items yield \u03B1 \u2248 .67 by formula, whereas eight items with the same correlations would yield \u03B1 \u2248 .84. The unidimensional structure is nevertheless confirmed by the Kaiser criterion."),

      // 4. GROUP COMPARISONS
      heading("4. Group Comparisons", HeadingLevel.HEADING_1),
      p("All comparisons use Welch\u2019s t-test (unequal variances) and Cohen\u2019s d with the root-mean-square pooled SD."),

      heading("4.1 Between-Group: Estonian vs Russian", HeadingLevel.HEADING_2),

      makeTable(
        ["Year", "Estonian M (SD)", "Russian M (SD)", "Cohen\u2019s d", "t", "p"],
        [
          ["2023", "1.50 (0.60)", "2.06 (0.79)", "\u22120.79", "\u221213.79", "<.0001***"],
          ["2020", "1.45 (0.51)", "2.08 (0.66)", "\u22121.08", "\u221218.78", "<.0001***"],
        ],
        [1000, 1800, 1800, 1400, 1400, 1960]
      ),
      p(""),

      p("Russians report substantially weaker superordinate identification than Estonians in both years. The effect is very large (d > 0.79) and highly significant. The gap was somewhat larger in 2020 (d = \u22121.08) than in 2023 (d = \u22120.79), suggesting a modest narrowing over time."),

      heading("4.2 Within-Group Change: 2020 \u2192 2023", HeadingLevel.HEADING_2),

      makeTable(
        ["Group", "2020 M (SD)", "2023 M (SD)", "Cohen\u2019s d", "t", "p"],
        [
          ["Estonian", "1.45 (0.51)", "1.50 (0.60)", "+0.10", "1.89", ".059 ns"],
          ["Russian", "2.08 (0.66)", "2.05 (0.79)", "\u22120.04", "\u22120.64", ".524 ns"],
        ],
        [1200, 1800, 1800, 1400, 1200, 1960]
      ),
      p(""),

      p("Neither group showed a statistically significant change in superordinate identification from 2020 to 2023. Estonian identification showed a marginal trend toward weakening (d = +0.10, p = .059) but did not reach significance. Russian identification remained entirely stable (d = \u22120.04, p = .524). The modest narrowing of the between-group gap is driven by a small (non-significant) Estonian shift away from strong identification."),

      // 5. SENSITIVITY ANALYSIS
      heading("5. Sensitivity Analysis", HeadingLevel.HEADING_1),
      p("Given the borderline reliability of the composite (particularly in 2020), a sensitivity analysis was conducted using the single best item\u2014Q67_5 / K6X5_4 (\u201CYou feel part of Estonian society\u201D)\u2014as a robustness check. All four comparisons were re-run substituting the single item for the composite."),

      heading("5.1 Results", HeadingLevel.HEADING_2),

      makeTable(
        ["Comparison", "Composite d", "Composite p", "Single-item d", "Single-item p", "Match"],
        [
          ["Est vs Rus 2023", "\u22120.79", "<.0001***", "\u22120.67", "<.0001***", "YES"],
          ["Est vs Rus 2020", "\u22121.08", "<.0001***", "\u22120.79", "<.0001***", "YES"],
          ["Est 2020\u21922023", "+0.10", ".059 ns", "+0.07", ".18 ns", "YES"],
          ["Rus 2020\u21922023", "\u22120.04", ".524 ns", "\u22120.08", ".205 ns", "YES"],
        ],
        [1800, 1400, 1500, 1500, 1500, 1060]
      ),
      p(""),

      p("All four comparisons match in direction, significance, and substantive interpretation. Both within-group changes are non-significant in the composite and single-item versions alike. The single-item effect sizes are systematically smaller than the composite for between-group comparisons, which is expected\u2014the composite captures more of the underlying construct. Critically, no substantive conclusion changes when the composite is replaced by the single item."),

      heading("5.2 Interpretation", HeadingLevel.HEADING_2),
      p("The sensitivity analysis confirms that the 3-item composite is not producing misleading results, even where reliability is below conventional thresholds (2020 data). The composite can be used with confidence for group comparisons, with the understanding that true effect sizes may be slightly larger than observed due to measurement attenuation."),

      // 6. SUMMARY
      heading("6. Summary of Findings", HeadingLevel.HEADING_1),

      bp([{ text: "1. ", bold: true },
          { text: "Russians report substantially weaker superordinate identification than Estonians in both 2020 and 2023, with very large effect sizes (d = 0.79\u20131.08)." }]),

      bp([{ text: "2. ", bold: true },
          { text: "Neither group showed a statistically significant change from 2020 to 2023. Estonian identification showed a marginal trend (d = +0.10, p = .059) while Russian identification remained stable (d = \u22120.04, p = .524)." }]),

      bp([{ text: "3. ", bold: true },
          { text: "The between-group gap narrowed modestly from d = 1.08 (2020) to d = 0.79 (2023), driven by a small (non-significant) Estonian shift away from strong identification." }]),

      bp([{ text: "4. ", bold: true },
          { text: "The composite is unidimensional across all groups and years (Kaiser criterion retains 1 component). Reliability is good for 2023 (\u03B1 = .70\u2013.76) and borderline for 2020 (\u03B1 \u2248 .61), with the latter partly a mechanical artifact of the 3-item constraint." }]),

      bp([{ text: "5. ", bold: true },
          { text: "A sensitivity analysis using the single best item (Q67_5 \u201CYou feel part of Estonian society\u201D) confirmed that all substantive conclusions hold, supporting the validity of the composite for group-level comparisons." }]),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/Users/brianwiggins/Desktop/Claude Code/EIM2/Superordinate_Identity_Patterns_Analysis.docx", buffer);
  console.log("Document created successfully.");
});
