import streamlit as st


def render_investment_decision(data: dict) -> None:
    buy_score = data["Kaufchance"]
    quality_score = data["Unternehmensqualität"]

    if buy_score >= 80 and quality_score >= 70:
        title = "🟢 Kaufen"
        text = (
            "Die Aktie bietet derzeit einen attraktiven Einstieg "
            "und überzeugt gleichzeitig durch eine hohe "
            "Unternehmensqualität."
        )

    elif buy_score >= 60:
        title = "🟡 Beobachten"
        text = (
            "Die Aktie ist interessant, erfüllt derzeit aber "
            "noch nicht alle Voraussetzungen für eine klare "
            "Kaufempfehlung."
        )

    else:
        title = "🔴 Abwarten"
        text = (
            "Der aktuelle Einstieg erscheint momentan "
            "nicht attraktiv genug."
        )

    st.success(title)
    st.caption(text)