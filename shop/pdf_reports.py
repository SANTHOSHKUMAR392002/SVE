"""Shared, good-looking PDF builder (reportlab) used by Sheet, Products and Reports downloads."""
import io
from datetime import datetime

TEAL = "#0E7C7B"; TEAL_LIGHT = "#E1F2F1"; INK = "#14212B"; MUTED = "#667684"; LINE = "#D5DDE2"
ORANGE = "#F97316"

def _load_wm():
    try:
        from pathlib import Path
        from PIL import Image
        p = Path(__file__).resolve().parent.parent / "static" / "img" / "watermark.png"
        with Image.open(p) as im: return str(p), im.width / im.height
    except Exception:
        return None            # PDFs still work without the watermark
_WM = _load_wm()


def _fmt(v):
    s = f"{v:f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def _chart(rows, width, height):
    """Grouped bar chart (Stock vs Sales per date) drawn with reportlab graphics."""
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.legends import Legend
    from reportlab.lib import colors
    d = Drawing(width, height)
    bc = VerticalBarChart()
    bc.x, bc.y, bc.width, bc.height = 38, 30, width - 52, height - 62
    bc.data = [[float(r["stock"]) for r in rows], [float(r["sales"]) for r in rows]]
    bc.categoryAxis.categoryNames = [r["date"].strftime("%d/%m") for r in rows]
    bc.categoryAxis.labels.fontSize = 7; bc.categoryAxis.labels.angle = 0
    if len(rows) > 14:
        bc.categoryAxis.labels.angle = 45; bc.categoryAxis.labels.dy = -8; bc.categoryAxis.labels.boxAnchor = "e"
    bc.valueAxis.valueMin = 0; bc.valueAxis.labels.fontSize = 7
    bc.valueAxis.gridStart = bc.x; bc.valueAxis.gridEnd = bc.x + bc.width
    bc.valueAxis.visibleGrid = True; bc.valueAxis.gridStrokeColor = colors.HexColor("#EDF0F3")
    bc.bars[0].fillColor = colors.HexColor(TEAL); bc.bars[1].fillColor = colors.HexColor(ORANGE)
    bc.bars.strokeColor = None; bc.groupSpacing = 6; bc.barSpacing = 1
    bc.categoryAxis.strokeColor = colors.HexColor(LINE); bc.valueAxis.strokeColor = colors.HexColor(LINE)
    d.add(bc)
    d.add(String(8, height - 10, "Quantity (units)", fontSize=7, fillColor=colors.HexColor(MUTED)))
    d.add(String(bc.x + bc.width / 2 - 8, 4, "Date", fontSize=7, fillColor=colors.HexColor(MUTED)))
    lg = Legend(); lg.x = width - 150; lg.y = height - 6; lg.fontSize = 8; lg.alignment = "right"
    lg.colorNamePairs = [(colors.HexColor(TEAL), "Stock"), (colors.HexColor(ORANGE), "Sales")]
    lg.columnMaximum = 1; lg.deltax = 60; lg.dxTextSpace = 4; lg.boxAnchor = "nw"; lg.strokeColor = None
    d.add(lg)
    return d


def build_table_pdf(*, shop_name, title, subtitle, headers, rows, widths_mm, right_from=None,
                    summary=None, chart_rows=None, totals_row=None, landscape_mode=True, empty_text="No data found", extra=None):
    """rows: list of lists of strings. summary: [(label, value)]. totals_row: list of strings (bold)."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
    page = landscape(A4) if landscape_mode else A4
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=page, leftMargin=14*mm, rightMargin=14*mm, topMargin=26*mm,
                            bottomMargin=16*mm, title=f"{shop_name} - {title}")
    ss = getSampleStyleSheet()
    h = ParagraphStyle("h", parent=ss["Title"], alignment=0, fontSize=17, leading=20, textColor=colors.HexColor(INK), spaceAfter=2)
    sub = ParagraphStyle("s", parent=ss["Normal"], textColor=colors.HexColor(MUTED), fontSize=9)
    cell = ParagraphStyle("c", parent=ss["Normal"], fontSize=9, leading=11)
    esc = lambda t: str(t).replace("&", "&amp;").replace("<", "&lt;")
    story = [Paragraph(esc(title), h), Paragraph(esc(subtitle), sub), Spacer(1, 8)]

    usable = page[0] - 28*mm
    if summary:
        n = len(summary)
        lab = ParagraphStyle("l", parent=cell, textColor=colors.HexColor(MUTED), fontSize=8)
        val = ParagraphStyle("v", parent=cell, fontSize=15, leading=18, fontName="Helvetica-Bold", textColor=colors.HexColor(INK))
        cards = Table([[Paragraph(esc(k), lab) for k, _ in summary], [Paragraph(esc(v), val) for _, v in summary]],
                      colWidths=[usable / n] * n)
        cards.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(TEAL_LIGHT)),
            ("LINEAFTER", (0, 0), (-2, -1), 3, colors.white), ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, 0), 8), ("BOTTOMPADDING", (0, 1), (-1, 1), 8), ("TOPPADDING", (0, 1), (-1, 1), 0)]))
        story += [cards, Spacer(1, 10)]
    if chart_rows:
        story += [_chart(chart_rows, usable, 190), Spacer(1, 10)]

    body = []
    for r in rows:
        body.append([Paragraph(esc(c), cell) if (i not in range(right_from or 99, 99) and len(str(c)) > 24) else c
                     for i, c in enumerate(r)])
    data = [headers] + body
    if not rows: data.append([""] * len(headers)); data[-1][min(1, len(headers) - 1)] = empty_text
    if totals_row: data.append(totals_row)
    t = Table(data, colWidths=[w*mm for w in widths_mm], repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(TEAL)), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor(LINE)),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F7F7")])]
    if right_from is not None: style.append(("ALIGN", (right_from, 0), (-1, -1), "RIGHT"))
    if totals_row:
        style += [("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(TEAL_LIGHT)),
                  ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor(TEAL))]
    t.setStyle(TableStyle(style))
    story.append(t)

    if extra:   # extra = dict(title, headers, rows, widths_mm, right_from)
        story += [Spacer(1, 16), Paragraph(esc(extra["title"]), h)]
        t2 = Table([extra["headers"]] + extra["rows"], colWidths=[w*mm for w in extra["widths_mm"]], repeatRows=1)
        t2.setStyle(TableStyle([s for s in style if s[0] != "LINEABOVE" and not (s[0] in ("FONTNAME", "BACKGROUND") and s[1][1] == -1 and s[2][1] == -1)]
                                + [("ALIGN", (extra["right_from"], 0), (-1, -1), "RIGHT")]))
        story.append(t2)

    stamp = datetime.now().strftime("%d-%m-%Y %H:%M")
    def deco(c, d):
        c.saveState(); w, hgt = page
        if _WM:
            ih = (hgt - 40*mm) * 0.62; iw = ih * _WM[1]
            c.saveState(); c.setFillAlpha(0.07)
            c.drawImage(_WM[0], (w - iw) / 2, (hgt - 17*mm - ih) / 2 + 8*mm, width=iw, height=ih, mask="auto")
            c.restoreState()
        c.setFillColor(colors.HexColor(TEAL)); c.rect(0, hgt - 16*mm, w, 16*mm, stroke=0, fill=1)
        c.setFillColor(colors.HexColor(ORANGE)); c.rect(0, hgt - 17.2*mm, w, 1.2*mm, stroke=0, fill=1)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 14); c.drawString(14*mm, hgt - 10.5*mm, shop_name)
        c.setFont("Helvetica", 9); c.drawRightString(w - 14*mm, hgt - 10.5*mm, title)
        c.setFillColor(colors.HexColor(MUTED)); c.setFont("Helvetica", 8)
        c.drawString(14*mm, 8*mm, f"Generated {stamp}"); c.drawRightString(w - 14*mm, 8*mm, f"Page {d.page}")
        c.restoreState()
    doc.build(story, onFirstPage=deco, onLaterPages=deco)
    return buf.getvalue()


# ---------- ready-made reports ----------
def products_pdf(products, shop_name, q=""):
    rows = [[str(i), p.name, p.hsn_code or "-", _fmt(p.total_stock or 0), _fmt(p.total_sales or 0), _fmt(p.balance)]
            for i, p in enumerate(products, 1)]
    sub = f"{len(products)} product{'s' if len(products) != 1 else ''}" + (f"  |  Search: {q}" if q else "")
    return build_table_pdf(shop_name=shop_name, title="Products List", subtitle=sub,
        headers=["S.No", "Product Name", "HSN Code", "Stock Bought", "Sales", "Balance"], rows=rows,
        widths_mm=[16, 122, 34, 32, 32, 33], right_from=3, landscape_mode=True,
        empty_text="No products found")


def report_pdf(shop_name, start, end, day_rows, tot, vendor_rows=None):
    rows = [[r["date"].strftime("%d-%m-%Y"), r["date"].strftime("%A"), str(r["entries"]),
             _fmt(r["stock"]), _fmt(r["sales"]), _fmt(r["balance"])] for r in day_rows]
    return build_table_pdf(shop_name=shop_name, title="Stock & Sales Report",
        subtitle=f"Period: {start.strftime('%d-%m-%Y')} to {end.strftime('%d-%m-%Y')}  |  date-wise",
        headers=["Date", "Day", "Entries", "Stock", "Sales", "Balance"], rows=rows,
        widths_mm=[44, 60, 32, 44, 44, 45], right_from=2,
        summary=[("Stock bought", _fmt(tot["stock"])), ("Sales", _fmt(tot["sales"])),
                 ("Balance", _fmt(tot["balance"])), ("Entries", str(tot["entries"]))],
        totals_row=["TOTAL", "", str(tot["entries"]), _fmt(tot["stock"]), _fmt(tot["sales"]), _fmt(tot["balance"])] if rows else None,
        empty_text="No entries in this period",
        extra=({"title": "Vendor-wise supply", "headers": ["Vendor", "GST number", "Entries", "Stock", "Sales", "Amount (Rs.)"],
                "rows": [[v["name"], v["gst"] or "-", str(v["entries"]), _fmt(v["stock"]), _fmt(v["sales"]), f"{v['amount']:,.2f}"] for v in vendor_rows],
                "widths_mm": [78, 52, 28, 32, 32, 45], "right_from": 2}) if vendor_rows else None)
