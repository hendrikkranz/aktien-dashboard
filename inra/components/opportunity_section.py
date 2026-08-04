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
    st.subheader(
        "Kaufchance",
        help=(
            "Bewertet die Attraktivität der Aktie zum aktuellen "
            "Zeitpunkt. Berücksichtigt werden derzeit "
            "Analystenpotenzial, Forward KGV und Dividendenrendite."
        ),
    )

    buy_score = data["Kaufchance"]

    if buy_score >= 80:
        rating = "🟢 Kaufen"
        explanation = (
            "Der aktuelle Einstieg erscheint attraktiv. "
            "Risiken und die eigene Anlagestrategie sollten "
            "dennoch geprüft werden."
        )
    elif buy_score >= 50:
        rating = "🟡 Beobachten"
        explanation = (
            "Die Aktie ist interessant, aber das "
            "Chancen-Risiko-Verhältnis ist aktuell noch "
            "nicht eindeutig genug."
        )
    else:
        rating = "🔴 Abwarten"
        explanation = (
            "Der aktuelle Einstieg erscheint auf Basis der "
            "berücksichtigten Kennzahlen noch nicht attraktiv genug."
        )

    st.metric(
        rating,
        f"{buy_score} / 100",
    )

    st.caption(explanation)

    _render_opportunity_breakdown(data)