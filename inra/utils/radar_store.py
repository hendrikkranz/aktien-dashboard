from datetime import datetime
from pathlib import Path

import pandas as pd


RADAR_PATH = Path("data/radar.csv")

RADAR_COLUMNS = [
    "Ticker",
    "Name",
    "Aufgenommen am",
    "Referenzkurs",
]


def load_radar():
    if not RADAR_PATH.exists():
        return pd.DataFrame(columns=RADAR_COLUMNS)

    try:
        radar = pd.read_csv(RADAR_PATH)
    except (pd.errors.EmptyDataError, OSError):
        return pd.DataFrame(columns=RADAR_COLUMNS)

    for column in RADAR_COLUMNS:
        if column not in radar.columns:
            radar[column] = None

    return radar[RADAR_COLUMNS]


def is_on_radar(ticker):
    ticker = str(ticker or "").strip().upper()

    if not ticker:
        return False

    radar = load_radar()

    if radar.empty:
        return False

    return ticker in radar["Ticker"].astype(str).str.upper().values


def add_to_radar(ticker, name, reference_price):
    ticker = str(ticker or "").strip().upper()

    if not ticker:
        return False

    radar = load_radar()

    if is_on_radar(ticker):
        return False

    new_row = pd.DataFrame(
        [
            {
                "Ticker": ticker,
                "Name": str(name or "").strip(),
                "Aufgenommen am": datetime.now().astimezone().isoformat(
                    timespec="seconds"
                ),
                "Referenzkurs": reference_price,
            }
        ]
    )

    if radar.empty:
        radar = new_row
    else:
        radar = pd.concat(
            [radar, new_row],
            ignore_index=True,
        )

    RADAR_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    radar.to_csv(
        RADAR_PATH,
        index=False,
    )

    return True


def remove_from_radar(ticker):
    ticker = str(ticker or "").strip().upper()

    radar = load_radar()

    if radar.empty:
        return False

    keep = (
        radar["Ticker"]
        .astype(str)
        .str.upper()
        != ticker
    )

    if keep.all():
        return False

    radar = radar.loc[keep].copy()

    radar.to_csv(
        RADAR_PATH,
        index=False,
    )

    return True
