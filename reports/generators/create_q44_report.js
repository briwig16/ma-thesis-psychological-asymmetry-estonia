const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
        PageNumber, Header, Footer } = require('docx');
const fs = require('fs');

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const headerBorder = { style: BorderStyle.SINGLE, size: 1, color: "1F3864" };
const headerBorders = { top: headerBorder, bottom: headerBorder, left: headerBorder, right: headerBorder };

const cm = (n) => n * 567;

function hdrCell(text, width) {
  return new TableCell({
    borders: headerBorders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: "1F3864", type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text, bold: true, color: "FFFFFF", font: "Arial", size: 20 })]
    })]
  });
}

function cell(text, width, shade = "FFFFFF", align = AlignmentType.LEFT, bold = false, color = "000000") {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: shade, type: ShadingType.CLEAR },
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, font: "Arial", size: 20, bold, color })]
    })]
  });
}

function sigColor(sig) {
  if (sig === "***") return "1F3864";
  if (sig === "**") return "2E5F9E";
  if (sig === "*") return "4472C4";
  return "666666";
}

function spacer() {
  return new Paragraph({ children: [new TextRun({ text: "", size: 20 })] });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: "Arial", size: 32, bold: true, color: "1F3864" })]
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, font: "Arial", size: 26, bold: true, color: "2E5F9E" })]
  });
}

function bodyText(text) {
  return new Paragraph({
    children: [new TextRun({ text, font: "Arial", size: 22 })],
    spacing: { after: 120 }
  });
}

function bodyBold(label, rest) {
  return new Paragraph({
    children: [
      new TextRun({ text: label, font: "Arial", size: 22, bold: true }),
      new TextRun({ text: rest, font: "Arial", size: 22 })
    ],
    spacing: { after: 100 }
  });
}

// ============================================================
//  ITEM DATA
// ============================================================
const items = [
  { domain: "Material well-being",        estM: "2.59", estSD: "0.92", rusM: "1.79", rusSD: "0.85", d: "+0.90", sig: "***" },
  { domain: "Social/political participation", estM: "2.33", estSD: "0.85", rusM: "1.61", rusSD: "0.79", d: "+0.88", sig: "***" },
  { domain: "Career/jobs",                estM: "2.47", estSD: "0.80", rusM: "1.89", rusSD: "0.84", d: "+0.70", sig: "***" },
  { domain: "Education",                  estM: "2.44", estSD: "0.86", rusM: "1.92", rusSD: "0.88", d: "+0.60", sig: "***" },
  { domain: "State benefits/services",    estM: "2.98", estSD: "0.77", rusM: "2.55", rusSD: "0.82", d: "+0.54", sig: "***" },
  { domain: "Children/youth",             estM: "2.73", estSD: "0.63", rusM: "2.36", rusSD: "0.81", d: "+0.50", sig: "***" },
  { domain: "Entrepreneurship",           estM: "2.73", estSD: "0.66", rusM: "2.38", rusSD: "0.80", d: "+0.48", sig: "***" },
  { domain: "Cultural participation",     estM: "2.53", estSD: "0.80", rusM: "2.18", rusSD: "0.89", d: "+0.41", sig: "***" },
  { domain: "Leisure/holidays",           estM: "2.93", estSD: "0.48", rusM: "2.76", rusSD: "0.60", d: "+0.32", sig: "***" },
  { domain: "Sports/exercise",            estM: "2.97", estSD: "0.37", rusM: "2.89", rusSD: "0.40", d: "+0.20", sig: "***" },
  { domain: "Medical care",               estM: "2.86", estSD: "0.65", rusM: "2.77", rusSD: "0.57", d: "+0.14", sig: "*"   },
  { domain: "Housing",                    estM: "2.74", estSD: "0.77", rusM: "2.77", rusSD: "0.58", d: "-0.05", sig: "ns"  },
];

const colWidths = [2600, 1500, 1500, 1500, 1500, 900, 760];
const totalWidth = colWidths.reduce((a, b) => a + b, 0); // 10260

const itemRows = items.map((r, i) => {
  const shade = i % 2 === 0 ? "F5F8FF" : "FFFFFF";
  const isSig = r.sig !== "ns";
  return new TableRow({
    children: [
      cell(r.domain,          colWidths[0], shade),
      cell(r.estM,            colWidths[1], shade, AlignmentType.CENTER),
      cell(`(${r.estSD})`,    colWidths[2], shade, AlignmentType.CENTER),
      cell(r.rusM,            colWidths[3], shade, AlignmentType.CENTER),
      cell(`(${r.rusSD})`,    colWidths[4], shade, AlignmentType.CENTER),
      cell(r.d,               colWidths[5], shade, AlignmentType.CENTER, isSig, isSig ? sigColor(r.sig) : "666666"),
      cell(r.sig,             colWidths[6], shade, AlignmentType.CENTER, true,  sigColor(r.sig)),
    ]
  });
});

// ============================================================
//  BUILD DOCUMENT
// ============================================================
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1F3864" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E5F9E" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
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
      default: new Header({ children: [
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "1F3864", space: 1 } },
          children: [new TextRun({ text: "EIM2 — Comparative Opportunity Assessment Analysis", font: "Arial", size: 18, color: "1F3864" })]
        })
      ]})
    },
    footers: {
      default: new Footer({ children: [
        new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 6, color: "1F3864", space: 1 } },
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({ text: "Page ", font: "Arial", size: 18, color: "666666" }),
            new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "666666" }),
          ]
        })
      ]})
    },
    children: [
      // TITLE
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [new TextRun({ text: "Comparative Opportunity Assessment", font: "Arial", size: 40, bold: true, color: "1F3864" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [new TextRun({ text: "Estonian vs Russian Respondents — EIM 2023", font: "Arial", size: 26, color: "2E5F9E" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: "1F3864", space: 4 } },
        spacing: { after: 280 },
        children: [new TextRun({ text: "Q44 Battery Analysis", font: "Arial", size: 22, italics: true, color: "666666" })]
      }),

      // OVERVIEW
      heading1("1. Overview"),
      bodyBold("Variable: ", "Comparative Opportunity Assessment (Q44)"),
      bodyBold("Items: ", "Q44_1 through Q44_12 (12 domains), averaged to form composite"),
      bodyBold("Scale: ", "1 = Very good \u2192 4 = Very bad (lower score = situation perceived as more favorable for Estonians)"),
      bodyBold("Question wording: ", "\"How would you rate the opportunities and situation of Estonians and people of other nationalities living in Estonia in the following areas?\""),
      spacer(),
      bodyText("Both Estonian and Russian respondents are rating the same objective situation \u2014 the relative opportunity landscape for Estonians vs other nationalities in Estonia. A lower score means the respondent perceives the situation as more favorable for Estonians; a higher score means they see fewer advantages for Estonians relative to other groups."),

      spacer(),

      // COMPOSITE
      heading1("2. Overall Composite"),

      new Table({
        width: { size: 7200, type: WidthType.DXA },
        columnWidths: [2400, 1600, 1600, 1600],
        rows: [
          new TableRow({ children: [
            hdrCell("Group",        2400),
            hdrCell("N",            1600),
            hdrCell("M (SD)",       1600),
            hdrCell("Cohen\u2019s d", 1600),
          ]}),
          new TableRow({ children: [
            cell("Estonian respondents", 2400, "F0F4FF"),
            cell("844", 1600, "F0F4FF", AlignmentType.CENTER),
            cell("2.71 (0.52)", 1600, "F0F4FF", AlignmentType.CENTER),
            cell("+0.74***", 1600, "F0F4FF", AlignmentType.CENTER, true, "1F3864"),
          ]}),
          new TableRow({ children: [
            cell("Russian respondents", 2400, "FFFFFF"),
            cell("518", 1600, "FFFFFF", AlignmentType.CENTER),
            cell("2.32 (0.53)", 1600, "FFFFFF", AlignmentType.CENTER),
            cell("", 1600, "FFFFFF"),
          ]}),
        ]
      }),
      spacer(),
      bodyText("Russians rate the opportunity situation as significantly more favorable for Estonians than Estonians rate it themselves \u2014 a large effect (d = +0.74, p < .0001, Welch t-test and Mann-Whitney U both significant)."),

      spacer(),

      // ITEM TABLE
      heading1("3. Item-by-Item Comparison"),
      bodyText("Ranked by magnitude of perceived Estonian advantage (largest gap first). Positive d = Estonians perceived as having better opportunities by Russian respondents relative to Estonian respondents\u2019 own assessment."),
      spacer(),

      new Table({
        width: { size: totalWidth, type: WidthType.DXA },
        columnWidths: colWidths,
        rows: [
          new TableRow({ children: [
            hdrCell("Domain",                   colWidths[0]),
            hdrCell("Est M",                    colWidths[1]),
            hdrCell("Est (SD)",                 colWidths[2]),
            hdrCell("Rus M",                    colWidths[3]),
            hdrCell("Rus (SD)",                 colWidths[4]),
            hdrCell("d",                        colWidths[5]),
            hdrCell("Sig",                      colWidths[6]),
          ]}),
          ...itemRows
        ]
      }),
      spacer(),
      bodyText("Sig: *** p < .001, ** p < .01, * p < .05, ns = not significant"),

      spacer(),

      // INTERPRETATION
      heading1("4. Interpretation"),

      heading2("4.1 The Core Finding"),
      bodyText("Russian-speakers perceive a clear Estonian structural advantage across nearly every life domain. Their scores are consistently lower (more positive for Estonians) indicating they see Estonian-speakers as having meaningfully better opportunities in material well-being, social/political life, careers, education, and access to state services. Estonians, rating the same situation, are considerably more skeptical of their own group\u2019s advantages \u2014 perceiving things as more middling rather than clearly favorable."),

      heading2("4.2 Where the Gaps Are Largest"),
      bodyBold("Material well-being (d = +0.90) and Social/political participation (d = +0.88): ",
        "The two largest gaps are in domains most directly tied to language, citizenship status, and access to political power. Russian-speakers, who face formal and informal barriers in these areas (language requirements for civil service, historical citizenship restrictions, political underrepresentation), perceive Estonian dominance most acutely here."),
      bodyBold("Career/jobs (d = +0.70) and Education (d = +0.60): ",
        "Both domains where language policy creates tangible structural advantages for Estonian-speakers, confirming that perceived gaps track real institutional inequalities."),

      heading2("4.3 The Exception \u2014 Housing"),
      bodyText("Housing is the only domain with no significant difference (d = \u22120.05, ns). Both groups rate it similarly (~2.74\u20132.77). The housing market is least shaped by ethnicity or language policy, supporting the interpretation that gaps elsewhere genuinely reflect perceived ethnic structural advantage rather than general pessimism about Estonian society."),

      heading2("4.4 Why Estonians Rate Their Own Situation Less Favorably"),
      bodyText("Estonians\u2019 higher scores (more critical self-assessment) likely reflect a combination of: (1) higher baseline expectations as the majority group \u2014 comparing against an ideal rather than against minority conditions; (2) genuine dissatisfaction with aspects of Estonian society; and (3) less salient awareness of relative advantage, since privilege is typically less visible to those who hold it."),

      heading2("4.5 Implications"),
      bodyText("The finding that Russian-speakers perceive Estonians as holding substantial structural advantages \u2014 especially in political participation, material well-being, and careers \u2014 has direct implications for integration research. Perceptions of ethnic inequality are a well-documented driver of inter-group tension and reduced superordinate identity. Cross-referencing this composite with the Social Distance and Belief in Inevitable Conflict variables would test whether perceived opportunity inequality predicts more negative inter-group attitudes."),

      spacer(),

      // NOTE
      new Paragraph({
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: "4472C4", space: 8 } },
        indent: { left: 360 },
        spacing: { after: 100 },
        children: [new TextRun({ text: "Note on cross-year comparisons: ", font: "Arial", size: 20, bold: true, color: "1F3864" })]
      }),
      new Paragraph({
        border: { left: { style: BorderStyle.SINGLE, size: 12, color: "4472C4", space: 8 } },
        indent: { left: 360 },
        spacing: { after: 200 },
        children: [new TextRun({ text: "Both groups showed a significant increase in perceived Estonian advantage from 2020 to 2023 (Estonians: d = +0.30***, Russians: d = +0.34***). The gap between the two groups\u2019 assessments narrowed slightly (d = +0.79 in 2020 vs +0.74 in 2023), but remained large and significant in both years.", font: "Arial", size: 20, color: "333333" })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("/Users/brianwiggins/Desktop/Claude Code/EIM2/Comparative_Opportunity_Assessment.docx", buf);
  console.log("Done: Comparative_Opportunity_Assessment.docx");
});
