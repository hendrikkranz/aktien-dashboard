import altair as alt
import streamlit as st

from components.investment_decision import (
    render_investment_decision,
)
from components.dividend_section import (
    render_dividend_section,
)
from components.opportunity_section import (
    render_opportunity_section,
)
from components.quality_section import (
    render_quality_section,
)
from utils.data_loader import find_ticker
from utils.market_data import (
    load_company_snapshot,
    load_price_history,
)


def format_market_cap(value, currency):
    if value is None:
        return "Keine Daten"

    units = [
        (1_000_000_000_000, "Bio."),
        (1_000_000_000, "Mrd."),
        (1_000_000, "Mio."),
    ]

    for divisor, label in units:
        if value >= divisor:
            return (
                f"{value / divisor:.1f} "
                f"{label} {currency}"
            )

    return f"{value:,.0f} {currency}"


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

    if (
        data.get("Kurs") is None
        and data.get("Marktkapitalisierung") is None
        and data.get("Land") is None
        and data.get("Sektor") is None
        and data.get("Branche") is None
    ):
        st.warning(
            "Für diese Eingabe konnten keine belastbaren "
            "Börsendaten gefunden werden. Bitte Ticker oder "
            "ISIN prüfen."
        )
        st.stop()

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

    st.caption(
        "🏢 Marktkapitalisierung: "
        + format_market_cap(
            data.get("Marktkapitalisierung"),
            data.get("Währung"),
        )
    )

    col_title, col_period = st.columns([3, 2])

    with col_title:
        title_placeholder = st.empty()

    with col_period:
        period = st.segmented_control(
            "Zeitraum",
            options=["1M", "3M", "6M", "1J", "5J"],
            default="6M",
            label_visibility="collapsed",
        )

    period_map = {
        "1M": "1mo",
        "3M": "3mo",
        "6M": "6mo",
        "1J": "1y",
        "5J": "5y",
    }

    price_history = load_price_history(
        data["Ticker"],
        period=period_map[period],
    )

    if not price_history.empty:
        first_price = price_history["Schlusskurs"].iloc[0]
        last_price = price_history["Schlusskurs"].iloc[-1]

        performance = (
            ((last_price / first_price) - 1) * 100
            if first_price
            else 0
        )

        performance_icon = "🟢" if performance >= 0 else "🔴"

        title_placeholder.markdown(
            f"### Kursverlauf &nbsp; "
            f"<span style='font-size:0.78em;'>"
            f"{performance_icon} {performance:+.1f} %"
            f"</span>",
            unsafe_allow_html=True,
        )
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

        if period == "5J":
            x_axis = alt.Axis(
                format="%Y",
                tickMinStep=365 * 24 * 60 * 60 * 1000,
                labelAngle=0,
                grid=True,
                gridColor="#5b6575",
                gridOpacity=0.25,
            )
        elif period == "1J":
            x_axis = alt.Axis(
                format="%m/%Y",
                tickCount="month",
                labelAngle=0,
            )
        else:
            x_axis = alt.Axis(
                format="%d.%m.",
                labelAngle=0,
            )

        chart = (
            alt.Chart(price_history)
            .mark_line()
            .encode(
                x=alt.X(
                    "Datum:T",
                    title=None,
                    axis=x_axis,
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
            "Für den gewählten Zeitraum liegen keine Kursdaten vor."
        )

        st.divider()

    render_investment_decision(data)

    st.divider()

    render_quality_section(data)

    st.divider()

    render_dividend_section(data)

    st.divider()

    render_opportunity_section(data)