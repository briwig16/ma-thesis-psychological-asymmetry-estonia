"""
Embed the bivariate-slope-per-variable figure into a Word document, in-line
and sized to the page text width so it scales with the document.

Re-uses the exact plotting code in 107_bivariate_slope_per_variable.py by
exec-ing it (which also refreshes the canonical .jpg), then grabs the live
Figure object and saves a crisp 300-DPI PNG (sharper text than JPEG) for
embedding. python-docx inserts it as an in-line picture sized to the usable
text width, so Word scales it to the page and the user can drag-resize.

Output: reports/Bivariate_Slope_Per_Variable.docx
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).parent.parent

# --- Re-run the canonical figure script, but capture the Figure instead of
#     stopping at its own jpg save. We strip its trailing save/print lines so
#     the `fig` object is left in the namespace for us to re-export. ---
src = (ROOT / "code" / "107_bivariate_slope_per_variable.py").read_text()
marker = "out = ROOT / \"viz\""
src_head = src.split(marker)[0]            # everything up to the final save block
ns = {"__file__": str(ROOT / "code" / "107_bivariate_slope_per_variable.py")}
exec(compile(src_head, "<107_plot>", "exec"), ns)
fig = ns["fig"]

# Crisp PNG for embedding (lossless text vs. the JPEG)
png_path = ROOT / "viz" / "fig_bivariate_slope_per_variable.png"
fig.savefig(png_path, dpi=300, format="png", facecolor="white")
plt.close(fig)

# --- Build the Word document ---
doc = Document()

# Set page to A4 portrait with modest margins so the tall figure fits on a page
section = doc.sections[0]
section.page_width = Inches(8.27)
section.page_height = Inches(11.69)
section.top_margin = Inches(0.6)
section.bottom_margin = Inches(0.6)
section.left_margin = Inches(0.7)
section.right_margin = Inches(0.7)

usable_width = Inches(
    (section.page_width - section.left_margin - section.right_margin) / 914400
)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run()
# Width = usable text width -> in-line, scales to the page, height auto-keeps ratio
run.add_picture(str(png_path), width=usable_width)

cap = doc.add_paragraph()
cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
cr = cap.add_run(
    "Figure 1. Bivariate contact slopes by outcome (standardized β per "
    "group × year cell)."
)
cr.italic = True
cr.font.size = Pt(9)

out = ROOT / "reports" / "Bivariate_Slope_Per_Variable.docx"
doc.save(out)
print(f"Saved: {out}")
print(f"PNG:   {png_path}")
print(f"Image embedded at width = {usable_width.inches:.2f} in (in-line, scales to page)")
