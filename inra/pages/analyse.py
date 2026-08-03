import html

import streamlit as st

from utils.investment_summary import create_investment_summary
from utils.market_data import load_company_snapshot
from components.key_metrics import render_key_metrics
from components.quality_section import render_quality_section


def score_icon(score: int, maximum: int) -> str:
    ratio = score / maximum if maximum else 0

    if ratio >= 0.8:
        return "🟢"
    if ratio >= 0.5:
        return "🟡"
    return "🔴"


def render_subscore(
    column,
    label: str,
    score: int,
    maximum: int,
    explanation: str,
) -> None:
    safe_explanation = html.escape(explanation, quote=True)
    icon = score_icon(score, maximum)

    with column:
        st.markdown(
            f"""
            <div title="{safe_explanation}">
                <div style="
                    font-size: 0.82rem;
                    font-weight: 600;
                    white-space: nowrap;
                ">
                    {icon} {label} ⓘ
                </div>
                <div style="
                    font-size: 1.45rem;
                    margin-top: 0.25rem;
                    white-space: nowrap;
                ">
                    {score} / {maximum}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_plus(column) -> None:
    with column:
        st.markdown(
            """
            <div style="
                color:#666;
                font-size:0.95rem;
                text-align:center;
                padding-top:1.05rem;
                font-weight:300;
            ">
                +
            </div>
            """,
            unsafe_allow_html=True,
        )


st.title("Analyse")
st.caption("Investmententscheidung auf einen Blick")

ticker = st.text_input(
    "Ticker",
    value="MSFT",
    placeholder="z. B. MSFT",
).strip().upper()

if ticker:
    data = load_company_snapshot(ticker)

    st.header(data["Name"])

    header_details = [
        data["Ticker"],
        data["Währung"],
        data.get("Land"),
        data.get("Sektor"),
        data.get("Branche"),
    ]

    st.caption(
        " • ".join(
            str(value)
            for value in header_details
            if value
        )
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Kurs",
            f'{data["Kurs"]:.2f} {data["Währung"]}'
            if data["Kurs"] is not None
            else "Keine Daten",
        )

    with col2:
        st.metric(
            "Dividendenrendite",
            f'{data["Dividendenrendite"]:.2f} %'
            if data["Dividendenrendite"] is not None
            else "Keine Dividende",
            help=(
                "Jährliche Dividende im Verhältnis zum aktuellen Aktienkurs. "
                "Eine hohe Rendite ist nicht automatisch positiv, da sie auch "
                "durch einen stark gefallenen Aktienkurs entstehen kann."
            ),
        )

    with col3:
        st.metric(
            "Potenzial",
            f'{data["Analystenpotenzial"]:.1f} %'
            if data["Analystenpotenzial"] is not None
            else "Keine Daten",
            help=(
                "Prozentualer Abstand zwischen aktuellem Kurs und durchschnittlichem "
                "Analystenziel. Ein positiver Wert bedeutet rechnerisches "
                "Aufwärtspotenzial. Die Kennzahl ist nur eine Orientierung."
            ),
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "KGV",
            f'{data["KGV"]:.1f}'
            if data["KGV"] is not None
            else "Keine Daten",
            help=(
                "Kurs-Gewinn-Verhältnis auf Basis der zuletzt erzielten Gewinne. "
                "Die Einordnung hängt stark von Branche, Wachstum und "
                "Unternehmensqualität ab."
            ),
        )

    with col5:
        st.metric(
            "Forward KGV",
            f'{data["Forward KGV"]:.1f}'
            if data["Forward KGV"] is not None
            else "Keine Daten",
            help=(
                "Kurs-Gewinn-Verhältnis auf Basis der erwarteten zukünftigen Gewinne. "
                "Die Kennzahl beruht auf Prognosen und ist daher unsicherer."
            ),
        )

    with col6:
        st.metric(
            "Analystenziel",
            f'{data["Analystenziel"]:.2f} {data["Währung"]}'
            if data["Analystenziel"] is not None
            else "Keine Daten",
            help=(
                "Durchschnittliches Kursziel der erfassten Analysten. "
                "Kursziele können sich nach neuen Zahlen oder Erwartungen "
                "schnell verändern."
            ),
        )

    st.divider()

    st.subheader(
        "Kaufchance",
        help=(
            "Bewertet die Attraktivität der Aktie zum aktuellen Zeitpunkt. "
            "Berücksichtigt werden aktuell Analystenpotenzial, Bewertung über "
            "das Forward-KGV und Dividendenrendite."
        ),
    )

    buy_score = data["Kaufchance"]

    if buy_score >= 80:
        rating = "🟢 Kaufen"
        rating_explanation = (
            "Der aktuelle Einstieg erscheint attraktiv. Risiken und die eigene "
            "Anlagestrategie sollten dennoch geprüft werden."
        )
    elif buy_score >= 50:
        rating = "🟡 Beobachten"
        rating_explanation = (
            "Die Aktie ist interessant, aber das Chancen-Risiko-Verhältnis "
            "ist aktuell noch nicht eindeutig genug."
        )
    else:
        rating = "🔴 Abwarten"
        rating_explanation = (
            "Der aktuelle Einstieg erscheint auf Basis der berücksichtigten "
            "Kennzahlen noch nicht attraktiv genug."
        )

    st.metric(rating, f"{buy_score} / 100")
    st.caption(rating_explanation)

    reasons = []

    if (
        data["Analystenpotenzial"] is not None
        and data["Analystenpotenzial"] >= 20
    ):
        reasons.append("✅ Hohes Analystenpotenzial")

    if (
        data["Forward KGV"] is not None
        and data["Forward KGV"] <= 20
    ):
        reasons.append("✅ Attraktive Bewertung (Forward KGV)")

    if (
        data["Dividendenrendite"] is not None
        and data["Dividendenrendite"] >= 2
    ):
        reasons.append("✅ Solide Dividendenrendite")

    if reasons:
        st.info("\n".join(reasons))
    else:
        st.info("Noch keine besonderen Kaufsignale.")

    st.divider()

    render_quality_section(data)

    st.divider()

    st.markdown("### Kennzahlen")

    render_key_metrics(data)