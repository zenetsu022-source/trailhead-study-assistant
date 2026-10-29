from __future__ import annotations
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from analyzer import ModuleReport
class NumberedCanvas(Canvas):
    def __init__(self, *args, **kwargs): Canvas.__init__(self, *args, **kwargs); self._saved_page_states = []
    def showPage(self): self._saved_page_states.append(dict(self.__dict__)); self._startPage()
    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states: self.__dict__.update(state); self.draw_page_number(total); Canvas.showPage(self)
        Canvas.save(self)
    def draw_page_number(self, total):
        self.saveState(); self.setFont("Helvetica", 8); self.setFillColor(colors.grey); self.drawString(.6*inch, .4*inch, self._module_title[:90]); self.drawRightString(7.9*inch, .4*inch, f"Page {self._pageNumber} of {total}"); self.restoreState()
def build_pdf(extraction: dict, report: ModuleReport, output: str | Path) -> Path:
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True); styles = getSampleStyleSheet(); styles.add(ParagraphStyle(name="Cover", parent=styles["Title"], alignment=TA_CENTER, textColor=colors.HexColor("#163A5F"), fontSize=24)); styles.add(ParagraphStyle(name="H1x", parent=styles["Heading1"], textColor=colors.HexColor("#163A5F"))); styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], backColor=colors.HexColor("#EAF3F8"), borderPadding=8, spaceAfter=8))
    def p(text, style="BodyText"): return Paragraph(str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), styles[style])
    story = [Spacer(1, inch), p("Salesforce Trailhead Study Guide", "Cover"), p(report.module_title, "Title"), Spacer(1, .3*inch), p("What This Module Is For & What It Teaches", "H1x"), p(report.executive_summary), PageBreak(), p("Target Roles", "H1x"), p(" • ".join(report.target_role) or "Not specified"), p("Key Learnings", "H1x")]
    story += [p("• " + x) for x in report.key_learnings] + [p("Hands-On Walkthrough", "H1x")] + [p(f"<b>{x.step}</b>: {x.explanation}") for x in report.hands_on_walkthrough] + [p("Limits, Best Practices & Gotchas", "H1x")] + [p("• " + x, "Callout") for x in report.limits_and_best_practices] + [p("Concept Q&A", "H1x")]
    for x in report.concept_qa: story += [p(f"<b>Question:</b> {x.question}"), p(f"<b>Explanation:</b> {x.explanation}", "Callout")]
    story += [p("Extracted Code Reference", "H1x")]
    for code in extraction.get("code_snippets", []): story += [Preformatted(code[:5000], styles["Code"]), Spacer(1, 6)]
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=.65*inch, leftMargin=.65*inch, topMargin=.65*inch, bottomMargin=.65*inch, title=report.module_title)
    def first(canvas, doc): canvas._module_title = report.module_title
    doc.build(story, onFirstPage=first, onLaterPages=first, canvasmaker=NumberedCanvas); return path


