from pathlib import Path
from typing import Optional

import pandas as pd


UNIVERSE_PATH = Path("inra/data/universe.csv")


def load_universe() -> pd.DataFrame:
    return pd.read_csv(UNIVERSE_PATH)


def find_ticker(search_text: str) -> Optional[str]:
    """
    Ermittelt einen Yahoo-Ticker anhand von
    Ticker oder Unternehmensname.
    """

    if not search_text:
        return None

    df = load_universe()

    search = search_text.strip().lower()

    # Exakter Ticker
    ticker_match = df[
        df["Ticker"].astype(str).str.lower() == search
    ]

    if not ticker_match.empty:
        return ticker_match.iloc[0]["Ticker"]

    # Exakter Unternehmensname
    name_match = df[
        df["Name"].astype(str).str.lower() == search
    ]

    if not name_match.empty:
        return name_match.iloc[0]["Ticker"]

    # Teiltreffer (z.B. "microsoft")
    partial = df[
        df["Name"].astype(str).str.lower().str.contains(
            search,
            na=False,
        )
    ]

    if not partial.empty:
        return partial.iloc[0]["Ticker"]

    return None