from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf


UNIVERSE_PATH = Path("inra/data/universe.csv")

BENCHMARK_CACHE_PATH = Path("inra/data/benchmark_cache.csv")

def load_universe() -> pd.DataFrame:
    return pd.read_csv(UNIVERSE_PATH)

def load_benchmark_cache() -> pd.DataFrame:
    if not BENCHMARK_CACHE_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(BENCHMARK_CACHE_PATH)

def find_ticker_in_universe(
    search_text: str,
) -> Optional[str]:
    if not search_text:
        return None

    universe = load_universe()
    search = search_text.strip().lower()

    ticker_match = universe[
        universe["Ticker"].astype(str).str.lower() == search
    ]

    if not ticker_match.empty:
        return str(ticker_match.iloc[0]["Ticker"])

    name_match = universe[
        universe["Name"].astype(str).str.lower() == search
    ]

    if not name_match.empty:
        return str(name_match.iloc[0]["Ticker"])

    partial_match = universe[
        universe["Name"]
        .astype(str)
        .str.lower()
        .str.contains(
            search,
            na=False,
            regex=False,
        )
    ]

    if not partial_match.empty:
        return str(partial_match.iloc[0]["Ticker"])

    return None


def find_ticker_with_yahoo(
    search_text: str,
) -> Optional[str]:
    if not search_text:
        return None

    try:
        search_result = yf.Search(
            search_text.strip(),
            max_results=10,
            news_count=0,
        )

        quotes = search_result.quotes or []

        for quote in quotes:
            symbol = quote.get("symbol")
            quote_type = quote.get("quoteType")
            short_name = str(
                quote.get("shortname") or ""
            ).lower()
            long_name = str(
                quote.get("longname") or ""
            ).lower()
            query = search_text.strip().lower()

            if (
                symbol
                and quote_type
                in (
                    "EQUITY",
                    "ETF",
                    "MUTUALFUND",
                )
                and (
                    query in short_name
                    or query in long_name
                )
            ):
                return str(symbol)

    except Exception:
        return None

    return None


def find_ticker(
    search_text: str,
) -> Optional[str]:
    if not search_text:
        return None

    universe_ticker = find_ticker_in_universe(
        search_text
    )

    if universe_ticker is not None:
        return universe_ticker

    yahoo_ticker = find_ticker_with_yahoo(
        search_text
    )

    if yahoo_ticker is not None:
        return yahoo_ticker

    direct_ticker = search_text.strip().upper()

    if " " not in direct_ticker:
        return direct_ticker

    return None