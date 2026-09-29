from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse


from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import ArcPath, Circle, Drawing, String
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PAGE_WIDTH, PAGE_HEIGHT = A4

GREEN = colors.HexColor("#2E7D5B")
PURPLE = colors.HexColor("#7457C8")
BLUE = colors.HexColor("#3976B8")
ORANGE = colors.HexColor("#C87932")
DARK = colors.HexColor("#20242B")
MID = colors.HexColor("#626A73")
LIGHT = colors.HexColor("#F4F5F7")
BORDER = colors.HexColor("#D9DDE3")
GREEN_LIGHT = colors.HexColor("#F2F8F5")
PURPLE_LIGHT = colors.HexColor("#F6F3FC")
BLUE_LIGHT = colors.HexColor("#F2F6FB")
SUMMARY_LIGHT = colors.HexColor("#EEF7F2")


def _text(value, fallback="–"):
    if value is None or value == "":
        return fallback
    return str(value)


def _number(value, digits=1, suffix=""):
    if value is None:
        return "–"

    try:
        return f"{float(value):.{digits}f}{suffix}"
    except (TypeError, ValueError):
        return str(value)


def _score(value, maximum=100):
    if value is None:
        return "–"
    return f"{_number(value, 0)} / {maximum}"


def _styles():
    base = getSampleStyleSheet()

    return {
        "brand": ParagraphStyle(
            "brand",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=MID,
            spaceAfter=3 * mm,
        ),
        "company": ParagraphStyle(
            "company",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=22,
            textColor=DARK,
            spaceAfter=1.5 * mm,
        ),
        "meta": ParagraphStyle(
            "meta",
            parent=base["Normal"],
            fontSize=8.5,
            leading=11,
            textColor=MID,
        ),
        "section": ParagraphStyle(
            "section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=15,
            textColor=DARK,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        ),
        "card_title": ParagraphStyle(
            "card_title",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=MID,
        ),
        "score": ParagraphStyle(
            "score",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=18,
            textColor=DARK,
            alignment=TA_CENTER,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontSize=8.7,
            leading=12.8,
            textColor=DARK,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["BodyText"],
            fontSize=7.5,
            leading=10,
            textColor=MID,
        ),
        "decision": ParagraphStyle(
            "decision",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            textColor=DARK,
        ),
        "eyebrow": ParagraphStyle(
            "eyebrow",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7,
            leading=9,
            textColor=MID,
            spaceAfter=1.2 * mm,
        ),
        "hero_body": ParagraphStyle(
            "hero_body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.2,
            leading=13,
            textColor=MID,
        ),
        "score_card_value": ParagraphStyle(
            "score_card_value",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=19,
            textColor=DARK,
        ),
        "score_card_label": ParagraphStyle(
            "score_card_label",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9,
            textColor=MID,
        ),
    }


LOGO_CACHE_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "logo_cache"
)


def _company_logo_domain(website):
    """Ermittelt eine sichere Domain für den lokalen Logo-Cache."""
    if not website:
        return None

    try:
        domain = urlparse(str(website)).netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        if not domain:
            return None

        return domain

    except Exception:
        return None


def _company_logo(website):
    """Lädt ein Firmenlogo ausschließlich aus dem lokalen Cache.

    Der PDF-Export führt bewusst keinen Netzwerkzugriff aus.
    Fehlt das Logo lokal, wird der Report sofort ohne Logo erzeugt.
    """
    domain = _company_logo_domain(website)

    if not domain:
        return None

    logo_path = LOGO_CACHE_DIR / f"{domain}.png"

    if not logo_path.is_file():
        return None

    try:
        logo_bytes = logo_path.read_bytes()

        if not logo_bytes:
            return None

        image_buffer = BytesIO(logo_bytes)

        # Beschädigte Cache-Dateien dürfen den Report nicht abbrechen.
        ImageReader(image_buffer).getSize()
        image_buffer.seek(0)

        return Image(
            image_buffer,
            width=13 * mm,
            height=13 * mm,
        )

    except Exception:
        return None



def _price_chart(price_history, currency=None):
    """Erzeugt einen kompakten 1J-Kurschart als Vektorgrafik."""
    if not price_history or len(price_history) < 2:
        return None

    values = []

    for index, item in enumerate(price_history):
        try:
            close = float(item["close"])
        except (KeyError, TypeError, ValueError):
            continue

        values.append((index, close))

    if len(values) < 2:
        return None

    prices = [value[1] for value in values]
    minimum = min(prices)
    maximum = max(prices)

    if minimum == maximum:
        padding = max(abs(minimum) * 0.05, 1)
    else:
        padding = (maximum - minimum) * 0.10

    drawing = Drawing(
        178 * mm,
        48 * mm,
    )

    chart = LinePlot()
    chart.x = 13 * mm
    chart.y = 8 * mm
    chart.width = 157 * mm
    chart.height = 33 * mm
    chart.data = [values]

    chart.xValueAxis.valueMin = 0
    chart.xValueAxis.valueMax = len(price_history) - 1
    chart.xValueAxis.valueSteps = [
        0,
        (len(price_history) - 1) / 2,
        len(price_history) - 1,
    ]
    chart.xValueAxis.labelTextFormat = lambda value: ""

    chart.yValueAxis.valueMin = minimum - padding
    chart.yValueAxis.valueMax = maximum + padding
    chart.yValueAxis.labels.fontName = "Helvetica"
    chart.yValueAxis.labels.fontSize = 6.5
    chart.yValueAxis.labels.fillColor = MID
    chart.yValueAxis.strokeColor = BORDER
    chart.yValueAxis.gridStrokeColor = BORDER
    chart.yValueAxis.gridStrokeWidth = 0.35
    chart.yValueAxis.visibleGrid = True

    chart.xValueAxis.strokeColor = BORDER
    chart.xValueAxis.tickDown = 0
    chart.xValueAxis.tickUp = 0

    chart.lines[0].strokeColor = PURPLE
    chart.lines[0].strokeWidth = 1.8
    chart.lines[0].symbol = None

    drawing.add(chart)

    first_date = price_history[0].get("date", "")
    last_date = price_history[-1].get("date", "")

    drawing.add(
        String(
            13 * mm,
            2.5 * mm,
            first_date,
            fontName="Helvetica",
            fontSize=6.5,
            fillColor=MID,
        )
    )

    drawing.add(
        String(
            170 * mm,
            2.5 * mm,
            last_date,
            fontName="Helvetica",
            fontSize=6.5,
            fillColor=MID,
            textAnchor="end",
        )
    )

    currency_label = f" · {currency}" if currency else ""

    drawing.add(
        String(
            13 * mm,
            44 * mm,
            f"1 Jahr · Schlusskurs{currency_label}",
            fontName="Helvetica-Bold",
            fontSize=7.5,
            fillColor=DARK,
        )
    )

    return drawing


def _investment_score_ring(value, color):
    """Zeigt den Investment-Score als partiell gefüllten Kreisring."""
    drawing = Drawing(30 * mm, 30 * mm)

    cx = 15 * mm
    cy = 15 * mm
    radius = 11 * mm

    # Ruhiger Hintergrundring.
    drawing.add(
        Circle(
            cx,
            cy,
            radius,
            fillColor=None,
            strokeColor=BORDER,
            strokeWidth=3.2,
        )
    )

    try:
        score = max(0.0, min(100.0, float(value)))
    except (TypeError, ValueError):
        score = 0.0

    # ReportLab misst Winkel gegen den Uhrzeigersinn.
    # Beginn oben; gefüllter Anteil entspricht exakt dem Score.
    extent = 360.0 * score / 100.0

    if extent > 0:
        arc = ArcPath()
        arc.addArc(
            cx,
            cy,
            radius,
            90,
            90 + extent,
        )
        arc.strokeColor = color
        arc.strokeWidth = 3.4
        arc.fillColor = None

        drawing.add(arc)

    drawing.add(
        String(
            cx,
            cy + 1.2 * mm,
            _number(value, 0),
            fontName="Helvetica-Bold",
            fontSize=14,
            fillColor=DARK,
            textAnchor="middle",
        )
    )

    drawing.add(
        String(
            cx,
            cy - 4.0 * mm,
            "/ 100",
            fontName="Helvetica",
            fontSize=6.5,
            fillColor=MID,
            textAnchor="middle",
        )
    )

    return drawing


def _summary_score_card(title, value, maximum, color, styles):
    """Ruhige Score-Karte für die drei Analysebereiche."""
    content = [
        [
            Paragraph(
                title.upper(),
                styles["score_card_label"],
            )
        ],
        [
            Paragraph(
                _score(value, maximum),
                styles["score_card_value"],
            )
        ],
    ]

    table = Table(
        content,
        colWidths=[54 * mm],
        rowHeights=[7 * mm, 11 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.55, BORDER),
                ("LINEABOVE", (0, 0), (-1, 0), 2.5, color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ]
        )
    )

    return table


def _score_card(title, value, maximum, color, styles):
    table = Table(
        [
            [Paragraph(title, styles["card_title"])],
            [Paragraph(_score(value, maximum), styles["score"])],
        ],
        colWidths=[52 * mm],
        rowHeights=[8 * mm, 13 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("LINEABOVE", (0, 0), (-1, 0), 3, color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )

    return table


def _section_box(title, body, color, styles):
    content = [
        [
            Paragraph(
                f"<b>{title}</b>",
                styles["body"],
            )
        ],
        [Paragraph(body or "Keine Daten verfügbar.", styles["body"])],
    ]

    table = Table(content, colWidths=[178 * mm])

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 3, color),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
            ]
        )
    )

    return table


def _opportunity_subcards(blocks, entry_setup, styles):
    """Drei kompakte Karten für Bewertung, Technik und Entry Setup."""
    cards = [
        (
            "Kursbewertung",
            f"{_number(blocks.get('fundamental_points'), 1)} / 45",
            "",
        ),
        (
            "Technische Verfassung",
            f"{_number(blocks.get('technical_points'), 1)} / 25",
            "",
        ),
        (
            "Entry Setup",
            f"{_number(blocks.get('entry_points'), 1)} / 30",
            _text(entry_setup),
        ),
    ]

    content = []

    for title, score, detail in cards:
        body = (
            f"<font color='#6B7280' size='7'>{title}</font>"
            f"<br/>"
            f"<font size='13'><b>{score}</b></font>"
        )

        if detail:
            body += (
                f"<br/>"
                f"<font color='#6B7280' size='6.5'>{detail}</font>"
            )

        content.append(
            Paragraph(
                body,
                styles["body"],
            )
        )

    table = Table(
        [content],
        colWidths=[
            59.3 * mm,
            59.3 * mm,
            59.4 * mm,
        ],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, BORDER),
                ("LINEABOVE", (0, 0), (-1, 0), 2.2, PURPLE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )

    return table


def _section_box_two_columns(
    title,
    left_body,
    right_body,
    color,
    styles,
):
    content = [
        [
            Paragraph(
                f"<b>{title}</b>",
                styles["body"],
            ),
            Paragraph(
                right_body or "",
                styles["body"],
            ),
        ],
        [
            Paragraph(
                left_body or "Keine Daten verfügbar.",
                styles["body"],
            ),
            "",
        ],
    ]

    table = Table(
        content,
        colWidths=[82 * mm, 96 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 3.5, color),
                ("SPAN", (1, 0), (1, 1)),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4.5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4.5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )

    return table


def _inra_fazit_box(body, styles):
    """Hervorgehobener Abschluss des Research-Reports."""
    content = [
        [
            Paragraph(
                "<font size='7' color='#2E7D5B'>"
                "<b>INRA · RESEARCH-FAZIT</b>"
                "</font>",
                styles["body"],
            )
        ],
        [
            Paragraph(
                "<font size='12'><b>Investment Case</b></font>",
                styles["body"],
            )
        ],
        [
            Paragraph(
                body or "Keine Daten verfügbar.",
                styles["body"],
            )
        ],
    ]

    table = Table(
        content,
        colWidths=[178 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SUMMARY_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.7, GREEN),
                ("LINEBEFORE", (0, 0), (0, -1), 4, GREEN),
                ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )

    return table


def _inra_summary_text(summary):
    if not isinstance(summary, dict):
        return _text(summary)

    parts = []

    for key, label in (
        ("Kernaussage", None),
        ("Dafuer", "Dafür"),
        ("Dagegen", "Dagegen"),
        ("Worauf_es_ankommt", "Worauf es ankommt"),
    ):
        value = summary.get(key)

        if value:
            if label:
                parts.append(f"<b>{label}:</b> {_text(value)}")
            else:
                parts.append(_text(value))

    if not parts and summary.get("Text"):
        parts.append(_text(summary.get("Text")))

    return "<br/>".join(parts) if parts else "Keine Daten verfügbar."


def _current_intelligence_item_text(item):
    """Formatiert einen Current-Intelligence-Eintrag kompakt fürs PDF."""
    if isinstance(item, dict):
        title = item.get("Titel")
        description = item.get("Beschreibung")

        if title and description:
            return (
                f"<b>{_text(title)}</b> – "
                f"{_text(description)}"
            )

        if title:
            return f"<b>{_text(title)}</b>"

        if description:
            return _text(description)

    return _text(item)


def _current_intelligence_text(current):
    if not isinstance(current, dict):
        return "Keine aktuellen Entwicklungen verfügbar."

    parts = []

    positives = current.get("Positive_Entwicklungen") or []
    negatives = current.get("Negative_Entwicklungen") or []
    open_factors = current.get("Offene_Faktoren") or []

    if positives:
        parts.append(
            "<b>Rückenwind</b><br/>"
            + "<br/>".join(
                _current_intelligence_item_text(item)
                for item in positives[:2]
            )
        )

    if negatives:
        parts.append(
            "<b>Gegenwind</b><br/>"
            + "<br/>".join(
                _current_intelligence_item_text(item)
                for item in negatives[:2]
            )
        )

    if open_factors:
        parts.append(
            "<b>Darauf kommt es an</b><br/>"
            + "<br/>".join(
                _current_intelligence_item_text(item)
                for item in open_factors[:2]
            )
        )

    event_status = current.get("Event_Impact_Status")
    event_reason = current.get("Event_Impact_Begruendung")

    if event_status or event_reason:
        parts.append(
            "<b>Event Impact</b><br/>"
            + " · ".join(
                _text(value)
                for value in (event_status, event_reason)
                if value
            )
        )

    return "<br/><br/>".join(parts) or (
        "Keine aktuellen Entwicklungen verfügbar."
    )


def _current_intelligence_summary_text(current):
    """Kompakte Current Intelligence für die Executive Summary."""
    if not isinstance(current, dict):
        return "Keine aktuellen Entwicklungen verfügbar."

    parts = []

    for key, label in (
        ("Positive_Entwicklungen", "Rückenwind"),
        ("Negative_Entwicklungen", "Gegenwind"),
        ("Offene_Faktoren", "Darauf kommt es an"),
    ):
        items = current.get(key) or []

        if items:
            parts.append(
                f"<b>{label}</b><br/>"
                + _current_intelligence_item_text(items[0])
            )

    return "<br/><br/>".join(parts) or (
        "Keine aktuellen Entwicklungen verfügbar."
    )


def build_analysis_pdf(report: dict) -> bytes:
    """
    Erzeugt den auf maximal zwei DIN-A4-Seiten ausgelegten
    InRA-Analyse-Report.

    Es wird keine Bewertungslogik neu berechnet.
    """
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="InRA Aktienanalyse",
        author="InRA – Investment Research Assistant",
    )

    styles = _styles()
    story = []

    company = report.get("company") or {}
    scores = report.get("scores") or {}
    decision = report.get("investment_decision") or {}
    quality = report.get("quality") or {}
    opportunity = report.get("opportunity") or {}
    dividend = report.get("dividend") or {}
    valuation = report.get("valuation") or {}
    current = report.get("current_intelligence") or {}

    # =====================================================
    # SEITE 1 · EXECUTIVE SUMMARY
    # =====================================================

    # --- Marken-/Unternehmenskopf ---------------------------------

    brand_row = Table(
        [
            [
                Paragraph(
                    "<b>InRA</b> · Investment Research Assistant",
                    styles["brand"],
                ),
                Paragraph(
                    "AKTIENANALYSE",
                    styles["eyebrow"],
                ),
            ]
        ],
        colWidths=[140 * mm, 38 * mm],
    )

    brand_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(brand_row)
    story.append(Spacer(1, 1.5 * mm))

    meta = (
        f"{_text(company.get('ticker'))} · "
        f"{_text(company.get('exchange'))} · "
        f"{_text(company.get('currency'))} · "
        f"{_text(company.get('country'))}<br/>"
        f"{_text(company.get('sector'))} · "
        f"{_text(company.get('industry'))}"
    )

    company_content = [
        Paragraph(
            _text(company.get("name"), "Aktienanalyse"),
            styles["company"],
        ),
        Paragraph(meta, styles["meta"]),
    ]

    logo = _company_logo(company.get("website"))

    if logo:
        company_header = Table(
            [[logo, company_content]],
            colWidths=[18 * mm, 160 * mm],
        )

        company_header.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (0, 0), 4 * mm),
                    ("RIGHTPADDING", (1, 0), (1, 0), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        story.append(company_header)

    else:
        story.extend(company_content)

    story.append(Spacer(1, 3.5 * mm))

    # --- Investment-Urteil als Hero -------------------------------

    investment_score = decision.get("score")

    decision_left = [
        Paragraph(
            "INVESTMENT-URTEIL",
            styles["eyebrow"],
        ),
        Paragraph(
            _text(decision.get("title")),
            styles["decision"],
        ),
        Spacer(1, 1.5 * mm),
        Paragraph(
            _text(decision.get("text")),
            styles["hero_body"],
        ),
    ]

    decision_table = Table(
        [
            [
                decision_left,
                _investment_score_ring(
                    investment_score,
                    GREEN,
                ),
            ]
        ],
        colWidths=[142 * mm, 36 * mm],
    )

    decision_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 4, GREEN),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 6 * mm),
                ("RIGHTPADDING", (0, 0), (0, 0), 7 * mm),
                ("LEFTPADDING", (1, 0), (1, 0), 2 * mm),
                ("RIGHTPADDING", (1, 0), (1, 0), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )

    story.append(decision_table)
    story.append(Spacer(1, 3 * mm))

    # --- Drei Analyse-Scores --------------------------------------

    story.append(
        Paragraph("Die drei Perspektiven", styles["section"])
    )

    score_table = Table(
        [
            [
                _summary_score_card(
                    "Unternehmensqualität",
                    scores.get("quality"),
                    100,
                    GREEN,
                    styles,
                ),
                _summary_score_card(
                    "Kaufchance",
                    scores.get("opportunity"),
                    100,
                    PURPLE,
                    styles,
                ),
                _summary_score_card(
                    "Dividendenstrategie",
                    scores.get("dividend"),
                    15,
                    BLUE,
                    styles,
                ),
            ]
        ],
        colWidths=[59.3 * mm] * 3,
    )

    score_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1.3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1.3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(score_table)
    story.append(Spacer(1, 2.5 * mm))

    # --- Kursverlauf ----------------------------------------------

    price_history = report.get("price_history") or []

    if price_history:
        chart_header = Table(
            [
                [
                    Paragraph(
                        "Kursverlauf",
                        styles["section"],
                    ),
                    Paragraph(
                        "1 JAHR",
                        styles["eyebrow"],
                    ),
                ]
            ],
            colWidths=[140 * mm, 38 * mm],
        )

        chart_header.setStyle(
            TableStyle(
                [
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )

        story.append(chart_header)

        chart = _price_chart(
            price_history,
            currency=company.get("currency"),
        )

        if chart is not None:
            chart_box = Table(
                [[chart]],
                colWidths=[178 * mm],
            )

            chart_box.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                        ("BOX", (0, 0), (-1, -1), 0.55, BORDER),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
                    ]
                )
            )

            story.append(chart_box)

    story.append(Spacer(1, 2 * mm))

    # --- Aktuelle Entwicklungen ----------------------------------

    intelligence_header = Table(
        [
            [
                Paragraph(
                    "Aktuelle Entwicklungen",
                    styles["section"],
                ),
                Paragraph(
                    "CURRENT INTELLIGENCE",
                    styles["eyebrow"],
                ),
            ]
        ],
        colWidths=[130 * mm, 48 * mm],
    )

    intelligence_header.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    story.append(intelligence_header)

    story.append(
        _section_box(
            "Was den Investment Case aktuell bewegt",
            _current_intelligence_summary_text(current),
            ORANGE,
            styles,
        )
    )

    story.append(PageBreak())

    # 1 · Unternehmensqualität

    story.append(
        Paragraph(
            "1 · Unternehmensqualität",
            styles["section"],
        )
    )

    quality_breakdown = quality.get("breakdown") or {}

    quality_text = (
        f"<b>Gesamtscore:</b> "
        f"{_score(scores.get('quality'), 100)}"
        f"<br/>"
        f"<b>Quantitativ:</b> "
        f"{_number(quality.get('quantitative'), 0)}"
        f" &nbsp;&nbsp; "
        f"<b>Qualitativ:</b> "
        f"{_number(quality.get('qualitative'), 0)}"
        f"<br/><br/>"
        + "<br/>".join(
            f"<b>{_text(name)}:</b> "
            f"{_number(value, 1)} Punkte"
            for name, value in quality_breakdown.items()
        )
    )

    quality_box = _section_box_two_columns(
        "Qualitätsprofil",
        quality_text,
        _text(quality.get("summary")),
        GREEN,
        styles,
    )
    quality_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), GREEN_LIGHT),
            ]
        )
    )
    story.append(quality_box)

    # 2 · Kaufchance

    story.append(
        Paragraph(
            "2 · Kaufchance",
            styles["section"],
        )
    )

    blocks = opportunity.get("blocks") or {}

    opportunity_text = (
        f"<b>{_text(opportunity.get('rating'))}</b>"
        f"<br/><br/>"
        f"<b>Forward-KGV:</b> "
        f"{_number(valuation.get('forward_pe'), 1)}"
        f" &nbsp;&nbsp; "
        f"<b>Analystenpotenzial:</b> "
        f"{_number(valuation.get('analyst_upside'), 1, ' %')}"
        f"<br/>"
        f"<b>Momentum:</b> "
        f"3M {_number(opportunity.get('momentum_3m'), 1, ' %')} · "
        f"6M {_number(opportunity.get('momentum_6m'), 1, ' %')} · "
        f"12M {_number(opportunity.get('momentum_12m'), 1, ' %')}"
    )

    story.append(
        _opportunity_subcards(
            blocks,
            opportunity.get("entry_setup"),
            styles,
        )
    )
    story.append(Spacer(1, 2 * mm))

    opportunity_box = _section_box_two_columns(
        "Bewertung · Technik · Einstieg",
        opportunity_text,
        _text(opportunity.get("explanation")),
        PURPLE,
        styles,
    )
    opportunity_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PURPLE_LIGHT),
            ]
        )
    )
    story.append(opportunity_box)

    # 3 · Dividendenstrategie

    story.append(
        Paragraph(
            "3 · Dividendenstrategie",
            styles["section"],
        )
    )

    dividend_text = (
        f"<font size='12'><b>Dividendenrendite: "
        f"{_number(dividend.get('yield'), 1, ' %')}</b></font>"
        f"<br/>"
        f"<b>Score:</b> "
        f"{_score(dividend.get('score'), 15)}"
        f"<br/><br/>"
        f"<b>Rendite:</b> "
        f"{_number(dividend.get('yield_points'), 1)} / 5"
        f" &nbsp;&nbsp; "
        f"<b>Ausschüttung:</b> "
        f"{_number(dividend.get('payout_points'), 1)} / 3"
        f"<br/>"
        f"<b>Wachstum:</b> "
        f"{_number(dividend.get('growth_points'), 1)} / 2"
        f" &nbsp;&nbsp; "
        f"<b>Kontinuität:</b> "
        f"{_number(dividend.get('continuity_points'), 1)} / 2"
        f" &nbsp;&nbsp; "
        f"<b>Kapitalallokation:</b> "
        f"{_number(dividend.get('allocation_points'), 1)} / 3"
    )

    dividend_box = _section_box(
        "Ausschüttung & Kapitalallokation",
        dividend_text,
        BLUE,
        styles,
    )
    dividend_box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BLUE_LIGHT),
            ]
        )
    )
    story.append(dividend_box)

    # Abschließendes InRA-Fazit

    story.append(
        Paragraph(
            "InRA-Fazit",
            styles["section"],
        )
    )

    story.append(
        _inra_fazit_box(
            _inra_summary_text(report.get("inra_summary")),
            styles,
        )
    )

    story.append(Spacer(1, 1.5 * mm))

    story.append(
        Paragraph(
            (
                "<b>Hinweis:</b> InRA ist ein Research-Werkzeug. "
                "Die dargestellten Scores, Einschätzungen und "
                "Analysen stellen keine Anlageberatung oder "
                "Kauf-/Verkaufsempfehlung dar. Daten können "
                "unvollständig oder zeitverzögert sein."
            ),
            styles["small"],
        )
    )

    document.build(story)

    return buffer.getvalue()
