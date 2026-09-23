from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf


UNIVERSE_PATH = Path("data/universe.csv")

BENCHMARK_CACHE_PATH = Path("data/benchmark_cache.csv")

def get_benchmark_cache_timestamp():
    if not BENCHMARK_CACHE_PATH.exists():
        return None

    return BENCHMARK_CACHE_PATH.stat().st_mtime

def load_universe() -> pd.DataFrame:
    return pd.read_csv(UNIVERSE_PATH)

def is_ticker_in_universe(ticker: str) -> bool:
    if not ticker:
        return False

    universe = load_universe()

    return (
        universe["Ticker"]
        .astype(str)
        .str.upper()
        .eq(ticker.strip().upper())
        .any()
    )

def add_stock_to_universe(
    name: str,
    ticker: str,
    sector=None,
    industry=None,
    country=None,
) -> bool:
    if not ticker or is_ticker_in_universe(ticker):
        return False

    row = pd.DataFrame(
        [
            {
                "Name": name or ticker,
                "Ticker": ticker.strip().upper(),
                "Sektor": sector,
                "Branche": industry,
                "Land": country,
                "Liste": "Watchlist",
                "Aktiv": 1,
            }
        ]
    )

    row.to_csv(
        UNIVERSE_PATH,
        mode="a",
        header=False,
        index=False,
    )

    return True

def add_stock_to_list(
    ticker: str,
    list_name: str,
) -> bool:
    """
    Fügt eine vorhandene Aktie einer Scout-Liste hinzu.

    Mehrere Listen werden in universe.csv durch Semikolon getrennt.
    Bestehende Listenzuordnungen bleiben erhalten.
    """
    if not ticker or not list_name:
        return False

    ticker = ticker.strip().upper()
    list_name = list_name.strip()

    if not list_name or ";" in list_name:
        return False

    universe = load_universe()

    ticker_mask = (
        universe["Ticker"]
        .astype(str)
        .str.upper()
        .eq(ticker)
    )

    if not ticker_mask.any():
        return False

    current_value = universe.loc[
        ticker_mask,
        "Liste",
    ].iloc[0]

    current_lists = [
        item.strip()
        for item in (
            ""
            if pd.isna(current_value)
            else str(current_value)
        ).split(";")
        if item.strip()
    ]

    if list_name in current_lists:
        return False

    current_lists.append(list_name)

    universe.loc[
        ticker_mask,
        "Liste",
    ] = ";".join(current_lists)

    universe.to_csv(
        UNIVERSE_PATH,
        index=False,
    )

    return True


def add_investment_decision_to_data(data: dict) -> dict:
    """
    Ergänzt das zentrale Investment-Urteil für die Cache-Nutzung.

    Die Berechnung erfolgt vor der CSV-Serialisierung, solange
    strukturierte Analysefelder noch ihre ursprünglichen Typen haben.
    """
    from components.investment_decision import (
        get_investment_decision,
    )

    decision = get_investment_decision(data)

    data["Investment-Urteil"] = decision["title"]

    return data


def update_stock_in_benchmark_cache(ticker: str) -> dict:
    from utils.market_data import load_company_snapshot
    from utils.current_intelligence import apply_current_intelligence

    if not ticker:
        raise ValueError("Ticker fehlt.")

    ticker = ticker.strip().upper()
    data = load_company_snapshot(ticker)
    data = apply_current_intelligence(data)
    data = add_investment_decision_to_data(data)

    if BENCHMARK_CACHE_PATH.exists():
        cache = pd.read_csv(BENCHMARK_CACHE_PATH)
        cache = cache[
            ~cache["Ticker"]
            .astype(str)
            .str.upper()
            .eq(ticker)
        ]
    else:
        cache = pd.DataFrame()

    new_row = pd.DataFrame([data])

    if cache.empty:
        updated_cache = new_row
    else:
        updated_cache = pd.concat(
            [cache, new_row],
            ignore_index=True,
        )

    updated_cache.to_csv(
        BENCHMARK_CACHE_PATH,
        index=False,
    )

    return data


def load_benchmark_cache() -> pd.DataFrame:
    if not BENCHMARK_CACHE_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(BENCHMARK_CACHE_PATH)

def search_stock_candidates(
    search_text: str,
    max_results: int = 8,
) -> list:
    if not search_text:
        return []

    query = search_text.strip()
    query_normalized = query.casefold()

    if len(query_normalized) < 2:
        return []

    candidates = []
    seen_tickers = set()

    def add_candidate(
        name,
        ticker,
        source,
        exchange=None,
        alias_match=False,
    ):
        ticker = str(ticker or "").strip()
        name = str(name or ticker).strip()

        if not ticker:
            return

        ticker_key = ticker.upper()

        if ticker_key in seen_tickers:
            return

        seen_tickers.add(ticker_key)
        candidates.append(
            {
                "Name": name,
                "Ticker": ticker,
                "Source": source,
                "Exchange": exchange,
                "AliasMatch": alias_match,
            }
        )

    universe = load_universe()

    search_aliases = {
        "bmw": "BMW.DE",
        "basf": "BAS.DE",
        "vw": "VOW3.DE",
    }

    alias_ticker = search_aliases.get(query_normalized)

    if alias_ticker:
        alias_rows = universe[
            universe["Ticker"]
            .astype(str)
            .str.upper()
            .eq(alias_ticker.upper())
        ]

        for _, row in alias_rows.iterrows():
            add_candidate(
                row.get("Name"),
                row.get("Ticker"),
                "Universe",
                alias_match=True,
            )

    for _, row in universe.iterrows():
        name = str(row.get("Name") or "")
        ticker = str(row.get("Ticker") or "")
        name_normalized = name.casefold()
        ticker_normalized = ticker.casefold()

        if (
            query_normalized in name_normalized
            or query_normalized in ticker_normalized
        ):
            add_candidate(
                name,
                ticker,
                "Universe",
            )

    try:
        search_result = yf.Search(
            query,
            max_results=10,
            news_count=0,
        )

        for quote in search_result.quotes or []:
            if quote.get("quoteType") != "EQUITY":
                continue

            add_candidate(
                quote.get("longname")
                or quote.get("shortname")
                or quote.get("symbol"),
                quote.get("symbol"),
                "Yahoo",
                quote.get("exchDisp"),
            )
    except Exception:
        pass

    def rank(candidate):
        name = candidate["Name"].strip().casefold()
        ticker = candidate["Ticker"].strip().casefold()
        words = name.split()

        if candidate.get("AliasMatch"):
            return 0
        if ticker == query_normalized:
            return 0
        if name == query_normalized:
            return 1
        if query_normalized in words:
            return 2
        if ticker.startswith(query_normalized):
            return 3
        if name.startswith(query_normalized):
            return 4
        if any(
            word.startswith(query_normalized)
            for word in words
        ):
            return 5
        if query_normalized in ticker:
            return 6
        if query_normalized in name:
            return 7

        return 8

    best_rank = min(
        (rank(candidate) for candidate in candidates),
        default=None,
    )

    relevant_candidates = [
        candidate
        for candidate in candidates
        if (
            best_rank is not None
            and rank(candidate) <= best_rank + 1
        )
    ]

    def listing_preference(candidate):
        ticker = candidate["Ticker"].strip()

        # Bei gleich guten Namens-Treffern bevorzugen wir
        # die typische Hauptnotierung ohne Börsensuffix.
        # Exakte Tickereingaben bleiben durch rank() vorrangig.
        return 0 if "." not in ticker else 1

    return sorted(
        relevant_candidates,
        key=lambda candidate: (
            rank(candidate),
            listing_preference(candidate),
            0 if candidate["Source"] == "Universe" else 1,
            candidate["Name"].casefold(),
            candidate["Ticker"].casefold(),
        ),
    )[:max_results]


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

        query = search_text.strip().lower()

        for quote in quotes:
            symbol = quote.get("symbol")
            quote_type = quote.get("quoteType")
            sector = quote.get("sector")
            industry = quote.get("industry")

            if (
                symbol
                and quote_type == "EQUITY"
                and (
                    sector is not None
                    or industry is not None
                )
            ):
                return str(symbol)

        for preferred_type in (
            "EQUITY",
            "ETF",
            "MUTUALFUND",
        ):
            for quote in quotes:
                symbol = quote.get("symbol")
                quote_type = quote.get("quoteType")
                short_name = str(
                    quote.get("shortname") or ""
                ).lower()
                long_name = str(
                    quote.get("longname") or ""
                ).lower()

                if (
                    symbol
                    and quote_type == preferred_type
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