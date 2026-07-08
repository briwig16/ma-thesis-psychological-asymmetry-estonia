const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageOrientation } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "AAAAAA" };
const borders = { top: border, bottom: border, left: border, right: border };
const cellMargins = { top: 50, bottom: 50, left: 80, right: 80 };

// Landscape: content width = 15840 - 2*1440 = 12960
const TABLE_WIDTH = 12960;

function hCell(text, width) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: { fill: "2E4057", type: ShadingType.CLEAR },
    margins: cellMargins, verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, bold: true, font: "Arial", size: 18, color: "FFFFFF" })
    ]})]
  });
}

function dCell(text, width, shade = null) {
  const opts = {
    borders, width: { size: width, type: WidthType.DXA },
    margins: cellMargins, verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text, font: "Arial", size: 18 })
    ]})]
  };
  if (shade) opts.shading = { fill: shade, type: ShadingType.CLEAR };
  return opts;
}

function lCell(text, width, bold = false, shade = null) {
  const opts = {
    borders, width: { size: width, type: WidthType.DXA },
    margins: cellMargins, verticalAlign: "center",
    children: [new Paragraph({ alignment: AlignmentType.LEFT, children: [
      new TextRun({ text, bold, font: "Arial", size: 18 })
    ]})]
  };
  if (shade) opts.shading = { fill: shade, type: ShadingType.CLEAR };
  return opts;
}

// Column widths: Variable, Year, Group, N, Items, KMO, Bartlett, EV1, Var%, Kaiser, Alpha, Loadings
const cw = [2600, 600, 1000, 700, 700, 800, 1000, 800, 800, 800, 800, 1000, 1360];
// That's 13 columns = 12960 total

const headers = ["Variable", "Year", "Group", "N", "Items", "KMO", "Bartlett p", "EV\u2081", "Var %", "Kaiser", "\u03B1", "Loadings", "Assessment"];

const data = [
  // Superordinate Identity
  { v: "Superordinate Identity", y: "2023", g: "Estonian", n: "807", k: "3", kmo: ".629", bart: "<.0001", ev: "1.893", var: "63.1%", kai: "1", a: ".698", load: ".70\u2013.86", assess: "Borderline", shade: null },
  { v: "Superordinate Identity", y: "2023", g: "Russian", n: "423", k: "3", kmo: ".658", bart: "<.0001", ev: "2.052", var: "68.4%", kai: "1", a: ".760", load: ".78\u2013.88", assess: "Good", shade: null },
  { v: "Superordinate Identity", y: "2020", g: "Estonian", n: "663", k: "3", kmo: ".611", bart: "<.0001", ev: "1.710", var: "57.0%", kai: "1", a: ".591", load: ".67\u2013.82", assess: "Weak", shade: "FFF3CD" },
  { v: "Superordinate Identity", y: "2020", g: "Russian", n: "575", k: "3", kmo: ".595", bart: "<.0001", ev: "1.791", var: "59.7%", kai: "1", a: ".642", load: ".70\u2013.86", assess: "Weak", shade: "FFF3CD" },

  // SD Primary
  { v: "SD: Primary Out-group", y: "2023", g: "Estonian", n: "699", k: "3", kmo: ".701", bart: "<.0001", ev: "2.232", var: "74.4%", kai: "1", a: ".827", load: ".81\u2013.89", assess: "Good", shade: null },
  { v: "SD: Primary Out-group", y: "2023", g: "Russian", n: "436", k: "3", kmo: ".698", bart: "<.0001", ev: "2.061", var: "68.7%", kai: "1", a: ".772", load: ".82\u2013.85", assess: "Acceptable", shade: null },
  { v: "SD: Primary Out-group", y: "2020", g: "Estonian", n: "626", k: "3", kmo: ".674", bart: "<.0001", ev: "2.113", var: "70.4%", kai: "1", a: ".790", load: ".77\u2013.88", assess: "Acceptable", shade: null },
  { v: "SD: Primary Out-group", y: "2020", g: "Russian", n: "639", k: "3", kmo: ".708", bart: "<.0001", ev: "2.271", var: "75.7%", kai: "1", a: ".839", load: ".83\u2013.89", assess: "Good", shade: null },

  // SD General
  { v: "SD: General Out-group", y: "2023", g: "Estonian", n: "668", k: "6", kmo: ".717", bart: "<.0001", ev: "4.160", var: "69.3%", kai: "1", a: ".911", load: ".78\u2013.89", assess: "Excellent", shade: null },
  { v: "SD: General Out-group", y: "2023", g: "Russian", n: "397", k: "6", kmo: ".749", bart: "<.0001", ev: "4.045", var: "67.4%", kai: "1", a: ".902", load: ".78\u2013.85", assess: "Excellent", shade: null },
  { v: "SD: General Out-group", y: "2020", g: "Estonian", n: "543", k: "3", kmo: ".721", bart: "<.0001", ev: "2.372", var: "79.1%", kai: "1", a: ".866", load: ".85\u2013.91", assess: "Good", shade: null },
  { v: "SD: General Out-group", y: "2020", g: "Russian", n: "555", k: "3", kmo: ".718", bart: "<.0001", ev: "2.411", var: "80.4%", kai: "1", a: ".876", load: ".86\u2013.92", assess: "Good", shade: null },

  // Comparative Opp Assessment
  { v: "Comparative Opp. Assessment", y: "2023", g: "Estonian", n: "528", k: "12", kmo: ".928", bart: "<.0001", ev: "5.892", var: "49.1%", kai: "2", a: ".901", load: ".60\u2013.74", assess: "Excellent", shade: null },
  { v: "Comparative Opp. Assessment", y: "2023", g: "Russian", n: "317", k: "12", kmo: ".913", bart: "<.0001", ev: "5.755", var: "48.0%", kai: "2", a: ".900", load: ".54\u2013.77", assess: "Excellent", shade: null },
  { v: "Comparative Opp. Assessment", y: "2020", g: "Estonian", n: "474", k: "12", kmo: ".913", bart: "<.0001", ev: "5.309", var: "44.2%", kai: "1", a: ".883", load: ".58\u2013.77", assess: "Good", shade: null },
  { v: "Comparative Opp. Assessment", y: "2020", g: "Russian", n: "480", k: "12", kmo: ".921", bart: "<.0001", ev: "6.080", var: "50.7%", kai: "2", a: ".910", load: ".63\u2013.80", assess: "Excellent", shade: null },

  // Belief in Inevitable Conflict
  { v: "Belief in Inevitable Conflict", y: "2023", g: "Estonian", n: "732", k: "4", kmo: ".741", bart: "<.0001", ev: "2.358", var: "59.0%", kai: "1", a: ".766", load: ".70\u2013.80", assess: "Acceptable", shade: null },
  { v: "Belief in Inevitable Conflict", y: "2023", g: "Russian", n: "405", k: "4", kmo: ".694", bart: "<.0001", ev: "2.062", var: "51.6%", kai: "1", a: ".681", load: ".70\u2013.74", assess: "Borderline", shade: null },
  { v: "Belief in Inevitable Conflict", y: "2020", g: "Estonian", n: "575", k: "4", kmo: ".646", bart: "<.0001", ev: "1.982", var: "49.5%", kai: "1", a: ".654", load: ".63\u2013.78", assess: "Weak", shade: "FFF3CD" },
  { v: "Belief in Inevitable Conflict", y: "2020", g: "Russian", n: "561", k: "4", kmo: ".611", bart: "<.0001", ev: "1.968", var: "49.2%", kai: "2", a: ".648", load: ".58\u2013.75", assess: "Weak", shade: "FFF3CD" },

  // Minority Support Inclusion
  { v: "Minority Support Inclusion", y: "2023", g: "Estonian", n: "715", k: "3", kmo: ".720", bart: "<.0001", ev: "2.256", var: "75.2%", kai: "1", a: ".835", load: ".85\u2013.89", assess: "Good", shade: null },
  { v: "Minority Support Inclusion", y: "2023", g: "Russian", n: "425", k: "3", kmo: ".685", bart: "<.0001", ev: "2.266", var: "75.5%", kai: "1", a: ".835", load: ".81\u2013.91", assess: "Good", shade: null },
  { v: "Minority Support Inclusion", y: "2020", g: "Estonian", n: "577", k: "3", kmo: ".708", bart: "<.0001", ev: "2.141", var: "71.4%", kai: "1", a: ".798", load: ".83\u2013.86", assess: "Acceptable", shade: null },
  { v: "Minority Support Inclusion", y: "2020", g: "Russian", n: "619", k: "3", kmo: ".660", bart: "<.0001", ev: "2.260", var: "75.3%", kai: "1", a: ".833", load: ".77\u2013.92", assess: "Good", shade: null },
];

const tableRows = [
  new TableRow({ children: headers.map((h, i) => hCell(h, cw[i])) }),
  ...data.map(r => new TableRow({ children: [
    new TableCell(lCell(r.v, cw[0], false, r.shade)),
    new TableCell(dCell(r.y, cw[1], r.shade)),
    new TableCell(dCell(r.g, cw[2], r.shade)),
    new TableCell(dCell(r.n, cw[3], r.shade)),
    new TableCell(dCell(r.k, cw[4], r.shade)),
    new TableCell(dCell(r.kmo, cw[5], r.shade)),
    new TableCell(dCell(r.bart, cw[6], r.shade)),
    new TableCell(dCell(r.ev, cw[7], r.shade)),
    new TableCell(dCell(r.var, cw[8], r.shade)),
    new TableCell(dCell(r.kai, cw[9], r.shade)),
    new TableCell(dCell(r.a, cw[10], r.shade)),
    new TableCell(dCell(r.load, cw[11], r.shade)),
    new TableCell(dCell(r.assess, cw[12], r.shade)),
  ]}))
];

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 20 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840, orientation: PageOrientation.LANDSCAPE },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
        children: [new TextRun({ text: "Master Composite Variable Summary", font: "Arial", size: 32, bold: true })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 100 },
        children: [new TextRun({ text: "PCA and Reliability Statistics \u2014 EIM 2020 & 2023", font: "Arial", size: 24, color: "555555" })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
        children: [new TextRun({ text: "Highlighted rows indicate composites with weak reliability (\u03B1 < .70)", font: "Arial", size: 20, italics: true, color: "888888" })] }),

      new Table({
        width: { size: TABLE_WIDTH, type: WidthType.DXA },
        columnWidths: cw,
        rows: tableRows
      }),

      new Paragraph({ spacing: { before: 300, after: 100 },
        children: [new TextRun({ text: "Notes:", font: "Arial", size: 20, bold: true })] }),
      new Paragraph({ spacing: { after: 80 },
        children: [new TextRun({ text: "EV\u2081 = first eigenvalue from PCA. Var % = variance explained by first component. Kaiser = number of components with eigenvalue \u2265 1. \u03B1 = Cronbach\u2019s alpha. Loadings = range of absolute factor loadings on PC1. All Bartlett tests significant at p < .0001.", font: "Arial", size: 18 })] }),
      new Paragraph({ spacing: { after: 80 },
        children: [new TextRun({ text: "Assessment thresholds: Excellent (\u03B1 \u2265 .90), Good (\u03B1 \u2265 .80), Acceptable (\u03B1 \u2265 .70), Borderline (.65\u2013.70), Weak (\u03B1 < .65).", font: "Arial", size: 18 })] }),
      new Paragraph({ spacing: { after: 80 },
        children: [new TextRun({ text: "SD: General Out-group uses 6 items (no Ukrainian refugees) in 2023 and 3 items (new immigrants) in 2020.", font: "Arial", size: 18 })] }),
      new Paragraph({ spacing: { after: 80 },
        children: [new TextRun({ text: "Comparative Opp. Assessment shows Kaiser = 2 for some groups, but a single-factor solution is retained based on theoretical coherence and high alpha.", font: "Arial", size: 18 })] }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/Users/brianwiggins/Desktop/Claude Code/EIM2/Master_Composite_Summary.docx", buffer);
  console.log("Document created successfully.");
});
