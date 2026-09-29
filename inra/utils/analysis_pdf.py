from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.shapes import Drawing, String
from reportlab.platypus import (
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
            fontSize=11,
            leading=13,
            textColor=DARK,
            spaceBefore=3 * mm,
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
            leading=12,
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
            fontSize=13,
            leading=16,
            textColor=DARK,
        ),
    }


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

    story.append(
        Paragraph(
            "InRA · Investment Research Assistant",
            styles["brand"],
        )
    )

    story.append(
        Paragraph(
            _text(company.get("name"), "Aktienanalyse"),
            styles["company"],
        )
    )

    meta = (
        f"{_text(company.get('ticker'))} · "
        f"{_text(company.get('exchange'))} · "
        f"{_text(company.get('currency'))} · "
        f"{_text(company.get('country'))}<br/>"
        f"{_text(company.get('sector'))} · "
        f"{_text(company.get('industry'))}"
    )

    story.append(Paragraph(meta, styles["meta"]))
    story.append(Spacer(1, 4 * mm))

    decision_table = Table(
        [
            [
                Paragraph(
                    _text(decision.get("title")),
                    styles["decision"],
                ),
                Paragraph(
                    _score(decision.get("score"), 100),
                    styles["score"],
                ),
            ],
            [
                Paragraph(
                    _text(decision.get("text")),
                    styles["body"],
                ),
                "",
            ],
        ],
        colWidths=[140 * mm, 38 * mm],
    )

    decision_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.7, BORDER),
                ("LINEBEFORE", (0, 0), (0, -1), 4, GREEN),
                ("SPAN", (1, 0), (1, 1)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )

    story.append(decision_table)

    story.append(
        Paragraph("InRA-Fazit", styles["section"])
    )

    story.append(
        _section_box(
            "Investment Case",
            _inra_summary_text(report.get("inra_summary")),
            GREEN,
            styles,
        )
    )

    story.append(
        Paragraph("Bewertungen", styles["section"])
    )

    score_table = Table(
        [
            [
                _score_card(
                    "Unternehmensqualität",
                    scores.get("quality"),
                    100,
                    GREEN,
                    styles,
                ),
                _score_card(
                    "Kaufchance",
                    scores.get("opportunity"),
                    100,
                    PURPLE,
                    styles,
                ),
                _score_card(
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
                ("LEFTPADDING", (0, 0), (-1, -1), 1.5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ]
        )
    )

    story.append(score_table)

    price_history = report.get("price_history") or []

    if price_history:
        story.append(
            Paragraph("Kursverlauf", styles["section"])
        )
        story.append(
            _price_chart(
                price_history,
                currency=company.get("currency"),
            )
        )

    story.append(
        Paragraph("Kaufchance", styles["section"])
    )

    blocks = opportunity.get("blocks") or {}

    opportunity_text = (
        f"<b>Kursbewertung:</b> "
        f"{_number(blocks.get('fundamental_points'), 1)} / 45"
        f"<br/>"
        f"<b>Technische Verfassung:</b> "
        f"{_number(blocks.get('technical_points'), 1)} / 25"
        f"<br/>"
        f"<b>Entry Setup:</b> "
        f"{_number(blocks.get('entry_points'), 1)} / 30"
        f" · {_text(opportunity.get('entry_setup'))}"
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
        _section_box(
            "Bewertung · Technik · Einstieg",
            opportunity_text,
            PURPLE,
            styles,
        )
    )

    story.append(PageBreak())

    story.append(
        Paragraph(
            "Unternehmensqualität",
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
            f"<b>{_text(name)}:</b> {_number(value, 1)} Punkte"
            for name, value in quality_breakdown.items()
        )
    )

    story.append(
        _section_box(
            "Qualitätsprofil",
            quality_text,
            GREEN,
            styles,
        )
    )

    story.append(
        Paragraph("Dividendenstrategie", styles["section"])
    )

    dividend_text = (
        f"<b>Score:</b> "
        f"{_score(dividend.get('score'), 15)}"
        f" &nbsp;&nbsp; "
        f"<b>Dividendenrendite:</b> "
        f"{_number(dividend.get('yield'), 1, ' %')}"
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

    story.append(
        _section_box(
            "Ausschüttung & Kapitalallokation",
            dividend_text,
            BLUE,
            styles,
        )
    )

    story.append(
        Paragraph("Aktuelle Entwicklungen", styles["section"])
    )

    story.append(
        _section_box(
            "Current Intelligence",
            _current_intelligence_text(current),
            ORANGE,
            styles,
        )
    )

    story.append(Spacer(1, 4 * mm))

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
