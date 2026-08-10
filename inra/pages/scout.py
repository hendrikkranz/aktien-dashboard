import csv
from pathlib import Path

import streamlit as st

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

    display_universe = display_universe[
        [
            "Favorit",
            "Name",
            "Ticker",
            "Sektor",
            "Branche",
            "Land",
        ]
    ]

    edited_universe = st.data_editor(
        display_universe,
        width="stretch",
        hide_index=True,
        disabled=[
            "Name",
            "Ticker",
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