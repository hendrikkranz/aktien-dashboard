from pathlib import Path
import sys

import pandas as pd

INRA_ROOT = Path(__file__).resolve().parent.parent

if str(INRA_ROOT) not in sys.path:
    sys.path.insert(0, str(INRA_ROOT))

from utils.market_data import load_company_snapshot
from utils.current_intelligence import apply_current_intelligence
from utils.data_loader import add_investment_decision_to_data


UNIVERSE_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "universe.csv"
)

OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "benchmark_cache.csv"
)

def load_universe() -> pd.DataFrame:
    return pd.read_csv(UNIVERSE_PATH)

def update_real_estate_benchmark() -> None:
    universe = load_universe()

    real_estate_rows = universe[
        universe["Ticker"].astype(str).str.strip().ne("")
        & universe["Sektor"].astype(str).str.strip().eq(
            "Real Estate"
        )
    ]

    results = []

    for _, row in real_estate_rows.iterrows():
        ticker = str(row["Ticker"]).strip().upper()

        print(f"Lade Immobilienaktie {ticker}...")

        try:
            data = load_company_snapshot(ticker)

            if data.get("Sektor") != "Real Estate":
                continue

            data = apply_current_intelligence(data)
            data = add_investment_decision_to_data(data)
            results.append(data)

        except Exception as error:
            print(
                f"Fehler bei Immobilienaktie {ticker}: {error}"
            )

    if not results:
        return

    if OUTPUT_PATH.exists():
        cache = pd.read_csv(OUTPUT_PATH)
    else:
        cache = pd.DataFrame()

    updated_cache = cache.copy()

    for data in results:
        ticker = data["Ticker"]

        if not updated_cache.empty:
            updated_cache = updated_cache[
                ~updated_cache["Ticker"]
                .astype(str)
                .str.upper()
                .eq(ticker.upper())
            ]

        updated_cache = pd.concat(
            [updated_cache, pd.DataFrame([data])],
            ignore_index=True,
        )

    updated_cache.to_csv(
        OUTPUT_PATH,
        index=False,
    )


def update_benchmark() -> None:
    universe = load_universe()

    results = []

    for _, row in universe.iterrows():
        ticker = row["Ticker"]

        print(f"Lade {ticker}...")

        try:
            data = load_company_snapshot(ticker)
            data = apply_current_intelligence(data)
            data = add_investment_decision_to_data(data)

            results.append(data)

        except Exception as error:
            print(f"Fehler bei {ticker}: {error}")

    pd.DataFrame(results).to_csv(
        OUTPUT_PATH,
        index=False,
    )

if __name__ == "__main__":
    update_benchmark()