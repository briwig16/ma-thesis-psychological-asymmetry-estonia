const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType, PageBreak } = require("docx");

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const margins = { top: 80, bottom: 80, left: 100, right: 100 };

function cell(text, opts = {}) {
    const { bold, shading, width, align, size } = opts;
    return new TableCell({
        borders, margins,
        width: width ? { size: width, type: WidthType.DXA } : undefined,
        shading: shading ? { fill: shading, type: ShadingType.CLEAR } : undefined,
        children: [new Paragraph({
            alignment: align || AlignmentType.LEFT,
            children: [new TextRun({ text: String(text), bold: !!bold, font: "Arial", size: size || 18 })]
        })]
    });
}

// TABLE 1: Between-group
const bCols = [2800, 600, 1300, 1300, 800, 1100, 600];
const bWidth = bCols.reduce((a,b)=>a+b,0);
const bHeader = ["Variable", "Year", "Est M (SD)", "Rus M (SD)", "d", "p", "Sig"];

const bData = [
    ["Superordinate Identity", "2020", "1.45 (0.51)", "2.08 (0.66)", "\u22121.08", "<.0001", "***"],
    ["Superordinate Identity", "2023", "1.50 (0.60)", "2.05 (0.79)", "\u22120.79", "<.0001", "***"],
    ["SD: Primary Out-group", "2020", "2.51 (0.88)", "1.90 (0.80)", "+0.74", "<.0001", "***"],
    ["SD: Primary Out-group", "2023", "2.91 (1.04)", "1.83 (0.77)", "+1.18", "<.0001", "***"],
    ["SD: General Out-group", "2020", "2.91 (1.01)", "3.12 (1.02)", "\u22120.21", ".0003", "***"],
    ["SD: General Out-group", "2023", "2.70 (0.90)", "2.60 (0.81)", "+0.11", ".049", "*"],
    ["Comp. Opp. Assessment", "2020", "2.56 (0.49)", "2.14 (0.56)", "+0.79", "<.0001", "***"],
    ["Comp. Opp. Assessment", "2023", "2.71 (0.52)", "2.32 (0.53)", "+0.74", "<.0001", "***"],
    ["Belief in Inev. Conflict", "2020", "2.78 (0.57)", "3.03 (0.58)", "\u22120.44", "<.0001", "***"],
    ["Belief in Inev. Conflict", "2023", "2.72 (0.67)", "3.21 (0.58)", "\u22120.78", "<.0001", "***"],
    ["Minority Support Incl.", "2020", "2.21 (0.70)", "1.57 (0.59)", "+1.00", "<.0001", "***"],
    ["Minority Support Incl.", "2023", "2.33 (0.77)", "1.54 (0.60)", "+1.14", "<.0001", "***"],
    ["Contact w/ Estonian spkrs", "2020", "1.85 (0.98)", "3.86 (1.14)", "\u22121.89", "<.0001", "***"],
    ["Contact w/ Estonian spkrs", "2023", "1.74 (0.86)", "3.29 (1.10)", "\u22121.57", "<.0001", "***"],
    ["Contact w/ Russian spkrs", "2020", "3.98 (1.06)", "1.79 (0.88)", "+2.25", "<.0001", "***"],
    ["Contact w/ Russian spkrs", "2023", "3.87 (1.10)", "1.71 (0.80)", "+2.25", "<.0001", "***"],
    ["Group ID Patterns", "2020", "2.95 (0.94)", "2.69 (0.81)", "+0.30", "<.0001", "***"],
    ["Group ID Patterns", "2023", "2.94 (0.95)", "2.81 (0.84)", "+0.15", ".009", "**"],
    ["Territorial Attachment", "2020", "1.24 (0.51)", "1.43 (0.59)", "\u22120.34", "<.0001", "***"],
    ["Territorial Attachment", "2023", "1.23 (0.51)", "1.27 (0.53)", "\u22120.09", ".116", "ns"],
];

// TABLE 2: Within-group change
const wCols = [2800, 900, 1300, 1300, 800, 1100, 600];
const wWidth = wCols.reduce((a,b)=>a+b,0);
const wHeader = ["Variable", "Group", "2020 M (SD)", "2023 M (SD)", "d", "p", "Sig"];

const wData = [
    ["Superordinate Identity", "Estonian", "1.45 (0.51)", "1.50 (0.60)", "+0.10", ".059", "ns"],
    ["Superordinate Identity", "Russian", "2.08 (0.66)", "2.05 (0.79)", "\u22120.04", ".524", "ns"],
    ["SD: Primary Out-group", "Estonian", "2.51 (0.88)", "2.91 (1.04)", "+0.42", "<.0001", "***"],
    ["SD: Primary Out-group", "Russian", "1.90 (0.80)", "1.83 (0.77)", "\u22120.08", ".205", "ns"],
    ["SD: General Out-group", "Estonian", "2.91 (1.01)", "2.70 (0.90)", "\u22120.23", "<.0001", "***"],
    ["SD: General Out-group", "Russian", "3.12 (1.02)", "2.60 (0.81)", "\u22120.56", "<.0001", "***"],
    ["Comp. Opp. Assessment", "Estonian", "2.56 (0.49)", "2.71 (0.52)", "+0.30", "<.0001", "***"],
    ["Comp. Opp. Assessment", "Russian", "2.14 (0.56)", "2.32 (0.53)", "+0.34", "<.0001", "***"],
    ["Belief in Inev. Conflict", "Estonian", "2.78 (0.57)", "2.72 (0.67)", "\u22120.09", ".077", "ns"],
    ["Belief in Inev. Conflict", "Russian", "3.03 (0.58)", "3.21 (0.58)", "+0.32", "<.0001", "***"],
    ["Minority Support Incl.", "Estonian", "2.21 (0.70)", "2.33 (0.77)", "+0.15", ".003", "**"],
    ["Minority Support Incl.", "Russian", "1.57 (0.59)", "1.54 (0.60)", "\u22120.04", ".490", "ns"],
    ["Contact w/ Estonian spkrs", "Estonian", "1.85 (0.98)", "1.74 (0.86)", "\u22120.12", ".016", "*"],
    ["Contact w/ Estonian spkrs", "Russian", "3.86 (1.14)", "3.29 (1.10)", "\u22120.51", "<.0001", "***"],
    ["Contact w/ Russian spkrs", "Estonian", "3.98 (1.06)", "3.87 (1.10)", "\u22120.10", ".042", "*"],
    ["Contact w/ Russian spkrs", "Russian", "1.79 (0.88)", "1.71 (0.80)", "\u22120.09", ".133", "ns"],
    ["Group ID Patterns", "Estonian", "2.95 (0.94)", "2.94 (0.95)", "\u22120.01", ".816", "ns"],
    ["Group ID Patterns", "Russian", "2.69 (0.81)", "2.81 (0.84)", "+0.14", ".022", "*"],
    ["Territorial Attachment", "Estonian", "1.24 (0.51)", "1.23 (0.51)", "\u22120.02", ".660", "ns"],
    ["Territorial Attachment", "Russian", "1.43 (0.59)", "1.27 (0.53)", "\u22120.27", "<.0001", "***"],
];

function makeTable(headers, data, colWidths, width) {
    return new Table({
        width: { size: width, type: WidthType.DXA },
        columnWidths: colWidths,
        rows: [
            new TableRow({ children: headers.map((h, i) => cell(h, { bold: true, shading: "2E75B6", width: colWidths[i], align: AlignmentType.CENTER })) }),
            ...data.map((row, ri) => new TableRow({
                children: row.map((val, ci) => {
                    const bg = ri % 4 < 2 ? "F2F2F2" : undefined;
                    const bold = ci === 6 && val === "***";
                    return cell(val, { bold, shading: bg, width: colWidths[ci], align: ci >= 2 ? AlignmentType.CENTER : AlignmentType.LEFT });
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
              run: { size: 32, bold: true, font: "Arial" }, paragraph: { spacing: { before: 240, after: 240 } } },
            { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
              run: { size: 26, bold: true, font: "Arial" }, paragraph: { spacing: { before: 180, after: 120 } } },
        ]
    },
    sections: [{
        properties: {
            page: { size: { width: 12240, height: 15840 }, margin: { top: 1200, right: 1200, bottom: 1200, left: 1200 } }
        },
        children: [
            new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Composite Variable Comparison Tables")] }),
            new Paragraph({ spacing: { after: 100 }, children: [new TextRun({ text: "EIM 2020 & 2023 \u2014 Estonian vs Russian Respondents", size: 22, italics: true })] }),
            new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: "All tests: Welch\u2019s t-test (unequal variances). Cohen\u2019s d = pooled SD method. * p < .05, ** p < .01, *** p < .001", size: 18 })] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Table 1: Between-Group Comparisons (Estonian vs Russian)")] }),
            makeTable(bHeader, bData, bCols, bWidth),

            new Paragraph({ spacing: { before: 200, after: 100 }, children: [
                new TextRun({ text: "Key patterns: ", bold: true, size: 18 }),
                new TextRun({ text: "All between-group differences significant in both years. Gaps widened for SD Primary (+0.74\u2192+1.18), Belief in Conflict (\u22120.44\u2192\u22120.78), Minority Support (+1.00\u2192+1.14). Gaps narrowed for Superordinate Identity (\u22121.08\u2192\u22120.79), Comparative Opp. (+0.79\u2192+0.74), Contact w/ Estonian spkrs (\u22121.89\u2192\u22121.57). Gap flipped direction for SD General (\u22120.21\u2192+0.11).", size: 18 }),
            ]}),

            new Paragraph({ children: [new PageBreak()] }),

            new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Table 2: Within-Group Change (2020 \u2192 2023)")] }),
            makeTable(wHeader, wData, wCols, wWidth),

            new Paragraph({ spacing: { before: 200 }, children: [
                new TextRun({ text: "Key patterns \u2014 Estonians: ", bold: true, size: 18 }),
                new TextRun({ text: "More distant from Russian-speakers (+0.42***). More open to general out-groups (\u22120.23***). Less satisfied with opportunities (+0.30***). Less supportive of minority inclusion (+0.15**). Slightly more contact with Estonian speakers (\u22120.12*) and Russian speakers (\u22120.10*). No change in superordinate identity or conflict beliefs.", size: 18 }),
            ]}),
            new Paragraph({ spacing: { before: 100 }, children: [
                new TextRun({ text: "Key patterns \u2014 Russians: ", bold: true, size: 18 }),
                new TextRun({ text: "More open to general out-groups (\u22120.56***) \u2014 largest within-group shift. Substantially more contact with Estonian speakers (\u22120.51***). Less satisfied with opportunities (+0.34***). Stronger belief in inevitable conflict (+0.32***). No change in primary out-group attitudes, minority support, superordinate identity, or Russian speaker contact.", size: 18 }),
            ]}),
        ]
    }]
});

Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync("Composite_Comparison_Tables.docx", buffer);
    console.log("Composite_Comparison_Tables.docx created");
});
