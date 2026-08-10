from pathlib import Path
import sys

import pandas as pd

INRA_ROOT = Path(__file__).resolve().parent.parent

if str(INRA_ROOT) not in sys.path:
    sys.path.insert(0, str(INRA_ROOT))

from utils.market_data import load_company_snapshot


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

def update_benchmark() -> None:
    universe = load_universe()

    results = []

    for _, row in universe.iterrows():
        ticker = row["Ticker"]

        print(f"Lade {ticker}...")

        try:
            data = load_company_snapshot(ticker)

            results.append(data)

        except Exception as error:
            print(f"Fehler bei {ticker}: {error}")

    pd.DataFrame(results).to_csv(
        OUTPUT_PATH,
        index=False,
    )

if __name__ == "__main__":
    update_benchmark()