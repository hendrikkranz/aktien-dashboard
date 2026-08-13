import html
from typing import Optional

import streamlit as st

from utils.fundamental_interpreter import (
    interpret_debt_equity,
    interpret_dividend_yield,
    interpret_net_margin,
    interpret_revenue_growth,
    interpret_roe,
)
from utils.investment_summary import create_investment_summary


def _quality_rating(score: int) -> tuple:
    if score >= 80:
        return "Sehr hoch", "🟢", "#2EAD7B"

    if score >= 60:
        return "Solide", "🟡", "#D9A514"

    return "Schwach", "🔴", "#D9534F"


def _score_icon(score: int, maximum: int) -> str:
    ratio = score / maximum if maximum else 0

    if ratio >= 0.8:
        return "🟢"

    if ratio >= 0.5:
        return "🟡"

    return "🔴"


def _format_percentage(
    value: Optional[float],
) -> str:
    if value is None:
        return "–"

    return f"{value:.1f} %"


def _format_number(
    value: Optional[float],
) -> str:
    if value is None:
        return "–"

    return f"{value:.1f}"


def _interpret_earnings_growth(
    value: Optional[float],
) -> Optional[dict]:
    if value is None:
        return None

    if value >= 20:
        return {
            "level": "excellent",
            "label": "Sehr stark",
        }

    if value >= 8:
        return {
            "level": "good",
            "label": "Stark",
        }

    if value >= 0:
        return {
            "level": "solid",
            "label": "Positiv",
        }

    if value >= -10:
        return {
            "level": "weak",
            "label": "Schwach",
        }

    return {
        "level": "poor",
        "label": "Sehr schwach",
    }


def _rating_icon(
    result: Optional[dict],
) -> str:
    if result is None:
        return "⚪"

    level = result.get("level")

    if level in ("excellent", "good"):
        return "🟢"

    if level == "solid":
        return "🟡"

    return "🔴"


def _rating_label(
    result: Optional[dict],
) -> str:
    if result is None:
        return "Keine Einordnung"

    if result.get("label"):
        return str(result["label"])

    mapping = {
        "excellent": "Exzellent",
        "good": "Stark",
        "solid": "Solide",
        "weak": "Schwach",
        "poor": "Kritisch",
        "low": "Niedrig",
    }

    return mapping.get(
        result.get("level"),
        "Keine Einordnung",
    )


def _render_section_header(
    title: str,
    score: int,
    maximum: int,
) -> None:
    icon = _score_icon(score, maximum)

    st.markdown(
        f"##### {icon} {title}"
        f"<span style='float:right'>{score} / {maximum}</span>",
        unsafe_allow_html=True,
    )


def _render_metric_row(
    label: str,
    value: str,
    result: Optional[dict],
    help_text: str,
) -> None:
    safe_label = html.escape(label)
    safe_value = html.escape(value)
    safe_help = html.escape(
        help_text,
        quote=True,
    )

    icon = _rating_icon(result)
    rating = html.escape(
        _rating_label(result)
    )

    row = f"""
<div
    title="{safe_help}"
    style="
        display:grid;
        grid-template-columns:minmax(150px, 1fr) 120px 150px;
        gap:16px;
        align-items:center;
        padding:10px 0;
        border-bottom:1px solid #30363d;
    "
>
    <div style="
        color:#c9d1d9;
        font-size:14px;
        font-weight:600;
    ">
        {safe_label} ⓘ
    </div>

    <div style="
        color:white;
        font-size:17px;
        font-weight:700;
        text-align:right;
    ">
        {safe_value}
    </div>

    <div style="
        color:#d0d7de;
        font-size:14px;
        font-weight:600;
        white-space:nowrap;
        text-align:right;
    ">
        {icon} {rating}
    </div>
</div>
"""

    st.html(row)


def render_quality_section(data: dict) -> None:
    quality_score = data["Unternehmensqualität"]
    rating, icon, border = _quality_rating(
        quality_score
    )

    summary = html.escape(
        create_investment_summary(data)
    )

    card = f"""
<div style="
    background:#1b1f27;
    border-left:6px solid {border};
    border-radius:12px;
    padding:22px 24px;
    margin:10px 0 22px 0;
">
    <div style="
        color:#8b949e;
        font-size:12px;
        font-weight:700;
        text-transform:uppercase;
        letter-spacing:1px;
    ">
        Unternehmensqualität
    </div>

    <div style="
        color:white;
        font-size:32px;
        font-weight:700;
        margin-top:10px;
    ">
        {quality_score} / 100
    </div>

    <div style="
        color:#d0d7de;
        font-size:15px;
        font-weight:600;
        margin-top:5px;
    ">
        {icon} {rating}
    </div>

    <div style="
        color:#c9d1d9;
        font-size:15px;
        line-height:1.55;
        margin-top:14px;
        max-width:1000px;
    ">
        {summary}
    </div>
</div>
"""

    st.html(card)

    breakdown = data["Quality Breakdown"]

    roe = data.get("Eigenkapitalrendite")
    margin = data.get("Nettomarge")
    revenue_growth = data.get("Umsatzwachstum")
    earnings_growth = data.get("Gewinnwachstum")
    debt = data.get("Verschuldungsgrad")
    dividend_yield = data.get("Dividendenrendite")

    with st.expander(
         f"Warum {quality_score} von 100 Punkten?"
    ):
        _render_section_header(
            "💰 Profitabilität",
            breakdown["Profitabilität"],
            35,
        )

        _render_metric_row(
            "ROE",
            _format_percentage(roe),
            interpret_roe(roe),
            (
                "Eigenkapitalrendite: Zeigt, wie viel Gewinn "
                "mit dem eingesetzten Eigenkapital erzielt wird. "
                "Sehr hohe Werte können durch Verschuldung oder "
                "Aktienrückkäufe verzerrt sein."
            ),
        )

        _render_metric_row(
            "Nettomarge",
            _format_percentage(margin),
            interpret_net_margin(margin),
            (
                "Anteil des Umsatzes, der nach sämtlichen "
                "Kosten als Gewinn verbleibt. Die Einordnung "
                "ist stark branchenabhängig."
            ),
        )

        st.divider()

        _render_section_header(
            "📈 Wachstum",
            breakdown["Wachstum"],
            30,
        )

        _render_metric_row(
            "Umsatzwachstum",
            _format_percentage(revenue_growth),
            interpret_revenue_growth(
                revenue_growth
            ),
            (
                "Aktuell gemeldetes Umsatzwachstum. "
                "Eine einzelne Kennzahl kann durch "
                "Basiseffekte oder zyklische Schwankungen "
                "verzerrt sein."
            ),
        )

        _render_metric_row(
            "Gewinnwachstum",
            _format_percentage(earnings_growth),
            _interpret_earnings_growth(
                earnings_growth
            ),
            (
                "Aktuell gemeldetes Gewinnwachstum. "
                "Diese Kennzahl kann deutlich stärker "
                "schwanken als das Umsatzwachstum."
            ),
        )

        st.caption(
            "Der Wachstumsscore ist noch V0.1. "
            "Später fließen mehrere Kennzahlen und "
            "mehrjährige Trends ein."
        )

        st.divider()

        _render_section_header(
            "🏦 Bilanz",
            breakdown["Bilanz"],
            20,
        )

        _render_metric_row(
            "Debt / Equity",
            _format_number(debt),
            interpret_debt_equity(debt),
            (
                "Verhältnis von Schulden zu Eigenkapital. "
                "Die Einordnung erfolgt derzeit nach "
                "allgemeinen Schwellen und noch nicht "
                "relativ zur Branche."
            ),
        )

        st.caption(
            "Kapitalintensive Geschäftsmodelle benötigen "
            "später einen stärkeren Branchenkontext."
        )

        st.divider()

        _render_section_header(
            "💎 Dividendenqualität",
            breakdown["Dividende"],
            15,
        )

        _render_metric_row(
            "Dividendenrendite",
            _format_percentage(dividend_yield),
            interpret_dividend_yield(
                dividend_yield
            ),
            (
                "Jährliche Dividende im Verhältnis zum "
                "Aktienkurs. Die Rendite allein sagt noch "
                "nichts über Sicherheit, Ausschüttungsquote "
                "oder Dividendenwachstum aus."
            ),
        )

        st.divider()

        st.markdown(
            f"**Gesamt: {quality_score} von 100 Punkten**"
        )