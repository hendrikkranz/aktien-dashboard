from typing import Optional

import streamlit as st

from utils.fundamental_interpreter import interpret_momentum


def _format_value(
    value: Optional[float],
    suffix: str = "",
) -> str:
    if value is None:
        return "Keine Daten"

    return f"{value:.1f}{suffix}"


def _format_momentum(
    value: Optional[float],
) -> str:
    if value is None:
        return "–"

    return f"{value:+.1f} %"


def _momentum_icon(
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


def _momentum_label(
    result: Optional[dict],
) -> str:
    if result is None:
        return "Keine Einordnung"

    mapping = {
        "excellent": "Sehr stark",
        "good": "Stark",
        "solid": "Positiv",
        "weak": "Schwach",
        "poor": "Sehr schwach",
    }

    return mapping.get(
        result.get("level"),
        "Keine Einordnung",
    )


def _render_opportunity_breakdown(
    data: dict,
    rating: str,
) -> None:

    breakdown = data.get(
        "Opportunity Breakdown",
        [],
    )

    values = {
        "Analystenpotenzial": _format_value(
            data.get("Analystenpotenzial"),
            " %",
        ),
        "Forward KGV": _format_value(
            data.get("Forward KGV"),
        ),
        "Dividendenrendite": _format_value(
            data.get("Dividendenrendite"),
            " %",
        ),
        "Abstand 52W-Hoch": _format_value(
            data.get("Abstand 52W Hoch"),
            " %",
        ),
    }

    explanations = {
        "Analystenpotenzial": (
            "Ab 20 % wird die volle Punktzahl vergeben, "
            "ab 10 % eine reduzierte Punktzahl."
        ),
        "Forward KGV": (
            "Bis 20 werden 35 Punkte vergeben. "
            "Bis 22 gibt es 30 Punkte, "
            "bis 25 noch 25 Punkte "
            "und bis 30 noch 15 Punkte."
        ),
        "Dividendenrendite": (
            "Ab 2 % wird die volle Punktzahl vergeben. "
            "Ab 1 % gibt es 15 Punkte, "
            "bei einer positiven Rendite "
            "unter 1 % noch 10 Punkte."
        ),
        "Abstand 52W-Hoch": (
            "Je näher der Kurs am 52-Wochen-Hoch liegt, "
            "desto mehr Punkte werden vergeben."
        ),
    }

    with st.expander(
        f"Warum {rating.lower()}?"
    ):

        st.markdown(
            "##### 💰 Fundamentale Bewertung"
        )

        for item in breakdown:

            criterion = item["Kriterium"]
            points = item["Punkte"]
            maximum = item["Maximum"]

            if points >= maximum:
                icon = "✅"
            elif points > 0:
                icon = "🟡"
            else:
                icon = "⚪"

            st.markdown(
                f"**{icon} {criterion}: "
                f"{points} von {maximum} Punkten**"
            )

            st.caption(
                f"Aktueller Wert: "
                f"{values.get(criterion, 'Keine Daten')}. "
                f"{explanations.get(criterion, '')}"
            )

        st.divider()

        st.markdown("##### 📊 Charttechnik"
        )

        st.markdown(
            "##### 📈 Momentum"
        )

        momentum_3m = data.get(
            "Momentum 3M"
        )
        momentum_6m = data.get(
            "Momentum 6M"
        )
        momentum_12m = data.get(
            "Momentum 12M"
        )

        momentum_3m_result = (
            interpret_momentum(
                momentum_3m
            )
        )
        momentum_6m_result = (
            interpret_momentum(
                momentum_6m
            )
        )
        momentum_12m_result = (
            interpret_momentum(
                momentum_12m
            )
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "3 Monate",
                _format_momentum(
                    momentum_3m
                ),
            )

            st.markdown(
                f"{_momentum_icon(momentum_3m_result)} "
                f"**{_momentum_label(momentum_3m_result)}**"
            )

        with c2:
            st.metric(
                "6 Monate",
                _format_momentum(
                    momentum_6m
                ),
            )

            st.markdown(
                f"{_momentum_icon(momentum_6m_result)} "
                f"**{_momentum_label(momentum_6m_result)}**"
            )

        with c3:
            st.metric(
                "12 Monate",
                _format_momentum(
                    momentum_12m
                ),
            )

            st.markdown(
                f"{_momentum_icon(momentum_12m_result)} "
                f"**{_momentum_label(momentum_12m_result)}**"
            )


        tech1, tech2 = st.columns(2)

        with tech1:
            st.metric(
                "52W-Hoch",
                (
                    f'{data["52W Hoch"]:.2f} {data["Währung"]}'
                    if data.get("52W Hoch") is not None
                    else "Keine Daten"
                ),
            )

        with tech2:
            st.metric(
                "Abstand 52W-Hoch",
                (
                    f'{data["Abstand 52W Hoch"]:+.1f} %'
                    if data.get("Abstand 52W Hoch") is not None
                    else "Keine Daten"
                ),
                help=(
                    "Abstand des aktuellen Kurses zum 52-Wochen-Hoch."
                ),
            )

        st.caption(
            "V0.1: Die Charttechnik wird derzeit noch nicht bewertet. "
            "In V2 fließen Trendkanal, Unterstützungen/Widerstände, "
            "CM MACD Refined und RSI in einen eigenen Charttechnik-Score ein."
        )

        total = sum(
            item["Punkte"]
            for item in breakdown
        )

        st.divider()

        st.markdown(
            f"**Aktueller Kaufchance-Score: {min(total,100)} von 100 Punkten**"
        )

def render_opportunity_section(
    data: dict,
) -> None:

    buy_score = data["Kaufchance"]

    if buy_score >= 80:
        rating = "Kaufen"
        icon = "🟢"
        border = "#2EAD7B"
        explanation = (
            "Der aktuelle Einstieg erscheint attraktiv. "
            "Risiken und die eigene Anlagestrategie "
            "sollten dennoch geprüft werden."
        )

    elif buy_score >= 50:
        rating = "Beobachten"
        icon = "🟡"
        border = "#D9A514"
        explanation = (
            "Die Aktie ist interessant, "
            "erfüllt derzeit aber noch nicht "
            "alle Voraussetzungen für "
            "eine klare Kaufempfehlung."
        )

    else:
        rating = "Abwarten"
        icon = "🔴"
        border = "#D9534F"
        explanation = (
            "Der aktuelle Einstieg erscheint "
            "momentan nicht attraktiv genug."
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
        Kaufchance
    </div>

    <div style="
        color:white;
        font-size:32px;
        font-weight:700;
        margin-top:10px;
    ">
        {buy_score} / 100
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
    ">
        {explanation}
    </div>
</div>
"""

    st.html(card)

    _render_opportunity_breakdown(
        data,
        rating,
    )