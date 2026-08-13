from pathlib import Path

import pandas as pd
import yfinance as yf


UNIVERSE_PATH = Path("inra/data/universe.csv")


DAX_TICKERS = [
    "ADS.DE",
    "AIR.DE",
    "ALV.DE",
    "BAS.DE",
    "BAYN.DE",
    "BEI.DE",
    "BMW.DE",
    "BNR.DE",
    "CBK.DE",
    "CON.DE",
    "DB1.DE",
    "DBK.DE",
    "DHL.DE",
    "DTE.DE",
    "DTG.DE",
    "ENR.DE",
    "EOAN.DE",
    "FME.DE",
    "FRE.DE",
    "G1A.DE",
    "G24.DE",
    "HEI.DE",
    "HEN3.DE",
    "HNR1.DE",
    "HOT.DE",
    "IFX.DE",
    "MBG.DE",
    "MRK.DE",
    "MTX.DE",
    "MUV2.DE",
    "QIA.DE",
    "RHM.DE",
    "RWE.DE",
    "SAP.DE",
    "SHL.DE",
    "SIE.DE",
    "SY1.DE",
    "VNA.DE",
    "VOW3.DE",
    "ZAL.DE",
]


def add_list_value(current_value, new_value: str) -> str:
    values = []

    if pd.notna(current_value):
        values = [
            value.strip()
            for value in str(current_value).split(";")
            if value.strip()
        ]

    if new_value not in values:
        values.append(new_value)

    return ";".join(values)


def load_company_data(ticker: str) -> dict:
    print(f"Lade {ticker}...")

    info = yf.Ticker(ticker).get_info()

    return {
        "Ticker": ticker,
        "Name": (
            info.get("longName")
            or info.get("shortName")
            or ticker
        ),
        "Land": info.get("country") or "Germany",
        "Sektor": info.get("sector"),
        "Branche": info.get("industry"),
        "Liste": "DAX",
    }


def main() -> None:
    universe = pd.read_csv(UNIVERSE_PATH)

    existing_tickers = set(
        universe["Ticker"]
        .dropna()
        .astype(str)
    )

    missing_tickers = [
        ticker
        for ticker in DAX_TICKERS
        if ticker not in existing_tickers
    ]

    print(
        f"Bereits vorhanden: "
        f"{len(DAX_TICKERS) - len(missing_tickers)}"
    )
    print(
        f"Neu hinzuzufügen: {len(missing_tickers)}"
    )

    for ticker in DAX_TICKERS:
        mask = universe["Ticker"] == ticker

        if mask.any():
            universe.loc[
                mask,
                "Liste",
            ] = universe.loc[
                mask,
                "Liste",
            ].apply(
                lambda value: add_list_value(
                    value,
                    "DAX",
                )
            )

    new_rows = []

    for ticker in missing_tickers:
        try:
            new_rows.append(
                load_company_data(ticker)
            )
        except Exception as exc:
            print(
                f"Fehler bei {ticker}: {exc}"
            )

    if new_rows:
        new_df = pd.DataFrame(new_rows)

        for column in universe.columns:
            if column not in new_df.columns:
                new_df[column] = None

        new_df = new_df[
            universe.columns
        ]

        universe = pd.concat(
            [
                universe,
                new_df,
            ],
            ignore_index=True,
        )

    universe = (
        universe
        .drop_duplicates(
            subset=["Ticker"],
            keep="first",
        )
        .sort_values(
            by=["Name", "Ticker"],
            na_position="last",
        )
        .reset_index(drop=True)
    )

    universe.to_csv(
        UNIVERSE_PATH,
        index=False,
    )

    print()
    print(
        f"Universum gespeichert: "
        f"{len(universe)} Aktien"
    )

    dax_count = (
        universe["Liste"]
        .fillna("")
        .str.contains(
            "DAX",
            regex=False,
        )
        .sum()
    )

    print(
        f"DAX-markierte Aktien: {dax_count}"
    )


if __name__ == "__main__":
    main()