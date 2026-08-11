import csv
from pathlib import Path

import streamlit as st
import plotly.express as px

from utils.data_loader import (
    load_benchmark_cache,
    load_universe,
)


FAVORITES_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "favorites.csv"
)


def load_favorites() -> list:
    if not FAVORITES_PATH.exists():
        return []

    with FAVORITES_PATH.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        return [
            row["Ticker"]
            for row in reader
            if row.get("Ticker")
        ]


def save_favorites(tickers: list) -> None:
    FAVORITES_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with FAVORITES_PATH.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["Ticker"],
        )

        writer.writeheader()

        for ticker in sorted(set(tickers)):
            writer.writerow(
                {
                    "Ticker": ticker,
                }
            )


st.title("Scout")
st.caption("Welche Aktien verdienen heute meine Aufmerksamkeit?")

if "favorite_tickers" not in st.session_state:
    st.session_state["favorite_tickers"] = load_favorites()

universe = load_universe()
benchmark_cache = load_benchmark_cache()

if not benchmark_cache.empty:
    universe = universe.merge(
        benchmark_cache,
        on="Ticker",
        how="left",
        suffixes=("", "_cache"),
    )

list_options = sorted(
    set(
        option.strip()
        for value in universe["Liste"].fillna("")
        for option in value.split(";")
        if option.strip()
    )
)

search = st.text_input(
    "Aktie suchen",
    key="scout_search",
    placeholder="Name oder Ticker eingeben",
)

selected_list = st.selectbox(
    "Liste",
    options=["Alle"] + list_options,
)

sector_options = sorted(
    universe["Sektor"]
    .dropna()
    .astype(str)
    .unique()
)

selected_sector = st.selectbox(
    "Sektor",
    options=["Alle"] + sector_options,
)

industry_options = sorted(
    universe["Branche"]
    .dropna()
    .astype(str)
    .unique()
)

selected_industry = st.selectbox(
    "Branche",
    options=["Alle"] + industry_options,
)

country_options = sorted(
    universe["Land"]
    .dropna()
    .astype(str)
    .unique()
)

selected_country = st.selectbox(
    "Land",
    options=["Alle"] + country_options,
)

show_favorites_only = st.checkbox(
    "Nur Favoriten anzeigen",
    value=False,
)

filtered_universe = universe.copy()

if search:
    filtered_universe = filtered_universe[
        filtered_universe["Name"].str.contains(
            search,
            case=False,
            na=False,
        )
        | filtered_universe["Ticker"].str.contains(
            search,
            case=False,
            na=False,
        )
    ]

if selected_list != "Alle":
    filtered_universe = filtered_universe[
        filtered_universe["Liste"]
        .fillna("")
        .str.contains(
            selected_list,
            case=False,
            regex=False,
        )
    ]

if selected_sector != "Alle":
    filtered_universe = filtered_universe[
        filtered_universe["Sektor"]
        == selected_sector
    ]

if selected_industry != "Alle":
    filtered_universe = filtered_universe[
        filtered_universe["Branche"]
        == selected_industry
    ]

if selected_country != "Alle":
    filtered_universe = filtered_universe[
        filtered_universe["Land"]
        == selected_country
    ]

if show_favorites_only:
    filtered_universe = filtered_universe[
        filtered_universe["Ticker"].isin(
            st.session_state["favorite_tickers"]
        )
    ]

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        "Aktien",
        len(filtered_universe),
    )

with metric2:
    st.metric(
        "Länder",
        filtered_universe["Land"].nunique(),
    )

with metric3:
    st.metric(
        "Sektoren",
        filtered_universe["Sektor"].nunique(),
    )

with metric4:
    st.metric(
        "Branchen",
        filtered_universe["Branche"].nunique(),
    )

if filtered_universe.empty:
    st.info("Keine passende Aktie gefunden.")
else:
    stock_options = {
        f'{row["Name"]} ({row["Ticker"]})': row["Ticker"]
        for _, row in filtered_universe.iterrows()
    }

    selected_label = st.selectbox(
        "Aktie auswählen",
        options=list(stock_options.keys()),
    )

    selected_ticker = stock_options[selected_label]

    if st.button(
        "Aktie analysieren",
        type="primary",
        use_container_width=True,
    ):
        st.session_state["analyse_ticker"] = selected_ticker
        st.switch_page("pages/analyse.py")

    display_universe = filtered_universe.copy()

    display_universe.insert(
        0,
        "Favorit",
        display_universe["Ticker"].isin(
            st.session_state["favorite_tickers"]
        ),
    )

    display_universe = display_universe.sort_values(
        by="Kaufchance",
        ascending=False,
        na_position="last",
    )

    display_universe = display_universe[
        [
            "Favorit",
            "Name",
            "Ticker",
            "Unternehmensqualität",
            "Kaufchance",
            "Sektor",
            "Branche",
            "Land",
        ]
    ]

    st.subheader("Aktienübersicht")

    edited_universe = st.data_editor(
        display_universe,
        width="stretch",
        hide_index=True,
        disabled=[
            "Name",
            "Ticker",
            "Unternehmensqualität",
            "Kaufchance",
            "Sektor",
            "Branche",
            "Land",
        ],
        column_config={
            "Favorit": st.column_config.CheckboxColumn(
                "★",
                help="Aktie als Favorit markieren",
            ),
        },
        key="scout_favorites_editor",
    )

    selected_favorites = edited_universe.loc[
        edited_universe["Favorit"] == True,
        "Ticker",
    ].tolist()

    if set(selected_favorites) != set(
        st.session_state["favorite_tickers"]
    ):
        st.session_state["favorite_tickers"] = selected_favorites

        save_favorites(
            st.session_state["favorite_tickers"]
        )

        st.rerun()
    
    st.subheader("Rankings")

    ranking_col1, ranking_col2 = st.columns(2)

    with ranking_col1:
        st.markdown("#### Top 10 Kaufchancen")

        top_opportunities = (
            universe[
                [
                    "Name",
                    "Ticker",
                    "Kaufchance",
                    "Unternehmensqualität",
                ]
            ]
            .dropna(subset=["Kaufchance"])
            .sort_values(
                by="Kaufchance",
                ascending=False,
            )
            .head(10)
        )

        top_opportunities = top_opportunities.rename(
            columns={
                "Kaufchance": "Chance",
                "Unternehmensqualität": "Qualität",
            }
        )

        st.dataframe(
            top_opportunities,
            width="stretch",
            hide_index=True,
        )

    with ranking_col2:
        st.markdown("#### Top 10 Unternehmensqualität")

        top_quality = (
            universe[
                [
                    "Name",
                    "Ticker",
                    "Unternehmensqualität",
                    "Kaufchance",
                ]
            ]
            .dropna(subset=["Unternehmensqualität"])
            .sort_values(
                by="Unternehmensqualität",
                ascending=False,
            )
            .head(10)
        )

        top_quality = top_quality.rename(
            columns={
                "Unternehmensqualität": "Qualität",
                "Kaufchance": "Chance",
            }
        )

        st.dataframe(
            top_quality,
            width="stretch",
            hide_index=True,
        )
    st.subheader("Qualität × Kaufchance")

    matrix_data = (
        universe[
            [
                "Name",
                "Ticker",
                "Unternehmensqualität",
                "Kaufchance",
            ]
        ]
        .dropna(
            subset=[
                "Unternehmensqualität",
                "Kaufchance",
            ]
        )
        .copy()
    )

    matrix_data["Quadrant"] = "Beobachten"

    matrix_data.loc[
        (matrix_data["Unternehmensqualität"] >= 70)
        & (matrix_data["Kaufchance"] >= 50),
        "Quadrant",
    ] = "Top-Kandidaten"

    matrix_data.loc[
        (matrix_data["Unternehmensqualität"] < 70)
        & (matrix_data["Kaufchance"] >= 50),
        "Quadrant",
    ] = "Qualitätsunternehmen"

    matrix_data.loc[
        (matrix_data["Unternehmensqualität"] >= 70)
        & (matrix_data["Kaufchance"] < 50),
        "Quadrant",
    ] = "Chancen"

    fig = px.scatter(
        matrix_data,
        x="Unternehmensqualität",
        y="Kaufchance",
        color="Quadrant",
        color_discrete_map={
            "Top-Kandidaten": "#2ecc71",
            "Qualitätsunternehmen": "#4da3ff",
            "Chancen": "#f1c40f",
            "Beobachten": "#e74c3c",
        },
        hover_name="Name",
        hover_data={
            "Ticker": ":",
            "Unternehmensqualität": False,
            "Kaufchance": False,
            "Quadrant": False,
        },
        labels={
            "Unternehmensqualität": "Unternehmensqualität",
            "Kaufchance": "Kaufchance",
        },
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br><br>"
            "Ticker: %{customdata[0]}<br>"
            "Qualität: %{x:.0f}<br>"
            "Chance: %{y:.0f}"
            "<extra></extra>"
        )
    )

    fig.add_vline(
        x=70,
        line_dash="dash",
    )

    fig.add_hline(
        y=50,
        line_dash="dash",
    )

    fig.add_shape(
        type="rect",
        x0=70,
        x1=100,
        y0=50,
        y1=100,
        fillcolor="green",
        opacity=0.03,
        line_width=0,
        layer="below",
    )

    fig.add_shape(
        type="rect",
        x0=0,
        x1=70,
        y0=50,
        y1=100,
        fillcolor="blue",
        opacity=0.02,
        line_width=0,
        layer="below",
    )

    fig.add_shape(
        type="rect",
        x0=70,
        x1=100,
        y0=0,
        y1=50,
        fillcolor="yellow",
        opacity=0.05,
        line_width=0,
        layer="below",
    )

    fig.add_shape(
        type="rect",
        x0=0,
        x1=70,
        y0=0,
        y1=50,
        fillcolor="red",
        opacity=0.02,
        line_width=0,
        layer="below",
    )

    fig.add_annotation(
        x=89,
        y=69,
        text="Top-Kandidaten",
        showarrow=False,
        font=dict(
            size=10,
            color="#2ecc71",
        ),
    )

    fig.add_annotation(
        x=44,
        y=69,
        text="Einstiegsoptionen",
        showarrow=False,
        font=dict(
            size=10,
            color="#4da3ff",
        ),
    )

    fig.add_annotation(
        x=89,
        y=23,
        text="Qualitätsaktien",
        showarrow=False,
        font=dict(
            size=10,
            color="#f1c40f",
        ),
    )

    fig.add_annotation(
        x=44,
        y=23,
        text="Keine Priorität",
        showarrow=False,
        font=dict(
            size=10,
            color="#e74c3c",
        ),
    )

    fig.update_layout(
        height=550,
        xaxis_range=[40, 92],
        yaxis_range=[22, 72],
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )