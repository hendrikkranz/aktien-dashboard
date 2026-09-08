from datetime import date
from pathlib import Path

import pandas as pd


QUALITATIVE_QUALITY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "qualitative_quality.csv"
)

QUALITATIVE_QUALITY_COLUMNS = [
    "Ticker",
    "Faktor",
    "Bewertung",
    "Status",
    "Quelle",
    "Stand",
    "Begründung",
    "Hauptkonkurrenten",
]


def load_qualitative_quality() -> pd.DataFrame:
    if not QUALITATIVE_QUALITY_PATH.exists():
        return pd.DataFrame(
            columns=QUALITATIVE_QUALITY_COLUMNS
        )

    quality_df = pd.read_csv(QUALITATIVE_QUALITY_PATH)

    # Abwärtskompatibilität mit bestehenden CSV-Dateien
    for column in QUALITATIVE_QUALITY_COLUMNS:
        if column not in quality_df.columns:
            quality_df[column] = None

    return quality_df[QUALITATIVE_QUALITY_COLUMNS]


def get_qualitative_quality_ratings(
    ticker: str,
) -> dict:
    quality_df = load_qualitative_quality()

    if quality_df.empty:
        return {}

    matches = quality_df[
        quality_df["Ticker"] == ticker
    ]

    ratings = {}

    for _, row in matches.iterrows():
        factor = row.get("Faktor")
        rating = row.get("Bewertung")

        if pd.isna(factor) or pd.isna(rating):
            continue

        ratings[str(factor)] = rating

    return ratings


def get_qualitative_quality_details(
    ticker: str,
) -> dict:
    quality_df = load_qualitative_quality()

    if quality_df.empty:
        return {}

    matches = quality_df[
        quality_df["Ticker"] == ticker
    ]

    details = {}

    for _, row in matches.iterrows():
        factor = row.get("Faktor")
        rating = row.get("Bewertung")

        if pd.isna(factor):
            continue

        competitors = row.get("Hauptkonkurrenten")

        details[str(factor)] = {
            "rating": (
                None
                if pd.isna(rating)
                else rating
            ),
            "status": row.get("Status"),
            "source": row.get("Quelle"),
            "date": row.get("Stand"),
            "reason": row.get("Begründung"),
            "competitors": (
                None
                if pd.isna(competitors)
                else str(competitors)
            ),
        }

    return details


def save_qualitative_quality_research(
    research_result: dict,
) -> None:
    ticker = research_result.get("Ticker")
    factors = research_result.get("Faktoren", {})

    if not ticker:
        raise ValueError(
            "Ticker fehlt im Rechercheergebnis."
        )

    if not factors:
        raise ValueError(
            "Keine qualitativen Faktoren im Rechercheergebnis."
        )

    quality_df = load_qualitative_quality()

    # Vorhandene Bewertung dieses Titels entfernen.
    quality_df = quality_df[
        quality_df["Ticker"] != ticker
    ].copy()

    sources = research_result.get("Quellen", [])

    source_titles = []
    for source in sources:
        if not isinstance(source, dict):
            continue

        title = source.get("Titel")
        if title and title not in source_titles:
            source_titles.append(title)

    source_text = (
        " | ".join(source_titles[:8])
        if source_titles
        else "Gemini mit Google Search"
    )

    rows = []

    for factor, details in factors.items():
        if not isinstance(details, dict):
            continue

        competitors = details.get(
            "Hauptkonkurrenten"
        )

        if isinstance(competitors, list):
            competitors_text = " · ".join(
                str(item).strip()
                for item in competitors
                if str(item).strip()
            )
        else:
            competitors_text = None

        rows.append(
            {
                "Ticker": ticker,
                "Faktor": factor,
                "Bewertung": details.get(
                    "Bewertung"
                ),
                "Status": details.get(
                    "Status"
                ),
                "Quelle": source_text,
                "Stand": date.today().isoformat(),
                "Begründung": details.get(
                    "Begründung"
                ),
                "Hauptkonkurrenten": (
                    competitors_text
                    if factor
                    == "Burggraben / Wettbewerbsposition"
                    else None
                ),
            }
        )

    if not rows:
        raise ValueError(
            "Keine speicherbaren Faktoren gefunden."
        )

    new_rows = pd.DataFrame(
        rows,
        columns=QUALITATIVE_QUALITY_COLUMNS,
    )

    quality_df = pd.concat(
        [quality_df, new_rows],
        ignore_index=True,
    )

    quality_df.to_csv(
        QUALITATIVE_QUALITY_PATH,
        index=False,
    )
