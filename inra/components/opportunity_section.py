from typing import Optional

import streamlit as st


def _format_value(
    value: Optional[float],
    suffix: str = "",
) -> str:
    if value is None:
        return "Keine Daten"

    return f"{value:.1f}{suffix}"


def _render_opportunity_breakdown(data: dict) -> None:
    breakdown = data.get("Opportunity Breakdown", [])

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
    }

    explanations = {
        "Analystenpotenzial": (
            "Ab 20 % wird die volle Punktzahl vergeben, "
            "ab 10 % eine reduzierte Punktzahl."
        ),
        "Forward KGV": (
            "Bis 20 werden 35 Punkte vergeben. "
            "Bis 22 gibt es 30 Punkte, bis 25 noch 25 Punkte "
            "und bis 30 noch 15 Punkte."
        ),
        "Dividendenrendite": (
            "Ab 2 % wird die volle Punktzahl vergeben. "
            "Ab 1 % gibt es 15 Punkte, bei einer positiven "
            "Rendite unter 1 % noch 10 Punkte."
        ),
    }

    with st.expander("Warum diese Kaufchance?"):
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

        total = sum(
            item["Punkte"]
            for item in breakdown
        )

        st.divider()
        st.markdown(
            f"**Gesamt: {min(total, 100)} von 100 Punkten**"
        )


def render_opportunity_section(data: dict) -> None:
    buy_score = data["Kaufchance"]

    if buy_score >= 80:
        rating = "Kaufen"
        icon = "🟢"
        border = "#2EAD7B"
        explanation = (
            "Der aktuelle Einstieg erscheint attraktiv. "
            "Risiken und die eigene Anlagestrategie sollten "
            "dennoch geprüft werden."
        )
    elif buy_score >= 50:
        rating = "Beobachten"
        icon = "🟡"
        border = "#D9A514"
        explanation = (
            "Die Aktie ist interessant, aber das "
            "Chancen-Risiko-Verhältnis ist aktuell noch "
            "nicht eindeutig genug."
        )
    else:
        rating = "Abwarten"
        icon = "🔴"
        border = "#D9534F"
        explanation = (
            "Der aktuelle Einstieg erscheint auf Basis der "
            "berücksichtigten Kennzahlen noch nicht attraktiv genug."
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

    _render_opportunity_breakdown(data)