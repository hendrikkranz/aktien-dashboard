from urllib.parse import urlparse

import altair as alt
import streamlit as st

from utils.company_localization import (
    localize_country,
    get_country_display,
    localize_industry,
    localize_sector,
)
from utils.company_portrait import get_company_portrait

from utils.current_intelligence import (
    apply_current_intelligence,
    get_current_intelligence,
)
from utils.analysis_report import build_analysis_report_data
from utils.analysis_pdf import build_analysis_pdf

from components.investment_decision import (
    render_investment_decision,
)
from components.analysis_overview import (
    render_analysis_overview,
)
from components.investment_decision import (
    render_inra_fazit_section,
)
from components.dividend_section import (
    render_dividend_section,
)
from components.opportunity_section import (
    render_current_intelligence_section,
    render_opportunity_section,
)
from components.quality_section import (
    render_quality_section,
)
from utils.data_loader import (
    add_stock_to_universe,
    find_ticker,
    is_ticker_in_universe,
    search_stock_candidates,
    update_stock_in_benchmark_cache,
)
from utils.market_data import (
    load_company_snapshot,
    load_price_history,
)


st.markdown(
    """
    <style>
    /* ============================================================
       InRA Redesign V1 · Analyse Design Foundation
       ============================================================ */

    /* Desktop-Arbeitsfläche:
       breit genug für Research, aber nicht grenzenlos auseinandergezogen */
    .stMainBlockContainer,
    .block-container {
        max-width: 1480px;
        padding-left: 2.2rem;
        padding-right: 2.2rem;
        padding-top: 2rem;
    }

    /* Grundfläche bewusst nicht rein schwarz */
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(
                circle at 50% -10%,
                rgba(55, 65, 81, 0.22) 0%,
                rgba(17, 24, 39, 0.08) 32%,
                rgba(9, 13, 20, 0) 58%
            ),
            #090d14;
    }

    /* Haupttypografie etwas klarer und kontrastreicher */
    [data-testid="stAppViewContainer"] h1,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3 {
        letter-spacing: -0.025em;
    }

    [data-testid="stAppViewContainer"] h1 {
        font-weight: 750;
    }

    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3 {
        font-weight: 700;
    }

    /* Drei Hauptbereiche 01–03 */
    [data-testid="stVerticalBlockBorderWrapper"]:has(
        .inra-main-section-marker
    ) {
        background: rgba(15, 23, 42, 0.38);
        border-color: rgba(148, 163, 184, 0.18);
        border-radius: 14px;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:has(
        .inra-main-section-marker
    ) > div {
        padding: 0.45rem 1.25rem 1.20rem 1.25rem;
    }

    /* Section-Header innerhalb der neuen Hauptcontainer */
    [data-testid="stVerticalBlockBorderWrapper"]:has(
        .inra-main-section-marker
    ) .inra-section-header {
        margin-top: 0.35rem;
    }

    /* Wiederverwendbare Bereichsüberschrift für 01–05 */
    .inra-section-header {
        margin-top: 0;
        margin-bottom: 1.35rem;
        padding: 0;
        border-bottom: none;
    }

    .inra-section-kicker {
        display: block;
        margin-bottom: 0.45rem;
        padding: 0;
        background: transparent;
        border: none;
        border-radius: 0;
        color: #f8fafc;
        font-size: 1.55rem;
        line-height: 1.2;
        font-weight: 760;
        letter-spacing: -0.025em;
        text-transform: uppercase;
        text-shadow:
            0 2px 2px rgba(0, 0, 0, 0.85),
            0 3px 7px rgba(0, 0, 0, 0.55),
            0 0 5px rgba(248, 250, 252, 0.55),
            0 0 12px rgba(203, 213, 225, 0.38),
            0 0 24px rgba(148, 163, 184, 0.22);
    }

    .inra-section-title {
        color: #94a3b8;
        font-size: 0.80rem;
        line-height: 1.3;
        font-weight: 800;
        letter-spacing: 0.10em;
        text-transform: uppercase;
    }

    .inra-section-subtitle {
        margin-top: 0.38rem;
        max-width: 850px;
        color: #94a3b8;
        font-size: 0.90rem;
        line-height: 1.5;
    }

    /* Analyse-Überblick: drei Säulen immer gleich hoch */
    div[data-testid="stHorizontalBlock"]:has(.inra-overview-card) {
        align-items: stretch;
    }

    div[data-testid="stHorizontalBlock"]:has(.inra-overview-card)
    > div[data-testid="stColumn"] {
        display: flex;
    }

    div[data-testid="stHorizontalBlock"]:has(.inra-overview-card)
    > div[data-testid="stColumn"]
    > div {
        width: 100%;
        display: flex;
    }

    div[data-testid="stHorizontalBlock"]:has(.inra-overview-card)
    .inra-overview-card {
        width: 100%;
        height: 100%;
        box-sizing: border-box;
    }

    /* Oberflächen für spätere Cards */
    .inra-surface {
        background:
            linear-gradient(
                145deg,
                rgba(31, 41, 55, 0.90),
                rgba(17, 24, 39, 0.96)
            );
        border: 1px solid rgba(148, 163, 184, 0.14);
        border-radius: 16px;
        box-shadow:
            0 12px 32px rgba(0, 0, 0, 0.20),
            inset 0 1px 0 rgba(255, 255, 255, 0.025);
    }

    /* Analyse: Trefferliste der Aktiensuche klar hervorheben */
    div[data-baseweb="popover"] ul {
        background: #f4f6f8 !important;
    }

    div[data-baseweb="popover"] li {
        color: #111827 !important;
        background: #f4f6f8 !important;
    }

    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="popover"] li[aria-selected="true"] {
        color: #111827 !important;
        background: #dbeafe !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
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
    st.session_state["analyse_input"] = (
        st.query_params.get("ticker")
        or st.session_state.get("last_analyzed_ticker")
        or "MSFT"
    )

st.markdown(
    """
    <style>
    div[data-testid="stTextInput"]:has(
        input[aria-label="Aktie oder Ticker"]
    ) input {
        min-height: 52px;
        font-size: 1.08rem;
        font-weight: 500;
    }

    div[data-testid="stTextInput"]:has(
        input[aria-label="Aktie oder Ticker"]
    ) div[data-baseweb="input"] {
        border: 1px solid rgba(255, 255, 255, 0.75);
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

search_text = st.text_input(
    "Aktie oder Ticker",
    key="analyse_input",
    placeholder="z. B. Microsoft, Telekom, MSFT oder DTE.DE",
).strip()

ticker = None

if search_text:
    candidates = search_stock_candidates(search_text)

    exact_candidates = [
        candidate
        for candidate in candidates
        if candidate["Ticker"].casefold() == search_text.casefold()
    ]

    explicit_exchange_ticker = "." in search_text

    if exact_candidates and explicit_exchange_ticker:
        ticker = exact_candidates[0]["Ticker"]

    elif len(candidates) == 1:
        ticker = candidates[0]["Ticker"]

    elif candidates:
        candidate_options = {
            (
                f'{candidate["Name"]} ({candidate["Ticker"]})'
                + (
                    f' · {candidate["Exchange"]}'
                    if candidate.get("Exchange")
                    else ""
                )
            ): candidate["Ticker"]
            for candidate in candidates
        }

        selected_candidate = st.selectbox(
            "Passende Aktie auswählen",
            options=list(candidate_options.keys()),
            key="analyse_search_candidate",
        )

        ticker = candidate_options[selected_candidate]

    else:
        ticker = find_ticker(search_text)

        if ticker is None:
            st.warning(
                "Keine passende Aktie gefunden. "
                "Bitte Unternehmensname oder Yahoo-Ticker prüfen."
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
    st.query_params["ticker"] = data["Ticker"]

    website = data.get("Website")
    logo_domain = None

    if website:
        logo_domain = urlparse(website).netloc.lower()
        if logo_domain.startswith("www."):
            logo_domain = logo_domain[4:]

    company_profile = [
        data.get("Sektor"),
        data.get("Branche"),
    ]
    company_profile_text = " · ".join(
        str(value)
        for value in company_profile
        if value
    )

    if logo_domain:
        logo_col, title_col, watchlist_col = st.columns(
            [0.055, 0.695, 0.25],
            gap="small",
            vertical_alignment="center",
        )
        with logo_col:
            st.markdown(
                "<div style='height: 6px;'></div>",
                unsafe_allow_html=True,
            )
            st.image(
                "https://www.google.com/s2/favicons"
                f"?domain={logo_domain}&sz=128",
                width=40,
            )
        with title_col:
            st.markdown(
                f"""
                <div style="display:flex; flex-direction:column; justify-content:center;">
                    <h1 style="margin:0; padding:0;">{data["Name"]}</h1>
                    {
                        f'<div style="margin-top:2px; color:#9ca3af; font-size:0.875rem;">{company_profile_text}</div>'
                        if company_profile_text
                        else ""
                    }
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        title_col, watchlist_col = st.columns(
            [0.75, 0.25],
            gap="small",
            vertical_alignment="center",
        )
        with title_col:
            st.markdown(
                f"""
                <div style="display:flex; flex-direction:column;">
                    <h1 style="margin:0; padding:0;">{data["Name"]}</h1>
                    {
                        f'<div style="margin-top:2px; color:#9ca3af; font-size:0.875rem;">{company_profile_text}</div>'
                        if company_profile_text
                        else ""
                    }
                </div>
                """,
                unsafe_allow_html=True,
            )

    header_details = [
        data["Ticker"],
        data.get("Börse"),
        data["Währung"],
        data.get("Land"),
        (
            "Market Cap: "
            + format_market_cap(
                data.get("Marktkapitalisierung"),
                data.get("Währung"),
            )
        ),
    ]


    watchlist_message = st.session_state.pop(
        "watchlist_message",
        None,
    )

    if watchlist_message:
        message_type, message_text = watchlist_message

        if message_type == "success":
            st.success(message_text)
        else:
            st.warning(message_text)

    if not is_ticker_in_universe(data["Ticker"]):
        with watchlist_col:
            if st.button(
                "➕ Zur Watchlist hinzufügen",
                key=f"add_to_watchlist_{data['Ticker']}",
                use_container_width=True,
            ):
                added = add_stock_to_universe(
                    name=data["Name"],
                    ticker=data["Ticker"],
                    sector=data.get("Sektor"),
                    industry=data.get("Branche"),
                    country=data.get("Land"),
                )

                if added:
                    try:
                        update_stock_in_benchmark_cache(
                            data["Ticker"]
                        )
                        st.session_state["watchlist_message"] = (
                            "success",
                            "Aktie wurde zur Watchlist hinzugefügt "
                            "und für den Scout aufbereitet.",
                        )
                    except Exception as error:
                        st.session_state["watchlist_message"] = (
                            "warning",
                            "Aktie wurde zur Watchlist hinzugefügt, "
                            "konnte aber noch nicht für den Scout "
                            f"aufbereitet werden: {error}",
                        )

                    st.rerun()

    meta_spacer, meta_col = st.columns([2.45, 2])

    with meta_col:
        st.markdown(
            f"""
            <div style="
                text-align:center;
                color:#9ca3af;
                font-size:0.875rem;
                margin-top:-22px;
                margin-bottom:2px;
                white-space:nowrap;
            ">
                {" · ".join(
                    str(value)
                    for value in header_details
                    if value
                )}
            </div>
            """,
            unsafe_allow_html=True,
        )

    chart_col, portrait_col = st.columns(
        [1, 1],
        gap="large",
        vertical_alignment="top",
    )

    with chart_col:
        chart_title_col, period_col = st.columns(
            [1.15, 1.85],
            vertical_alignment="center",
        )

        with chart_title_col:
            title_placeholder = st.empty()

        with period_col:
            period = st.segmented_control(
                "Zeitraum",
                options=["1M", "3M", "6M", "1J", "5J"],
                default="6M",
                label_visibility="collapsed",
                key="analysis_chart_period",
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

            performance_icon = (
                "🟢" if performance >= 0 else "🔴"
            )

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

            history_start = price_history["Datum"].min()
            history_end = price_history["Datum"].max()
            history_days = (
                history_end - history_start
            ).days

            if history_days >= 730:
                x_axis = alt.Axis(
                    format="%Y",
                    tickMinStep=365 * 24 * 60 * 60 * 1000,
                    labelAngle=0,
                    grid=True,
                    gridColor="#5b6575",
                    gridOpacity=0.25,
                )
            elif history_days >= 180:
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
                .properties(height=280)
            )

            st.altair_chart(
                chart,
                use_container_width=True,
            )

            requested_days = {
                "1M": 30,
                "3M": 90,
                "6M": 180,
                "1J": 365,
                "5J": 1825,
            }[period]

            if history_days < requested_days * 0.80:
                st.caption(
                    "ℹ️ Für diesen Titel ist nur eine kürzere "
                    "Kurshistorie verfügbar: "
                    f"{history_start:%d.%m.%Y} bis "
                    f"{history_end:%d.%m.%Y}."
                )
        else:
            title_placeholder.markdown("### Kursverlauf")
            st.info(
                "Für den gewählten Zeitraum liegen "
                "keine Kursdaten vor."
            )

    with portrait_col:
        portrait_sector = localize_sector(
            data.get("Sektor")
        )
        portrait_industry = localize_industry(
            data.get("Branche")
        )
        portrait_country = get_country_display(
            data.get("Land")
        )
        portrait_country_name = portrait_country["name"]
        portrait_country_flag = portrait_country["flag"]

        portrait = get_company_portrait(
            data.get("Ticker")
        )

        if portrait:
            portrait_description = (
                portrait.get("Kurzbeschreibung") or
                "Keine Kurzbeschreibung verfügbar."
            )
            portrait_core_business = (
                portrait.get("Kerngeschaeft") or []
            )
        else:
            portrait_description = (
                "Noch kein deutsches Unternehmensporträt "
                "gespeichert."
            )
            portrait_core_business = []

        portrait_core_text = (
            "<br>".join(portrait_core_business)
            if portrait_core_business
            else "Noch nicht verfügbar"
        )

        st.html(
            f"""
            <div style="
                min-height:322px;
                box-sizing:border-box;
                border:1px solid rgba(148,163,184,0.16);
                border-radius:14px;
                padding:22px 24px;
                background:
                    linear-gradient(
                        145deg,
                        rgba(31,41,55,0.70),
                        rgba(15,23,42,0.78)
                    );
            ">
                <div style="
                    color:#64748b;
                    font-size:0.70rem;
                    font-weight:800;
                    letter-spacing:0.14em;
                    margin-bottom:14px;
                ">
                    UNTERNEHMENSPORTRÄT
                </div>

                <div style="
                    color:#f8fafc;
                    font-size:1.05rem;
                    font-weight:800;
                    margin-bottom:8px;
                ">
                    Was macht {data["Name"]}?
                </div>

                <div style="
                    color:#9ca3af;
                    font-size:0.86rem;
                    line-height:1.55;
                    min-height:86px;
                ">
                    {portrait_description}
                </div>

                <div style="
                    border-top:1px solid rgba(148,163,184,0.14);
                    margin-top:14px;
                    padding-top:14px;
                    display:grid;
                    grid-template-columns:1fr 1fr;
                    gap:14px 20px;
                ">
                    <div>
                        <div style="
                            color:#64748b;
                            font-size:0.68rem;
                            font-weight:700;
                            text-transform:uppercase;
                        ">
                            Sektor
                        </div>
                        <div style="
                            color:#cbd5e1;
                            font-size:0.84rem;
                            margin-top:3px;
                        ">
                            {portrait_sector}
                        </div>
                    </div>

                    <div>
                        <div style="
                            color:#64748b;
                            font-size:0.68rem;
                            font-weight:700;
                            text-transform:uppercase;
                        ">
                            Branche
                        </div>
                        <div style="
                            color:#cbd5e1;
                            font-size:0.84rem;
                            margin-top:3px;
                        ">
                            {portrait_industry}
                        </div>
                    </div>

                    <div>
                        <div style="
                            color:#64748b;
                            font-size:0.68rem;
                            font-weight:700;
                            text-transform:uppercase;
                        ">
                            Sitz / Markt
                        </div>
                        <div style="
                            color:#cbd5e1;
                            font-size:0.84rem;
                            margin-top:3px;
                        ">
                            {portrait_country_name}
                            {
                                f'<div style="font-size:1.9rem; '
                                f'line-height:1; margin-top:5px;">'
                                f'{portrait_country_flag}</div>'
                                if portrait_country_flag
                                else ""
                            }
                        </div>
                    </div>

                    <div>
                        <div style="
                            color:#64748b;
                            font-size:0.68rem;
                            font-weight:700;
                            text-transform:uppercase;
                        ">
                            Kerngeschäft
                        </div>
                        <div style="
                            color:#cbd5e1;
                            font-size:0.84rem;
                            margin-top:3px;
                        ">
                            {portrait_core_text}
                        </div>
                    </div>
                </div>
            </div>
            """
        )

    # Current Intelligence wirkt als begrenztes Overlay auf
    # die Kaufchance. Nur persistent übernommene Analysen zählen.
    data = apply_current_intelligence(data)

    def build_report_pdf():
        report_data = build_analysis_report_data(data)
        return build_analysis_pdf(report_data)

    ticker_for_filename = (
        str(data.get("Ticker") or "Aktie")
        .strip()
        .replace("/", "-")
        .replace("\\", "-")
    )

    with st.container(border=True):
        st.html(
            '<span class="inra-main-section-marker"></span>'
        )
        render_investment_decision(
            data,
            report_pdf_builder=build_report_pdf,
            report_filename=(
                f"InRA_Analyse_{ticker_for_filename}.pdf"
            ),
        )

    st.markdown(
        "<div style='height:18px;'></div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.html(
            '<span class="inra-main-section-marker"></span>'
        )
        render_analysis_overview(data)

        active_detail = st.session_state.get(
            "analysis_overview_detail"
        )

        if active_detail:
            if active_detail == "quality":
                render_quality_section(data)

            elif active_detail == "opportunity":
                render_opportunity_section(data)

            elif active_detail == "dividend":
                render_dividend_section(data)

    st.markdown(
        "<div style='height:18px;'></div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.html(
            '<span class="inra-main-section-marker"></span>'
        )
        st.markdown(
            """
            <div
                class="inra-section-header"
                style="margin-bottom:0.55rem;"
            >
                <div class="inra-section-kicker">
                    03 · WAS BEWEGT DIE AKTIE?
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_current_intelligence_section(data)

    st.markdown(
        "<div style='height:18px;'></div>",
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.html(
            '<span class="inra-main-section-marker"></span>'
        )
        st.markdown(
            """
            <div
                class="inra-section-header"
                style="margin-bottom:0.55rem;"
            >
                <div class="inra-section-kicker">
                    04 · INRA-FAZIT
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_inra_fazit_section(data)
