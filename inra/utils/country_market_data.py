"""Datenebene für die InRA-Länderansichten."""

from functools import lru_cache
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


INDEX_CONSTITUENTS_DIR = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "index_constituents"
)

DAX_CONSTITUENTS_PATH = (
    INDEX_CONSTITUENTS_DIR / "dax.csv"
)


COUNTRY_MARKETS = {
    "Germany": {
        "name": "Deutschland",
        "flag": "🇩🇪",
        "index_name": "DAX",
        "index_ticker": "^GDAXI",
    },
}


@lru_cache(maxsize=1)
def load_dax_constituents() -> pd.DataFrame:
    """Lädt die aktuellen DAX-Mitglieder von Wikipedia."""

    url = "https://en.wikipedia.org/wiki/DAX"

    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    for table in soup.find_all("table"):
        headers = [
            cell.get_text(" ", strip=True)
            for cell in table.find_all("th")
        ]

        if not (
            "Ticker" in headers
            and "Company" in headers
        ):
            continue

        rows = []

        for row in table.find_all("tr")[1:]:
            cells = [
                cell.get_text(" ", strip=True)
                for cell in row.find_all(["th", "td"])
            ]

            if len(cells) < 3:
                continue

            ticker = cells[0]
            company = cells[2]

            if ticker and company:
                rows.append(
                    {
                        "Ticker": ticker,
                        "Name": company,
                    }
                )

        members = pd.DataFrame(rows)

        if len(members) == 40:
            return members

    raise ValueError(
        "Die DAX-Mitglieder konnten nicht vollständig geladen werden."
    )



def update_dax_constituents() -> pd.DataFrame:
    """Aktualisiert den lokalen DAX-Mitglieder-Cache."""

    members = load_dax_constituents().copy()

    INDEX_CONSTITUENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    members.to_csv(
        DAX_CONSTITUENTS_PATH,
        index=False,
    )

    return members


def get_dax_constituents() -> pd.DataFrame:
    """Liest die DAX-Mitglieder aus dem lokalen Cache."""

    if not DAX_CONSTITUENTS_PATH.exists():
        raise FileNotFoundError(
            "Lokaler DAX-Mitglieder-Cache fehlt. "
            "Bitte zunächst aktualisieren."
        )

    members = pd.read_csv(
        DAX_CONSTITUENTS_PATH
    )

    required_columns = {
        "Ticker",
        "Name",
    }

    if not required_columns.issubset(
        members.columns
    ):
        raise ValueError(
            "DAX-Mitglieder-Cache hat ein ungültiges Format."
        )

    if len(members) != 40:
        raise ValueError(
            "DAX-Mitglieder-Cache enthält nicht 40 Titel."
        )

    return members


def _performance_since(
    series: pd.Series,
    months: int = 0,
    years: int = 0,
):
    """Performance seit einem Kalenderstichtag."""

    series = series.dropna()

    if series.empty:
        return None

    end_date = series.index[-1]
    target_date = (
        end_date
        - pd.DateOffset(
            months=months,
            years=years,
        )
    )

    eligible = series[
        series.index <= target_date
    ]

    if eligible.empty:
        return None

    start_price = float(eligible.iloc[-1])
    end_price = float(series.iloc[-1])

    if start_price <= 0:
        return None

    return (
        end_price / start_price - 1
    ) * 100.0


def build_dax_market_snapshot() -> pd.DataFrame:
    """Erzeugt den aktuellen Markt-Snapshot aller DAX-Mitglieder."""

    import yfinance as yf

    members = get_dax_constituents().copy()
    tickers = members["Ticker"].tolist()

    prices = yf.download(
        tickers,
        period="max",
        interval="1d",
        auto_adjust=True,
        progress=False,
        threads=True,
    )

    if prices.empty or "Close" not in prices:
        raise ValueError(
            "DAX-Kurshistorien konnten nicht geladen werden."
        )

    close = prices["Close"]

    rows = []

    for _, member in members.iterrows():
        ticker = member["Ticker"]
        name = member["Name"]

        series = (
            close[ticker].dropna()
            if ticker in close.columns
            else pd.Series(dtype=float)
        )

        market_cap = None
        currency = None

        try:
            fast_info = yf.Ticker(ticker).fast_info
            market_cap = fast_info.get("marketCap")
            currency = fast_info.get("currency")
        except Exception:
            pass

        if series.empty:
            max_performance = None
            history_start = None
        else:
            first_price = float(series.iloc[0])
            last_price = float(series.iloc[-1])

            max_performance = (
                (last_price / first_price - 1) * 100.0
                if first_price > 0
                else None
            )

            history_start = series.index[0].date()

        rows.append(
            {
                "Ticker": ticker,
                "Name": name,
                "Marktkapitalisierung": market_cap,
                "Währung": currency,
                "1M": _performance_since(
                    series,
                    months=1,
                ),
                "3M": _performance_since(
                    series,
                    months=3,
                ),
                "6M": _performance_since(
                    series,
                    months=6,
                ),
                "1J": _performance_since(
                    series,
                    years=1,
                ),
                "3J": _performance_since(
                    series,
                    years=3,
                ),
                "5J": _performance_since(
                    series,
                    years=5,
                ),
                "Max": max_performance,
                "Historie seit": history_start,
            }
        )

    return pd.DataFrame(rows)


DAX_MARKET_SNAPSHOT_PATH = (
    INDEX_CONSTITUENTS_DIR / "dax_market_snapshot.csv"
)


def update_dax_market_snapshot() -> pd.DataFrame:
    """Aktualisiert den lokalen DAX-Markt-Snapshot."""

    snapshot = build_dax_market_snapshot()

    INDEX_CONSTITUENTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    snapshot.to_csv(
        DAX_MARKET_SNAPSHOT_PATH,
        index=False,
    )

    return snapshot


def get_dax_market_snapshot() -> pd.DataFrame:
    """Liest den DAX-Markt-Snapshot aus dem lokalen Cache."""

    if not DAX_MARKET_SNAPSHOT_PATH.exists():
        raise FileNotFoundError(
            "Lokaler DAX-Markt-Snapshot fehlt. "
            "Bitte zunächst aktualisieren."
        )

    snapshot = pd.read_csv(
        DAX_MARKET_SNAPSHOT_PATH
    )

    required_columns = {
        "Ticker",
        "Name",
        "Marktkapitalisierung",
        "Währung",
        "1M",
        "3M",
        "6M",
        "1J",
        "3J",
        "5J",
        "Max",
        "Historie seit",
    }

    if not required_columns.issubset(
        snapshot.columns
    ):
        raise ValueError(
            "DAX-Markt-Snapshot hat ein ungültiges Format."
        )

    if len(snapshot) != 40:
        raise ValueError(
            "DAX-Markt-Snapshot enthält nicht 40 Titel."
        )

    return snapshot
