const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
        ShadingType, PageNumber, PageBreak } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const margins = { top: 80, bottom: 80, left: 100, right: 100 };

function cell(text, opts = {}) {
    const { bold, shading, width, align } = opts;
    return new TableCell({
        borders, margins,
        width: width ? { size: width, type: WidthType.DXA } : undefined,
        shading: shading ? { fill: shading, type: ShadingType.CLEAR } : undefined,
        children: [new Paragraph({
            alignment: align || AlignmentType.LEFT,
            children: [new TextRun({ text: String(text), bold: !!bold, font: "Arial", size: 18 })]
        })]
    });
}

const colWidths = [2600, 600, 1000, 500, 550, 600, 600, 650, 700, 1060];
const tableWidth = colWidths.reduce((a,b) => a+b, 0);

const headerRow = ["Variable", "Year", "Group", "N", "Items", "KMO", "\u03B1", "Var%", "Loadings", "Assessment"];

const data = [
    ["Superordinate Identity", "2023", "Estonian", "807", "3", ".629", ".698", "63.1%", ".70\u2013.86", "Borderline"],
    ["Superordinate Identity", "2023", "Russian", "423", "3", ".658", ".760", "68.4%", ".78\u2013.88", "Good"],
    ["Superordinate Identity", "2020", "Estonian", "669", "3", ".619", ".614", "61.3%", ".45\u2013.79", "Weak"],
    ["Superordinate Identity", "2020", "Russian", "497", "3", ".585", ".618", "57.7%", ".45\u2013.94", "Weak"],
    ["SD: Primary Out-group", "2023", "Estonian", "699", "3", ".701", ".827", "74.4%", ".81\u2013.89", "Good"],
    ["SD: Primary Out-group", "2023", "Russian", "436", "3", ".698", ".772", "68.7%", ".82\u2013.85", "Acceptable"],
    ["SD: Primary Out-group", "2020", "Estonian", "600", "3", ".669", ".782", "70.3%", ".58\u2013.85", "Acceptable"],
    ["SD: Primary Out-group", "2020", "Russian", "529", "3", ".701", ".833", "75.2%", ".68\u2013.87", "Good"],
    ["SD: General Out-group", "2023", "Estonian", "668", "6", ".717", ".911", "69.3%", ".78\u2013.89", "Excellent"],
    ["SD: General Out-group", "2023", "Russian", "397", "6", ".749", ".902", "67.4%", ".78\u2013.85", "Excellent"],
    ["SD: General Out-group", "2020", "Estonian", "551", "3", ".719", ".865", "78.8%", ".73\u2013.88", "Good"],
    ["SD: General Out-group", "2020", "Russian", "471", "3", ".727", ".885", "81.3%", ".77\u2013.92", "Good"],
    ["Comp. Opp. Assessment", "2023", "Estonian", "528", "12", ".928", ".901", "49.1%", ".60\u2013.74", "Excellent"],
    ["Comp. Opp. Assessment", "2023", "Russian", "317", "12", ".913", ".900", "48.0%", ".54\u2013.77", "Excellent"],
    ["Comp. Opp. Assessment", "2020", "Estonian", "481", "12", ".920", ".893", "46.8%", ".56\u2013.76", "Good"],
    ["Comp. Opp. Assessment", "2020", "Russian", "413", "12", ".915", ".906", "49.6%", ".57\u2013.78", "Excellent"],
    ["Belief in Inev. Conflict", "2023", "Estonian", "732", "4", ".741", ".766", "59.0%", ".70\u2013.80", "Acceptable"],
    ["Belief in Inev. Conflict", "2023", "Russian", "405", "4", ".694", ".681", "51.6%", ".70\u2013.74", "Borderline"],
    ["Belief in Inev. Conflict", "2020", "Estonian", "577", "4", ".650", ".656", "50.3%", ".50\u2013.71", "Borderline"],
    ["Belief in Inev. Conflict", "2020", "Russian", "492", "4", ".617", ".647", "49.6%", ".42\u2013.65", "Weak"],
    ["Minority Support Incl.", "2023", "Estonian", "715", "3", ".720", ".835", "75.2%", ".85\u2013.89", "Good"],
    ["Minority Support Incl.", "2023", "Russian", "425", "3", ".685", ".835", "75.5%", ".81\u2013.91", "Good"],
    ["Minority Support Incl.", "2020", "Estonian", "580", "3", ".707", ".796", "71.3%", ".71\u2013.78", "Acceptable"],
    ["Minority Support Incl.", "2020", "Russian", "543", "3", ".654", ".828", "74.8%", ".57\u2013.90", "Good"],
    ["Contact w/ Estonian spkrs", "2023", "Estonian", "780", "6", ".749", ".760", "48.2%", ".48\u2013.85", "Acceptable"],
    ["Contact w/ Estonian spkrs", "2023", "Russian", "456", "6", ".827", ".812", "52.4%", ".53\u2013.83", "Good"],
    ["Contact w/ Estonian spkrs", "2020", "Estonian", "662", "6", ".802", ".816", "55.0%", ".53\u2013.82", "Good"],
    ["Contact w/ Estonian spkrs", "2020", "Russian", "557", "6", ".845", ".863", "60.2%", ".61\u2013.82", "Good"],
    ["Contact w/ Russian spkrs", "2023", "Estonian", "770", "6", ".867", ".854", "59.4%", ".63\u2013.87", "Good"],
    ["Contact w/ Russian spkrs", "2023", "Russian", "469", "6", ".737", ".737", "44.7%", ".60\u2013.75", "Acceptable"],
    ["Contact w/ Russian spkrs", "2020", "Estonian", "667", "6", ".875", ".852", "58.1%", ".57\u2013.82", "Good"],
    ["Contact w/ Russian spkrs", "2020", "Russian", "570", "6", ".760", ".773", "52.0%", ".46\u2013.77", "Acceptable"],
];

function assessColor(a) {
    if (a === "Excellent") return "C6EFCE";
    if (a === "Good") return "C6EFCE";
    if (a === "Acceptable") return "FFEB9C";
    if (a === "Borderline") return "FFC7CE";
    if (a === "Weak") return "FFC7CE";
    return undefined;
}

const tableRows = [
    new TableRow({
        children: headerRow.map((h, i) => cell(h, { bold: true, shading: "2E75B6", width: colWidths[i] }))
    }),
    ...data.map((row, ri) => new TableRow({
        children: row.map((val, ci) => {
            const bg = ci === 9 ? assessColor(val) : (ri % 2 === 0 ? "F2F2F2" : undefined);
            const bold = ci === 6;
            return cell(val, { bold, shading: bg, width: colWidths[ci], align: ci >= 3 ? AlignmentType.CENTER : AlignmentType.LEFT });
        })
    }))
];

const doc = new Document({
    styles: {
        default: { document: { run: { font: "Arial", size: 22 } } },
        paragraphStyles: [
            { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 32, bold: true, font: "Arial" }, paragraph: { spacing: { before: 240, after: 240 } } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 26, bold: true, font: "Arial" }, paragraph: { spacing: { before: 180, after: 120 } } },
        ]
    },
    sections: [{
        properties: {
            page: { size: { width: 15840, height: 12240, orientation: "landscape" },
                    margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 } }
        },
        children: [
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Master Composite Reliability Summary")] }),
            new Paragraph({ spacing: { after: 200 }, children: [
                new TextRun({ text: "All composites validated with PCA, KMO, Bartlett's test, Cronbach's \u03B1, and factor loading ranges. Thresholds: ", size: 20 }),
                new TextRun({ text: "Excellent (\u03B1 \u2265 .90), Good (\u03B1 \u2265 .80), Acceptable (\u03B1 \u2265 .70), Borderline (.65\u2013.70), Weak (\u03B1 < .65)", size: 20, italics: true }),
            ]}),
            new Table({ width: { size: tableWidth, type: WidthType.DXA }, columnWidths: colWidths, rows: tableRows }),
            new Paragraph({ spacing: { before: 200 }, children: [
                new TextRun({ text: "Note: ", bold: true, size: 18 }),
                new TextRun({ text: "Contact composites (Q51/Q52) show 2 Kaiser components for in-group contact across all groups and years. Work/school loads weakest, suggesting in-group contact splits into public/proximity and close/personal sub-dimensions. Single-factor composite retained (\u03B1 > .73) but should be acknowledged.", size: 18, italics: true }),
            ]}),
        ]
    }]
});

Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync("Master_Composite_Summary.docx", buffer);
    console.log("Master_Composite_Summary.docx created");
});
