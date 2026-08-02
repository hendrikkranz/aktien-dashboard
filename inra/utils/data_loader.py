from pathlib import Path

import pandas as pd


UNIVERSE_PATH = Path("inra/data/universe.csv")


def load_universe() -> pd.DataFrame:
    return pd.read_csv(UNIVERSE_PATH)