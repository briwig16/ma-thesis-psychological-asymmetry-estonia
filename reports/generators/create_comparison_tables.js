const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageOrientation, PageBreak } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const borders = { top: border, bottom: border, left: border, right: border };
const cm = { top: 50, bottom: 50, left: 80, right: 80 };
const TABLE_WIDTH = 12960;

function hCell(text, w) {
  return new TableCell({ borders, width: { size: w, type: WidthType.DXA },
    shading: { fill: "2E4057", type: ShadingType.CLEAR }, margins: cm, verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, bold: true, font: "Arial", size: 18, color: "FFFFFF" }) ]})] });
}
function dC(text, w, shade) {
  const o = { borders, width: { size: w, type: WidthType.DXA }, margins: cm, verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, font: "Arial", size: 18 }) ]})] };
  if (shade) o.shading = { fill: shade, type: ShadingType.CLEAR };
  return new TableCell(o);
}
function lC(text, w, shade) {
  const o = { borders, width: { size: w, type: WidthType.DXA }, margins: cm, verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.LEFT, children: [
      new TextRun({ text, font: "Arial", size: 18 }) ]})] };
  if (shade) o.shading = { fill: shade, type: ShadingType.CLEAR };
  return new TableCell(o);
}

// Table 1 columns: Variable, Year, Est N, Est M(SD), Rus N, Rus M(SD), t, p, d, Sig
const cw1 = [2600, 600, 700, 1500, 700, 1500, 1100, 1100, 1100, 700]; // removed extra, fits in 11600
// Adjust to fill 12960
const cw1f = [2800, 600, 700, 1600, 700, 1600, 1200, 1200, 1100, 760]; // sum = 12260... let me calc
// 2800+600+700+1600+700+1600+1200+1200+1100+760 = 12260. Need 12960. Add 700 spread.
const t1cw = [2900, 650, 750, 1600, 750, 1600, 1200, 1200, 1100, 1210];

const t1data = [
  // Superordinate Identity
  { v: "Superordinate Identity", y: "2020", en: "697", em: "1.43 (0.49)", rn: "692", rm: "2.07 (0.67)", t: "\u221220.38", p: "<.0001", d: "\u22121.09", sig: "***", s: null },
  { v: "Superordinate Identity", y: "2023", en: "865", em: "1.50 (0.60)", rn: "517", rm: "2.05 (0.79)", t: "\u221213.79", p: "<.0001", d: "\u22120.79", sig: "***", s: null },
  // SD Primary
  { v: "SD: Primary Out-group", y: "2020", en: "694", em: "2.50 (0.89)", rn: "699", rm: "1.87 (0.79)", t: "13.90", p: "<.0001", d: "+0.75", sig: "***", s: "FFF3CD" },
  { v: "SD: Primary Out-group", y: "2023", en: "810", em: "2.91 (1.04)", rn: "477", rm: "1.83 (0.77)", t: "21.30", p: "<.0001", d: "+1.18", sig: "***", s: "FFF3CD" },
  // SD General
  { v: "SD: General Out-group", y: "2020", en: "675", em: "2.91 (1.01)", rn: "667", rm: "3.10 (1.02)", t: "\u22123.40", p: ".0007", d: "\u22120.19", sig: "***", s: null },
  { v: "SD: General Out-group", y: "2023", en: "855", em: "2.70 (0.90)", rn: "516", rm: "2.60 (0.81)", t: "1.97", p: ".049", d: "+0.11", sig: "*", s: null },
  // Comparative Opp
  { v: "Comparative Opp. Assessment", y: "2020", en: "675", em: "2.57 (0.48)", rn: "692", rm: "2.14 (0.57)", t: "15.33", p: "<.0001", d: "+0.83", sig: "***", s: null },
  { v: "Comparative Opp. Assessment", y: "2023", en: "844", em: "2.71 (0.52)", rn: "518", rm: "2.32 (0.53)", t: "13.13", p: "<.0001", d: "+0.74", sig: "***", s: null },
  // Conflict
  { v: "Belief in Inevitable Conflict", y: "2020", en: "694", em: "2.77 (0.57)", rn: "688", rm: "3.03 (0.57)", t: "\u22128.49", p: "<.0001", d: "\u22120.46", sig: "***", s: null },
  { v: "Belief in Inevitable Conflict", y: "2023", en: "855", em: "2.72 (0.67)", rn: "507", rm: "3.21 (0.58)", t: "\u221214.21", p: "<.0001", d: "\u22120.78", sig: "***", s: "FFF3CD" },
  // Minority
  { v: "Minority Support Inclusion", y: "2020", en: "673", em: "2.21 (0.70)", rn: "668", rm: "1.58 (0.60)", t: "17.64", p: "<.0001", d: "+0.96", sig: "***", s: null },
  { v: "Minority Support Inclusion", y: "2023", en: "844", em: "2.33 (0.77)", rn: "505", rm: "1.54 (0.60)", t: "20.88", p: "<.0001", d: "+1.14", sig: "***", s: null },
];

// Table 2 columns: Variable, Group, 2020 N, 2020 M(SD), 2023 N, 2023 M(SD), t, p, d, Sig
const t2cw = [2900, 900, 750, 1600, 750, 1600, 1200, 1200, 1100, 960];

const t2data = [
  { v: "Superordinate Identity", g: "Estonian", n1: "697", m1: "1.43 (0.49)", n2: "865", m2: "1.50 (0.60)", t: "\u22122.49", p: ".013", d: "+0.13", sig: "*", s: null },
  { v: "Superordinate Identity", g: "Russian", n1: "692", m1: "2.07 (0.67)", n2: "517", m2: "2.05 (0.79)", t: "0.46", p: ".645", d: "\u22120.03", sig: "ns", s: null },
  { v: "SD: Primary Out-group", g: "Estonian", n1: "694", m1: "2.50 (0.89)", n2: "810", m2: "2.91 (1.04)", t: "\u22128.35", p: "<.0001", d: "+0.43", sig: "***", s: "FFF3CD" },
  { v: "SD: Primary Out-group", g: "Russian", n1: "699", m1: "1.87 (0.79)", n2: "477", m2: "1.83 (0.77)", t: "0.79", p: ".428", d: "\u22120.05", sig: "ns", s: null },
  { v: "SD: General Out-group", g: "Estonian", n1: "675", m1: "2.91 (1.01)", n2: "855", m2: "2.70 (0.90)", t: "4.29", p: "<.0001", d: "\u22120.22", sig: "***", s: null },
  { v: "SD: General Out-group", g: "Russian", n1: "667", m1: "3.10 (1.02)", n2: "516", m2: "2.60 (0.81)", t: "9.29", p: "<.0001", d: "\u22120.54", sig: "***", s: "D4EDDA" },
  { v: "Comparative Opp. Assessment", g: "Estonian", n1: "675", m1: "2.57 (0.48)", n2: "844", m2: "2.71 (0.52)", t: "\u22125.20", p: "<.0001", d: "+0.27", sig: "***", s: null },
  { v: "Comparative Opp. Assessment", g: "Russian", n1: "692", m1: "2.14 (0.57)", n2: "518", m2: "2.32 (0.53)", t: "\u22125.69", p: "<.0001", d: "+0.33", sig: "***", s: null },
  { v: "Belief in Inevitable Conflict", g: "Estonian", n1: "694", m1: "2.77 (0.57)", n2: "855", m2: "2.72 (0.67)", t: "1.60", p: ".111", d: "\u22120.08", sig: "ns", s: null },
  { v: "Belief in Inevitable Conflict", g: "Russian", n1: "688", m1: "3.03 (0.57)", n2: "507", m2: "3.21 (0.58)", t: "\u22125.35", p: "<.0001", d: "+0.31", sig: "***", s: "FFF3CD" },
  { v: "Minority Support Inclusion", g: "Estonian", n1: "673", m1: "2.21 (0.70)", n2: "844", m2: "2.33 (0.77)", t: "\u22123.05", p: ".002", d: "+0.16", sig: "**", s: null },
  { v: "Minority Support Inclusion", g: "Russian", n1: "668", m1: "1.58 (0.60)", n2: "505", m2: "1.54 (0.60)", t: "1.16", p: ".245", d: "\u22120.07", sig: "ns", s: null },
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "EIM Composite Variable Comparisons", font: "Arial", size: 18, italics: true, color: "888888" })]
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
      // TABLE 1
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
        children: [new TextRun({ text: "Table 1: Between-Group Comparisons (Estonian vs Russian)", font: "Arial", size: 28, bold: true })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 250 },
        children: [new TextRun({ text: "Welch\u2019s t-test with Cohen\u2019s d (pooled SD). Positive d = Estonians score higher.", font: "Arial", size: 18, italics: true, color: "666666" })] }),

      new Table({
        width: { size: TABLE_WIDTH, type: WidthType.DXA },
        columnWidths: t1cw,
        rows: [
          new TableRow({ children: [
            hCell("Variable", t1cw[0]), hCell("Year", t1cw[1]), hCell("Est N", t1cw[2]),
            hCell("Est M (SD)", t1cw[3]), hCell("Rus N", t1cw[4]), hCell("Rus M (SD)", t1cw[5]),
            hCell("t", t1cw[6]), hCell("p", t1cw[7]), hCell("d", t1cw[8]), hCell("Sig.", t1cw[9])
          ]}),
          ...t1data.map(r => new TableRow({ children: [
            lC(r.v, t1cw[0], r.s), dC(r.y, t1cw[1], r.s), dC(r.en, t1cw[2], r.s),
            dC(r.em, t1cw[3], r.s), dC(r.rn, t1cw[4], r.s), dC(r.rm, t1cw[5], r.s),
            dC(r.t, t1cw[6], r.s), dC(r.p, t1cw[7], r.s), dC(r.d, t1cw[8], r.s), dC(r.sig, t1cw[9], r.s)
          ]}))
        ]
      }),

      new Paragraph({ spacing: { before: 200, after: 80 },
        children: [new TextRun({ text: "Note: Yellow highlights indicate composites where the between-group gap widened substantially from 2020 to 2023. *** p < .001, ** p < .01, * p < .05, ns = not significant.", font: "Arial", size: 17, color: "666666" })] }),

      // PAGE BREAK
      new Paragraph({ children: [new PageBreak()] }),

      // TABLE 2
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
        children: [new TextRun({ text: "Table 2: Within-Group Change (2020 \u2192 2023)", font: "Arial", size: 28, bold: true })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 250 },
        children: [new TextRun({ text: "Welch\u2019s t-test with Cohen\u2019s d (pooled SD). Positive d = score increased from 2020 to 2023.", font: "Arial", size: 18, italics: true, color: "666666" })] }),

      new Table({
        width: { size: TABLE_WIDTH, type: WidthType.DXA },
        columnWidths: t2cw,
        rows: [
          new TableRow({ children: [
            hCell("Variable", t2cw[0]), hCell("Group", t2cw[1]), hCell("2020 N", t2cw[2]),
            hCell("2020 M (SD)", t2cw[3]), hCell("2023 N", t2cw[4]), hCell("2023 M (SD)", t2cw[5]),
            hCell("t", t2cw[6]), hCell("p", t2cw[7]), hCell("d", t2cw[8]), hCell("Sig.", t2cw[9])
          ]}),
          ...t2data.map(r => new TableRow({ children: [
            lC(r.v, t2cw[0], r.s), dC(r.g, t2cw[1], r.s), dC(r.n1, t2cw[2], r.s),
            dC(r.m1, t2cw[3], r.s), dC(r.n2, t2cw[4], r.s), dC(r.m2, t2cw[5], r.s),
            dC(r.t, t2cw[6], r.s), dC(r.p, t2cw[7], r.s), dC(r.d, t2cw[8], r.s), dC(r.sig, t2cw[9], r.s)
          ]}))
        ]
      }),

      new Paragraph({ spacing: { before: 200, after: 80 },
        children: [new TextRun({ text: "Note: Yellow = notable worsening; Green = notable improvement. *** p < .001, ** p < .01, * p < .05, ns = not significant.", font: "Arial", size: 17, color: "666666" })] }),
      new Paragraph({ spacing: { after: 80 },
        children: [new TextRun({ text: "SD: General Out-group uses 6 items in 2023 and 3 items in 2020; cross-year comparisons should be interpreted cautiously.", font: "Arial", size: 17, color: "666666" })] }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/Users/brianwiggins/Desktop/Claude Code/EIM2/Composite_Comparison_Tables.docx", buffer);
  console.log("Document created successfully.");
});
