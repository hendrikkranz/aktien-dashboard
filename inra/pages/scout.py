import csv
from pathlib import Path

import streamlit as st

from utils.data_loader import load_universe


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

search = st.text_input(
    "Aktie suchen",
    key="scout_search",
    placeholder="Name oder Ticker eingeben",
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

if show_favorites_only:
    filtered_universe = filtered_universe[
        filtered_universe["Ticker"].isin(
            st.session_state["favorite_tickers"]
        )
    ]

metric1, metric2 = st.columns(2)

with metric1:
    st.metric(
        "Gefundene Aktien",
        len(filtered_universe),
    )

with metric2:
    st.metric(
        "Favoriten",
        len(st.session_state["favorite_tickers"]),
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

    is_favorite = (
        selected_ticker
        in st.session_state["favorite_tickers"]
    )

    action1, action2 = st.columns(2)

    with action1:
        if st.button(
            "Aktie analysieren",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["analyse_ticker"] = selected_ticker
            st.switch_page("pages/analyse.py")

    with action2:
        favorite_label = (
            "★ Favorit entfernen"
            if is_favorite
            else "☆ Als Favorit speichern"
        )

        if st.button(
            favorite_label,
            use_container_width=True,
        ):
            if is_favorite:
                st.session_state["favorite_tickers"].remove(
                    selected_ticker
                )
            else:
                st.session_state["favorite_tickers"].append(
                    selected_ticker
                )

            save_favorites(
                st.session_state["favorite_tickers"]
            )

            st.rerun()

    display_universe = filtered_universe.copy()

    display_universe.insert(
        0,
        "Favorit",
        display_universe["Ticker"].apply(
            lambda ticker: (
                "★"
                if ticker
                in st.session_state["favorite_tickers"]
                else ""
            )
        ),
    )

    st.dataframe(
        display_universe,
        width="stretch",
        hide_index=True,
    )