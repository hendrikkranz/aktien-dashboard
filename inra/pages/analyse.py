import altair as alt
import streamlit as st

from components.investment_decision import (
    render_investment_decision,
)
from components.key_metrics import render_key_metrics
from components.opportunity_section import (
    render_opportunity_section,
)
from components.quality_section import render_quality_section
from utils.data_loader import find_ticker
from utils.market_data import (
    load_company_snapshot,
    load_price_history,
)


st.markdown(
    """
    <div style="
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #8b949e;
        margin-bottom: 0.15rem;
    ">
        Aktienanalyse
    </div>
    """,
    unsafe_allow_html=True,
)

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
                "Der Unternehmensname wurde nicht gefunden. "
                "Bitte den Yahoo-Ticker eingeben."
            )

if ticker:
    data = load_company_snapshot(ticker)

    st.session_state["last_analyzed_ticker"] = data["Ticker"]
    st.session_state["last_analyzed_name"] = data["Name"]

    st.title(data["Name"])

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

    render_investment_decision(data)

    st.divider()

    price_history = load_price_history(
        data["Ticker"],
        period="6mo",
    )

    if not price_history.empty:
        st.markdown("### Kursverlauf · 6 Monate")

        minimum_price = price_history["Schlusskurs"].min()
        maximum_price = price_history["Schlusskurs"].max()

        price_range = maximum_price - minimum_price

        if price_range > 0:
            axis_padding = price_range * 0.04
        else:
            axis_padding = maximum_price * 0.05

        y_min = max(
            0,
            minimum_price - axis_padding,
        )
        y_max = maximum_price + axis_padding

        chart = (
            alt.Chart(price_history)
            .mark_line()
            .encode(
                x=alt.X(
                    "Datum:T",
                    title=None,
                    axis=alt.Axis(
                        format="%d.%m.",
                        labelAngle=0,
                    ),
                ),
                y=alt.Y(
                    "Schlusskurs:Q",
                    title=None,
                    scale=alt.Scale(
                        domain=[y_min, y_max],
                        zero=False,
                        nice=False,
                    ),
                ),
                tooltip=[
                    alt.Tooltip(
                        "Datum:T",
                        title="Datum",
                        format="%d.%m.%Y",
                    ),
                    alt.Tooltip(
                        "Schlusskurs:Q",
                        title="Kurs",
                        format=".2f",
                    ),
                ],
            )
            .properties(
                height=280,
            )
        )

        st.altair_chart(
            chart,
            use_container_width=True,
        )
    else:
        st.info(
            "Für den Kursverlauf liegen derzeit keine Daten vor."
        )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Kurs",
            (
                f'{data["Kurs"]:.2f} {data["Währung"]}'
                if data["Kurs"] is not None
                else "Keine Daten"
            ),
        )

    with col2:
        st.metric(
            "Dividendenrendite",
            (
                f'{data["Dividendenrendite"]:.2f} %'
                if data["Dividendenrendite"] is not None
                else "Keine Dividende"
            ),
            help=(
                "Jährliche Dividende im Verhältnis zum aktuellen "
                "Aktienkurs. Renditen von etwa 2 bis 4 % gelten "
                "häufig als attraktiv. Sehr hohe Werte können auch "
                "durch einen stark gefallenen Kurs entstehen."
            ),
        )

    with col3:
        st.metric(
            "Potenzial",
            (
                f'{data["Analystenpotenzial"]:.1f} %'
                if data["Analystenpotenzial"] is not None
                else "Keine Daten"
            ),
            help=(
                "Prozentualer Abstand zwischen aktuellem Kurs und "
                "durchschnittlichem Analystenziel. Analystenziele "
                "sind nur eine Orientierung."
            ),
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "KGV",
            (
                f'{data["KGV"]:.1f}'
                if data["KGV"] is not None
                else "Keine Daten"
            ),
            help=(
                "Kurs-Gewinn-Verhältnis auf Basis der zuletzt "
                "erzielten Gewinne. Die Einordnung hängt von "
                "Branche, Wachstum und Unternehmensqualität ab."
            ),
        )

    with col5:
        st.metric(
            "Forward KGV",
            (
                f'{data["Forward KGV"]:.1f}'
                if data["Forward KGV"] is not None
                else "Keine Daten"
            ),
            help=(
                "Kurs-Gewinn-Verhältnis auf Basis der erwarteten "
                "zukünftigen Gewinne. Die Kennzahl beruht auf "
                "Prognosen."
            ),
        )

    with col6:
        st.metric(
            "Analystenziel",
            (
                f'{data["Analystenziel"]:.2f} '
                f'{data["Währung"]}'
                if data["Analystenziel"] is not None
                else "Keine Daten"
            ),
            help=(
                "Durchschnittliches Kursziel der erfassten "
                "Analysten. Kursziele können sich schnell ändern."
            ),
        )

    st.divider()

    render_opportunity_section(data)

    st.divider()

    render_quality_section(data)