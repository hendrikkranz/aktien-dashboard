import streamlit as st

from components.key_metrics import render_key_metrics
from components.quality_section import render_quality_section
from utils.data_loader import find_ticker
from utils.market_data import load_company_snapshot


st.title("Analyse")
st.caption("Investmententscheidung auf einen Blick")

if "analyse_ticker" in st.session_state:
    st.session_state["analyse_input"] = st.session_state.pop(
        "analyse_ticker"
    )
elif "analyse_input" not in st.session_state:
    st.session_state["analyse_input"] = "MSFT"

search_text = st.text_input(
    "Aktie oder Ticker",
    key="analyse_input",
    placeholder="z. B. Microsoft, Telekom, MSFT oder DTE.DE",
).strip()

ticker = None

if search_text:
    ticker = find_ticker(search_text)

    if ticker is None:
        direct_ticker = search_text.upper()

        if " " not in direct_ticker:
            ticker = direct_ticker
        else:
            st.warning(
                "Der Unternehmensname wurde im Research-Universum "
                "nicht gefunden. Bitte den Yahoo-Ticker eingeben."
            )

if ticker:
    data = load_company_snapshot(ticker)

    st.session_state["last_analyzed_ticker"] = data["Ticker"]
    st.session_state["last_analyzed_name"] = data["Name"]

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
                "Orientierung: Renditen von etwa 2 bis 4 % gelten häufig als "
                "attraktiv. Sehr hohe Werte können jedoch auch durch einen "
                "stark gefallenen Aktienkurs entstehen."
            ),
        )

    with col3:
        st.metric(
            "Potenzial",
            f'{data["Analystenpotenzial"]:.1f} %'
            if data["Analystenpotenzial"] is not None
            else "Keine Daten",
            help=(
                "Prozentualer Abstand zwischen aktuellem Kurs und "
                "durchschnittlichem Analystenziel. Ein positiver Wert bedeutet "
                "rechnerisches Aufwärtspotenzial. Analystenziele sind jedoch "
                "nur eine Orientierung und können sich schnell verändern."
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
                "Kurs-Gewinn-Verhältnis auf Basis der zuletzt erzielten "
                "Gewinne. Niedrigere Werte können auf eine günstigere "
                "Bewertung hindeuten. Die Einordnung hängt jedoch stark von "
                "Branche, Wachstum und Unternehmensqualität ab."
            ),
        )

    with col5:
        st.metric(
            "Forward KGV",
            f'{data["Forward KGV"]:.1f}'
            if data["Forward KGV"] is not None
            else "Keine Daten",
            help=(
                "Kurs-Gewinn-Verhältnis auf Basis der erwarteten zukünftigen "
                "Gewinne. Die Kennzahl beruht auf Prognosen und ist deshalb "
                "unsicherer als das historische KGV."
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
                "Kursziele können sich nach Unternehmenszahlen oder "
                "veränderten Erwartungen schnell ändern."
            ),
        )

    st.divider()

    st.subheader(
        "Kaufchance",
        help=(
            "Bewertet die Attraktivität der Aktie zum aktuellen Zeitpunkt. "
            "Berücksichtigt werden derzeit Analystenpotenzial, Bewertung über "
            "das Forward-KGV und Dividendenrendite."
        ),
    )

    buy_score = data["Kaufchance"]

    if buy_score >= 80:
        rating = "🟢 Kaufen"
        rating_explanation = (
            "Der aktuelle Einstieg erscheint attraktiv. Risiken und die "
            "eigene Anlagestrategie sollten dennoch geprüft werden."
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