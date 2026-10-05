import time
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st

from utils.country_market_data import (
    FRANCE_INDICES,
    GERMANY_INDICES,
    JAPAN_INDICES,
    NETHERLANDS_INDICES,
    SWITZERLAND_INDICES,
    UK_INDICES,
    USA_INDICES,
    get_index_inra_update_timestamp,
    get_index_market_snapshot,
    save_index_inra_update_timestamp,
    update_missing_index_inra_scores,
)
from utils.data_loader import (
    load_benchmark_cache,
)
from utils.market_data import (
    load_price_history,
)


def render_country(
    country_name,
    flag,
    indices,
    default_index,
    key_prefix,
):
    st.markdown(
        f"## {flag} {country_name}"
    )
    st.caption(
        " · ".join(indices)
    )

    requested_index = st.session_state.pop(
        "country_market_index",
        None,
    )

    index_key = f"{key_prefix}_index"

    if requested_index in indices:
        st.session_state[index_key] = requested_index
    elif (
        index_key not in st.session_state
        or st.session_state[index_key] not in indices
    ):
        st.session_state[index_key] = default_index

    index_name = st.segmented_control(
        "Index",
        options=list(indices),
        key=index_key,
        label_visibility="collapsed",
    )

    if index_name is None:
        index_name = default_index

    index_config = indices[index_name]


    # ------------------------------------------------------------------
    # Index-Chart
    # ------------------------------------------------------------------

    try:
        index_history = load_price_history(
            index_config["ticker"],
            period="max",
        )

        if (
            index_history is not None
            and not index_history.empty
            and "Datum" in index_history.columns
            and "Schlusskurs" in index_history.columns
        ):
            chart_data = (
                index_history[
                    ["Datum", "Schlusskurs"]
                ]
                .dropna()
                .copy()
            )

            chart_data["Datum"] = pd.to_datetime(
                chart_data["Datum"],
                utc=True,
            ).dt.tz_localize(None)

            chart_period = st.segmented_control(
                "Zeitraum",
                options=["1J", "3J", "5J", "Max"],
                default="1J",
                key=f"{key_prefix}_{index_name.lower()}_chart_period",
                label_visibility="collapsed",
            )

            period_years = {
                "1J": 1,
                "3J": 3,
                "5J": 5,
            }

            if chart_period in period_years:
                latest_date = chart_data["Datum"].max()
                start_date = latest_date - pd.DateOffset(
                    years=period_years[chart_period]
                )
                visible_data = chart_data[
                    chart_data["Datum"] >= start_date
                ].copy()
            else:
                visible_data = chart_data.copy()

            min_price = float(
                visible_data["Schlusskurs"].min()
            )
            max_price = float(
                visible_data["Schlusskurs"].max()
            )

            padding = max(
                (max_price - min_price) * 0.08,
                max_price * 0.01,
            )

            chart = (
                alt.Chart(visible_data)
                .mark_line(
                    strokeWidth=2,
                )
                .encode(
                    x=alt.X(
                        "Datum:T",
                        title=None,
                        axis=alt.Axis(
                            format="%b %Y",
                            labelAngle=0,
                        ),
                    ),
                    y=alt.Y(
                        "Schlusskurs:Q",
                        title=None,
                        scale=alt.Scale(
                            domain=[
                                max(0, min_price - padding),
                                max_price + padding,
                            ],
                            zero=False,
                        ),
                        axis=alt.Axis(
                            format=",.0f",
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
                            title=index_name,
                            format=",.2f",
                        ),
                    ],
                )
                .properties(
                    height=300,
                )
            )

            st.altair_chart(
                chart,
                use_container_width=True,
            )
        else:
            st.info(
                f"Für den {index_name}-Chart sind aktuell "
                "keine Kursdaten verfügbar."
            )

    except Exception as exc:
        st.warning(
            f"{index_name}-Chart konnte nicht geladen werden: {exc}"
        )


    # ------------------------------------------------------------------
    # Index-Ranking
    # ------------------------------------------------------------------

    st.markdown(
        f"### {index_name}-Ranking"
    )

    try:
        snapshot = get_index_market_snapshot(
            index_name
        )
    except FileNotFoundError:
        st.info(
            f"Der lokale {index_name}-Markt-Snapshot "
            "wurde noch nicht erzeugt."
        )
        st.stop()

    update_key = (
        f"{key_prefix}_{index_name.lower()}_inra_last_update"
    )

    button_col, date_col = st.columns(
        [0.42, 0.58],
        vertical_alignment="center",
    )

    with button_col:
        update_clicked = st.button(
            "🔄 Fehlende InRA-Bewertungen ergänzen",
            key=f"{key_prefix}_{index_name.lower()}_inra_update",
            help=(
                "Ergänzt ausschließlich fehlende quantitative "
                "InRA-Bewertungen. Keine KI-Recherche und keine "
                "kostenpflichtigen API-Aufrufe."
            ),
        )

    with date_col:
        last_update = (
            get_index_inra_update_timestamp(index_name)
        )

        if last_update:
            st.caption(
                f"Zuletzt aktualisiert: {last_update}"
            )
        else:
            st.caption("Noch nicht aktualisiert")

    if update_clicked:
        progress = st.progress(0)
        status = st.empty()

        def update_progress(value, label):
            progress.progress(
                min(max(float(value), 0.0), 1.0)
            )
            status.caption(label)

        result = update_missing_index_inra_scores(
            index_name,
            progress_callback=update_progress,
        )

        if result["total"] == 0:
            status.success(
                "Alle Indexmitglieder sind bereits im "
                "Benchmark-Cache vorhanden."
            )
        else:
            status.success(
                f"{result['updated']} von "
                f"{result['total']} fehlenden Aktien "
                "quantitativ ergänzt."
            )

            if result["failed"]:
                st.warning(
                    f"{len(result['failed'])} Aktien konnten "
                    "nicht aktualisiert werden."
                )

        update_timestamp = (
            datetime.now().strftime("%d.%m.%Y %H:%M")
        )

        save_index_inra_update_timestamp(
            index_name,
            update_timestamp,
        )

        time.sleep(5)
        status.empty()
        progress.empty()

    benchmark = load_benchmark_cache()

    score_columns = [
        column
        for column in (
            "Ticker",
            "Dividendenrendite",
            "Unternehmensqualität",
            "Kaufchance",
        )
        if column in benchmark.columns
    ]

    benchmark_scores = (
        benchmark[score_columns]
        .drop_duplicates(
            subset=["Ticker"],
            keep="last",
        )
    )

    ranking = snapshot.merge(
        benchmark_scores,
        on="Ticker",
        how="left",
    )

    ranking["Scout-Score"] = (
        ranking["Unternehmensqualität"]
        * ranking["Kaufchance"]
    ) ** 0.5

    ranking = ranking.sort_values(
        "Marktkapitalisierung",
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)

    ranking["Rang"] = range(
        1,
        len(ranking) + 1,
    )

    ranking["Marktkapitalisierung Mrd."] = (
        ranking["Marktkapitalisierung"]
        / 1_000_000_000
    )

    # Synthetische Median-Zeile.
    # Sie wird Bestandteil der Tabelle und bei jeder
    # Spaltensortierung wie eine normale Zeile mitsortiert.
    median_columns = [
        "Marktkapitalisierung Mrd.",
        "Dividendenrendite",
        "1M",
        "3M",
        "6M",
        "1J",
        "3J",
        "5J",
        "Max",
        "Unternehmensqualität",
        "Kaufchance",
        "Scout-Score",
    ]

    median_row = {
        column: None
        for column in ranking.columns
    }

    median_row["Rang"] = None
    median_row["Name"] = f"MEDIAN {index_name}"
    median_row["Ticker"] = ""

    for column in median_columns:
        if column in ranking.columns:
            median_row[column] = pd.to_numeric(
                ranking[column],
                errors="coerce",
            ).median()

    ranking_display = pd.concat(
        [
            ranking,
            pd.DataFrame([median_row]),
        ],
        ignore_index=True,
    )

    display_columns = [
        "Rang",
        "Name",
        "Ticker",
        "Marktkapitalisierung Mrd.",
        "Dividendenrendite",
        "1M",
        "3M",
        "6M",
        "1J",
        "3J",
        "5J",
        "Max",
        "Unternehmensqualität",
        "Kaufchance",
        "Scout-Score",
    ]

    def highlight_median_row(row):
        if str(row.get("Name", "")).startswith("MEDIAN "):
            return [
                "color: #2563eb; font-weight: 700"
                for _ in row
            ]

        return ["" for _ in row]

    styled_ranking = (
        ranking_display[display_columns]
        .style.apply(
            highlight_median_row,
            axis=1,
        )
        .map(
            lambda value: "font-weight: 600",
            subset=["Name"],
        )
    )

    table_state = st.dataframe(
        styled_ranking,
        width="stretch",
        height=770,
        hide_index=True,
        key=f"{key_prefix}_{index_name.lower()}_ranking",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Rang": st.column_config.NumberColumn(
                "#",
                help="Rang nach Marktkapitalisierung",
                width=45,
                format="%d",
            ),
            "Name": st.column_config.TextColumn(
                "Unternehmen",
                help="Zeile auswählen, um die InRA-Analyse zu öffnen",
                width=190,
            ),
            "Ticker": st.column_config.TextColumn(
                "Ticker",
                width=80,
            ),
            "Marktkapitalisierung Mrd.": (
                st.column_config.NumberColumn(
                    "Market Cap",
                    help="Marktkapitalisierung in Mrd. der Handelswährung",
                    width=80,
                    format="%.1f",
                )
            ),
            "Dividendenrendite": st.column_config.NumberColumn(
                "Div. %",
                help="Aktuelle Dividendenrendite",
                width=70,
                format="%.1f %%",
            ),
            "1M": st.column_config.NumberColumn(
                "1M",
                format="%+.1f %%",
            ),
            "3M": st.column_config.NumberColumn(
                "3M",
                format="%+.1f %%",
            ),
            "6M": st.column_config.NumberColumn(
                "6M",
                format="%+.1f %%",
            ),
            "1J": st.column_config.NumberColumn(
                "1J",
                format="%+.1f %%",
            ),
            "3J": st.column_config.NumberColumn(
                "3J",
                format="%+.1f %%",
            ),
            "5J": st.column_config.NumberColumn(
                "5J",
                format="%+.1f %%",
            ),
            "Max": st.column_config.NumberColumn(
                "Max",
                help=(
                    "Performance seit Beginn der jeweils "
                    "verfügbaren Yahoo-Kurshistorie"
                ),
                format="%+.1f %%",
            ),
            "Unternehmensqualität": (
                st.column_config.NumberColumn(
                    "Qualität",
                    width=65,
                    format="%.0f",
                )
            ),
            "Kaufchance": st.column_config.NumberColumn(
                "Kaufchance",
                width=75,
                format="%.0f",
            ),
            "Scout-Score": st.column_config.NumberColumn(
                "Scout",
                help=(
                    "Geometrisches Mittel aus "
                    "Unternehmensqualität und Kaufchance"
                ),
                width=60,
                format="%.1f",
            ),
        },
    )

    selected_rows = table_state.selection.rows

    if selected_rows:
        selected_row = selected_rows[0]
        selected_ticker = ranking_display.iloc[
            selected_row
        ]["Ticker"]

        if selected_ticker:
            st.session_state["analyse_ticker"] = (
                selected_ticker
            )
            st.switch_page("pages/analyse.py")


    inra_count = ranking[
        "Unternehmensqualität"
    ].notna().sum()

    st.caption(
        f"{len(ranking)} {index_name}-Mitglieder · "
        f"{inra_count} davon aktuell mit InRA-Bewertung"
    )

def render_germany():
    render_country(
        country_name="Deutschland",
        flag="🇩🇪",
        indices=GERMANY_INDICES,
        default_index="DAX",
        key_prefix="germany",
    )


def render_usa():
    render_country(
        country_name="USA",
        flag="🇺🇸",
        indices=USA_INDICES,
        default_index="Dow Jones",
        key_prefix="usa",
    )


def render_france():
    render_country(
        country_name="Frankreich",
        flag="🇫🇷",
        indices=FRANCE_INDICES,
        default_index="CAC 40",
        key_prefix="france",
    )


def render_switzerland():
    render_country(
        country_name="Schweiz",
        flag="🇨🇭",
        indices=SWITZERLAND_INDICES,
        default_index="SMI",
        key_prefix="switzerland",
    )


def render_uk():
    render_country(
        country_name="Großbritannien",
        flag="🇬🇧",
        indices=UK_INDICES,
        default_index="FTSE 100",
        key_prefix="uk",
    )


def render_japan():
    render_country(
        country_name="Japan",
        flag="🇯🇵",
        indices=JAPAN_INDICES,
        default_index="Nikkei 225",
        key_prefix="japan",
    )


def render_netherlands():
    render_country(
        country_name="Niederlande",
        flag="🇳🇱",
        indices=NETHERLANDS_INDICES,
        default_index="AEX",
        key_prefix="netherlands",
    )

