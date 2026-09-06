import html
from typing import Optional

import streamlit as st

from utils.fundamental_interpreter import (
    interpret_debt_equity,
    interpret_cash_to_debt,
    interpret_ocf_to_debt,
    interpret_net_margin,
    interpret_operating_margin,
    interpret_revenue_growth,
    interpret_roe,
)
from utils.investment_summary import create_investment_summary
from modules.quality_score import calculate_profitability_breakdown


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

    if value >= 10:
        return {
            "level": "good",
            "label": "Stark",
        }

    if value >= 0:
        return {
            "level": "solid",
            "label": "Solide",
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
    result,
) -> str:
    if result is None or isinstance(result, str):
        return "⚪"

    level = result.get("level")

    if level in ("excellent", "good"):
        return "🟢"

    if level == "solid":
        return "🟡"

    if level == "neutral":
        return "⚪"

    return "🔴"


def _rating_label(
    result,
) -> str:
    if result is None:
        return "Keine Einordnung"

    if isinstance(result, str):
        return result

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
    profitability_breakdown = calculate_profitability_breakdown(
        data.get("Kapitalrendite"),
        data.get("Eigenkapitalrendite"),
        data.get("Sektor"),
        data.get("Branche"),
    )

    roe = data.get("Eigenkapitalrendite")
    margin = data.get("Nettomarge")
    operating_margin = data.get("Operative Marge")
    revenue_growth = data.get("Umsatzwachstum")
    earnings_growth = data.get("Gewinnwachstum")
    revenue_growth_scored = data.get("Umsatzwachstum Jahresabschluss")
    earnings_growth_scored = data.get("Gewinnwachstum Jahresabschluss")
    debt = data.get("Verschuldungsgrad")
    total_cash = data.get("Gesamtliquidität")
    total_debt = data.get("Gesamtverschuldung")
    operating_cashflow = data.get("Operativer Cashflow")
    cash_to_debt_ratio = (
        total_cash / total_debt
        if total_cash is not None and total_debt not in (None, 0)
        else None
    )

    ocf_to_debt_ratio = (
        operating_cashflow / total_debt
        if operating_cashflow is not None and total_debt not in (None, 0)
        else None
    )

    with st.expander(
         f"Warum {quality_score} von 100 Punkten?"
    ):
        _render_section_header(
            "💰 Profitabilität",
            breakdown["Profitabilität"],
            40,
        )

        return_on_capital = data.get("Kapitalrendite")

        _render_metric_row(
            "Kapitalrendite (ROC)",
            _format_percentage(return_on_capital),
            {
                "level": "neutral",
                "label": (
                    f"{profitability_breakdown['roc_score']:.0f} / "
                    f"{profitability_breakdown['roc_max']:.0f}"
                ),
            },
            (
                "Misst die Rendite auf das im operativen Geschäft "
                "eingesetzte Kapital. Sie ist die wichtigste "
                "Profitabilitätskennzahl im Quality Score und "
                "fließt mit bis zu 25 von 40 Punkten ein. "
                "Bewertet werden sowohl das absolute Niveau als "
                "auch der Vergleich mit der Branche."
            ),
        )

        _render_metric_row(
            "ROE",
            _format_percentage(roe),
            {
                "level": "neutral",
                "label": (
                    f"{profitability_breakdown['roe_score']:.0f} / "
                    f"{profitability_breakdown['roe_max']:.0f}"
                ),
            },
            (
                "Eigenkapitalrendite: Zeigt, wie viel Gewinn "
                "mit dem eingesetzten Eigenkapital erzielt wird. "
                "Sie fließt mit bis zu 15 von 40 Punkten ein. "
                "Auch hier werden absolutes Niveau und "
                "Branchenvergleich berücksichtigt. Sehr hohe "
                "Werte können durch Verschuldung oder "
                "Aktienrückkäufe verzerrt sein."
            ),
        )

        _render_metric_row(
            "Nettomarge",
            _format_percentage(margin),
            "Diagnosekennzahl",
            (
                "Anteil des Umsatzes, der nach sämtlichen "
                "Kosten als Gewinn verbleibt. Die Kennzahl "
                "liefert zusätzlichen Kontext, fließt aber "
                "nicht mehr separat in den Profitabilitätsscore ein."
            ),
        )

        _render_metric_row(
            "Operative Marge",
            _format_percentage(operating_margin),
            "Diagnosekennzahl",
            (
                "Anteil des Umsatzes, der aus dem operativen "
                "Kerngeschäft als operativer Gewinn verbleibt. "
                "Sie wird zur Einordnung angezeigt, erhält aber "
                "keine eigenen Punkte, da die operative "
                "Ertragskraft bereits in der Kapitalrendite "
                "enthalten ist."
            ),
        )

        _render_section_header(
            "📈 Wachstum",
            breakdown["Wachstum"],
            35,
        )

        _render_metric_row(
            "Umsatzwachstum",
            _format_percentage(revenue_growth_scored),
            interpret_revenue_growth(
                revenue_growth_scored
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
            _format_percentage(earnings_growth_scored),
            _interpret_earnings_growth(
                earnings_growth_scored
            ),
            (
                "Aktuell gemeldetes Gewinnwachstum. "
                "Diese Kennzahl kann deutlich stärker "
                "schwanken als das Umsatzwachstum."
            ),
        )

        if (
            (
                data.get("Extremer Umsatzsprung")
                or data.get("Gewinn Vorzeichenwechsel")
            )
            and not data.get("Research Bereinigung aktiv")
        ):
            st.warning(
                "Außergewöhnliche Wachstumshistorie erkannt. "
                "Starke Veränderungen können reales strukturelles Wachstum "
                "abbilden oder durch Sondereffekte wie Akquisitionen, "
                "Bilanzierung oder Restrukturierungen beeinflusst sein. "
                "Eine zusätzliche fachliche Einordnung ist sinnvoll."
            )

        if data.get("Research Bereinigung aktiv"):
            for adjustment in data.get("Research Bereinigungen", []):
                original_value = adjustment.get("Originalwert")
                replacement_value = adjustment.get("Ersatzwert")

                value_text = ""

                if (
                    original_value is not None
                    and replacement_value is not None
                ):
                    value_text = (
                        f" Originalwert: {original_value:.1f} %. "
                        f"Research-Wert: {replacement_value:.1f} %."
                    )

                source = adjustment.get("Quelle")
                date = adjustment.get("Stand")

                st.info(
                    f"Research-Hinweis: "
                    f"{adjustment.get('Kennzahl')} · "
                    f"{adjustment.get('Status')}."
                    f"{value_text} "
                    f"{adjustment.get('Begründung')}"
                )

                if source:
                    source_text = f"Quelle: {source}"

                    if date:
                        source_text += f" ({date})"

                    st.caption(source_text)

        st.caption(
            "Growth V2 bewertet Umsatz- und Gewinnentwicklung "
            "auf Basis der verfügbaren Jahresabschluss- und "
            "Mehrjahresdaten."
        )

        st.divider()

        _render_section_header(
            "🏦 Bilanz",
            breakdown["Bilanz"],
            25,
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

        _render_metric_row(
            "Cash / Debt",
            f"{cash_to_debt_ratio:.2f}" if cash_to_debt_ratio is not None else "–",
            interpret_cash_to_debt(cash_to_debt_ratio),
            (
                "Verhältnis von liquiden Mitteln zur Gesamtverschuldung. "
                "Je höher der Wert, desto größer der finanzielle Puffer "
                "gegenüber den bestehenden Schulden."
            ),
        )

        _render_metric_row(
            "Operativer Cashflow / Debt",
            f"{ocf_to_debt_ratio:.2f}" if ocf_to_debt_ratio is not None else "–",
            interpret_ocf_to_debt(ocf_to_debt_ratio),
            (
                "Verhältnis des operativen Cashflows zur Gesamtverschuldung. "
                "Zeigt, wie stark die Verschuldung durch die laufende "
                "operative Mittelgenerierung getragen wird."
            ),
        )

        st.caption(
            "Kapitalintensive Geschäftsmodelle benötigen "
            "später einen stärkeren Branchenkontext."
        )

        st.divider()

        st.markdown(
            f"**Gesamt: {quality_score} von 100 Punkten**"
        )