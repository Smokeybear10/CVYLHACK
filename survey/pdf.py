"""Render a SiteReport (or several) into a professional PDF with reportlab.

reportlab is pure-Python (no system libraries), so this works anywhere. Styling
follows research/05: restrained navy + accent palette, RAG scorecard chips (color
plus a letter so they survive grayscale), running footer with page numbers. The PDF
renders only from the validated report, so it inherits the no-hallucination
guarantee. (WeasyPrint + HTML/CSS is the higher-fidelity swap noted in research/05.)
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable, ListFlowable, ListItem, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

from .schema import SiteReport

# --- palette (research/05) ---
NAVY = colors.HexColor("#14213D")
INK = colors.HexColor("#1A1A1A")
ACCENT = colors.HexColor("#E76F00")
GRAY = colors.HexColor("#667085")
RULE = colors.HexColor("#D0D5DD")
ZEBRA = colors.HexColor("#F2F4F7")
RAG = {"GO": colors.HexColor("#2E7D32"), "CAUTION": colors.HexColor("#D69E2E"),
       "NO-GO": colors.HexColor("#C62828")}
TIER_COLOR = {"Tier 1": colors.HexColor("#2E7D32"), "Tier 2": colors.HexColor("#2F6FB0"),
              "Tier 3": colors.HexColor("#D69E2E"), "No-go": colors.HexColor("#C62828")}
RAG_LETTER = {"GO": "G", "CAUTION": "A", "NO-GO": "R"}

MARGIN = inch
PAGE_W, PAGE_H = letter

_ss = getSampleStyleSheet()
TITLE = ParagraphStyle("t", parent=_ss["Title"], fontName="Helvetica-Bold", fontSize=19,
                       textColor=NAVY, spaceAfter=2, alignment=TA_LEFT)
SUB = ParagraphStyle("sub", parent=_ss["Normal"], fontName="Helvetica", fontSize=9,
                     textColor=GRAY, spaceAfter=8)
H2 = ParagraphStyle("h2", parent=_ss["Heading2"], fontName="Helvetica-Bold", fontSize=12,
                    textColor=NAVY, spaceBefore=12, spaceAfter=4)
BODY = ParagraphStyle("body", parent=_ss["Normal"], fontName="Helvetica", fontSize=9.5,
                      textColor=INK, leading=13)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=9, leading=11)
CELL_W = ParagraphStyle("cellw", parent=CELL, textColor=colors.white, fontName="Helvetica-Bold")


def _num(x, suffix=""):
    if x is None:
        return "n/a"
    if isinstance(x, float) and x.is_integer():
        x = int(x)
    return f"{x}{suffix}"


def _bullets(items):
    items = [i for i in (items or []) if i]
    if not items:
        return Paragraph("None.", BODY)
    return ListFlowable([ListItem(Paragraph(str(i), BODY), leftIndent=10) for i in items],
                        bulletType="bullet", start="•", bulletColor=ACCENT, bulletFontSize=7)


def _h2(text):
    return [Paragraph(text, H2), HRFlowable(width="100%", thickness=0.5, color=RULE,
                                            spaceBefore=1, spaceAfter=5)]


def _kv(pairs):
    rows = [[Paragraph(f"<b>{k}</b>", CELL), Paragraph(str(v), CELL)] for k, v in pairs]
    t = Table(rows, colWidths=[1.9 * inch, 4.4 * inch])
    style = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 2),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 2), ("LINEBELOW", (0, 0), (-1, -2), 0.25, RULE)]
    for i in range(len(rows)):
        if i % 2:
            style.append(("BACKGROUND", (0, i), (-1, i), ZEBRA))
    t.setStyle(TableStyle(style))
    return t


def _verdict_badge(report: SiteReport):
    v = report.verdict
    color = TIER_COLOR.get(v.tier, NAVY)
    badge = Paragraph(f"{v.tier}", ParagraphStyle("badge", parent=CELL_W, fontSize=12, alignment=1))
    reason = Paragraph(f"<b>{v.one_line_reason}</b><br/><font color='#667085' size=8>"
                       f"Composite screening score {_num(v.composite_score)} / 100</font>", CELL)
    t = Table([[badge, reason]], colWidths=[1.5 * inch, 4.8 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), color), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("BOX", (0, 0), (-1, -1), 0.5, RULE),
    ]))
    return t


def _scorecard(report: SiteReport):
    header = [Paragraph(f"<b>{h}</b>", CELL_W) for h in ("Criterion", "Finding", "Rating", "Src")]
    rows = [header]
    rating_rows = []
    for r in report.scorecard:
        label = f"{r.rating} ({RAG_LETTER.get(r.rating, '?')})"
        rows.append([Paragraph(r.criterion, CELL), Paragraph(r.value, CELL),
                     Paragraph(f"<b>{label}</b>", CELL_W), Paragraph(r.source, CELL)])
        rating_rows.append((len(rows) - 1, RAG.get(r.rating, GRAY)))
    t = Table(rows, colWidths=[1.8 * inch, 3.0 * inch, 1.0 * inch, 0.5 * inch], repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
             ("GRID", (0, 0), (-1, -1), 0.25, RULE)]
    for ridx, color in rating_rows:
        style.append(("BACKGROUND", (2, ridx), (2, ridx), color))
    t.setStyle(TableStyle(style))
    return t


def _site_flowables(report: SiteReport):
    s, m = report.site, report
    out = [Paragraph("Curbside EV Charging — Site Assessment", TITLE)]
    coords = f"{s.lat:.5f}, {s.lon:.5f}"
    out.append(Paragraph(f"Site {s.id} &nbsp;|&nbsp; {s.street or 'curb segment'} "
                         f"&nbsp;|&nbsp; {coords}" + (f" &nbsp;|&nbsp; {s.region}" if s.region else ""), SUB))
    out.append(_verdict_badge(report))
    out.append(Spacer(1, 6))

    out += _h2("Executive summary"); out.append(_bullets(report.executive_summary))
    out += _h2("Scorecard"); out.append(_scorecard(report))

    pf = report.physical_fit
    out += _h2("Physical fit")
    out.append(_kv([("Usable frontage", _num(pf.usable_frontage_ft, " ft")),
                    ("Ports that fit", _num(pf.ports_that_fit)),
                    ("Road width", _num(pf.road_width_ft, " ft"))]))
    if pf.notes:
        out.append(Spacer(1, 2)); out.append(_bullets(pf.notes))

    c = report.connection
    out += _h2("Connection and make-ready (rough order of magnitude)")
    out.append(_kv([("Distance to power", _num(c.distance_to_power_m, " m")),
                    ("Connection point", c.pole_type or "n/a"),
                    ("Trench length", _num(c.trench_len_ft, " ft")),
                    ("Surface to cut", c.surface or "verify on site"),
                    ("Estimated make-ready", (f"${int(c.rom_cost_usd):,}" if c.rom_cost_usd else "n/a")
                     + (f" ({c.cost_band})" if c.cost_band else ""))]))
    out.append(Paragraph("<font size=8 color='#667085'>Estimate excludes:</font>", BODY))
    out.append(_bullets(c.exclusions))

    d = report.demand
    out += _h2("Demand")
    out.append(_kv([("Residential suitability", _num(d.residential_suit)),
                    ("Traveler suitability", _num(d.traveler_suit)),
                    ("Road functional class", _num(d.functional_class)),
                    ("Nearby chargers", _num(d.nearby_chargers))]))
    if d.notes:
        out.append(_bullets(d.notes))

    sc = report.site_conditions
    out += _h2("Site conditions")
    out.append(_kv([("Pavement PCI", _num(sc.pavement_pci)), ("Surface", sc.surface or "verify on site"),
                    ("Obstructions in frontage", _num(sc.obstruction_count))]))
    if sc.clearance_notes:
        out.append(_bullets(sc.clearance_notes))

    a = report.accessibility
    out += _h2("Accessibility")
    out.append(_kv([("Near a curb ramp", "verify on site" if a.near_curb_ramp is None
                     else ("yes" if a.near_curb_ramp else "no"))]))
    if a.notes:
        out.append(_bullets(a.notes))

    out += _h2("Risks and constraints"); out.append(_bullets(report.risks_and_constraints))
    out += _h2("To be verified on site"); out.append(_bullets(report.to_be_verified))
    out += _h2("Next steps"); out.append(_bullets(report.next_steps))

    if report.evidence.photo_ref or report.evidence.cv_findings:
        out += _h2("Evidence")
        if report.evidence.photo_ref:
            out.append(Paragraph(f"Photo: {report.evidence.photo_ref}", BODY))
        if report.evidence.cv_findings:
            out.append(_bullets(report.evidence.cv_findings))
    return out


class _NumberedCanvas(canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self._footer(total)
            super().showPage()
        super().save()

    def _footer(self, total):
        self.setFont("Helvetica", 8)
        self.setFillColor(GRAY)
        self.drawString(MARGIN, 0.5 * inch, "Sonder — screening assessment, verify on site")
        self.drawRightString(PAGE_W - MARGIN, 0.5 * inch, f"Page {self._pageNumber} of {total}")
        self.setStrokeColor(RULE)
        self.line(MARGIN, 0.65 * inch, PAGE_W - MARGIN, 0.65 * inch)


def build_pdf(reports, out_path) -> str:
    """Render one or more SiteReports to a PDF at out_path. Returns the path."""
    if isinstance(reports, SiteReport):
        reports = [reports]
    out_path = str(out_path)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(out_path, pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=0.9 * inch,
                            title="Sonder Site Assessment")
    story = []
    for i, r in enumerate(reports):
        story += _site_flowables(r)
        if i < len(reports) - 1:
            story.append(PageBreak())
    doc.build(story, canvasmaker=_NumberedCanvas)
    return out_path
