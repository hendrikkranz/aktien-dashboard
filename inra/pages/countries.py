import altair as alt
import pandas as pd
import streamlit as st

from utils.country_market_data import (
    get_dax_market_snapshot,
)
from utils.data_loader import (
    load_benchmark_cache,
)
from utils.market_data import (
    load_price_history,
)


st.title("Länder")
st.caption(
    "Internationale Aktienmärkte, Leitindizes und Indexmitglieder"
)

st.markdown("## 🇩🇪 Deutschland")
st.caption("DAX · 40 führende deutsche Aktiengesellschaften")


# ------------------------------------------------------------------
# DAX-Chart
# ------------------------------------------------------------------

try:
    dax_history = load_price_history(
        "^GDAXI",
        period="max",
    )

    if (
        dax_history is not None
        and not dax_history.empty
        and "Datum" in dax_history.columns
        and "Schlusskurs" in dax_history.columns
    ):
        chart_data = (
            dax_history[
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
            key="dax_chart_period",
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
                        title="DAX",
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
            "Für den DAX-Chart sind aktuell keine Kursdaten verfügbar."
        )

except Exception as exc:
    st.warning(
        f"DAX-Chart konnte nicht geladen werden: {exc}"
    )


# ------------------------------------------------------------------
# DAX-Ranking
# ------------------------------------------------------------------

st.markdown("### DAX-Ranking")

snapshot = get_dax_market_snapshot()
benchmark = load_benchmark_cache()

score_columns = [
    column
    for column in (
        "Ticker",
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

display_columns = [
    "Rang",
    "Name",
    "Ticker",
    "Marktkapitalisierung Mrd.",
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

table_state = st.dataframe(
    ranking[display_columns],
    width="stretch",
    hide_index=True,
    key="dax_ranking",
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
                help="Marktkapitalisierung in Mrd. EUR",
                width=105,
                format="%.1f",
            )
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
                width=80,
                format="%.0f",
            )
        ),
        "Kaufchance": st.column_config.NumberColumn(
            "Kaufchance",
            width=95,
            format="%.0f",
        ),
        "Scout-Score": st.column_config.NumberColumn(
            "Scout",
            help=(
                "Geometrisches Mittel aus "
                "Unternehmensqualität und Kaufchance"
            ),
            width=75,
            format="%.1f",
        ),
    },
)

selected_rows = table_state.selection.rows

if selected_rows:
    selected_row = selected_rows[0]
    selected_ticker = ranking.iloc[
        selected_row
    ]["Ticker"]

    st.session_state["analyse_ticker"] = (
        selected_ticker
    )
    st.switch_page("pages/analyse.py")


inra_count = ranking[
    "Unternehmensqualität"
].notna().sum()

st.caption(
    f"{len(ranking)} DAX-Mitglieder · "
    f"{inra_count} davon aktuell mit InRA-Bewertung"
)
