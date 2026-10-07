from datetime import date
from pathlib import Path

import pandas as pd


SPECIAL_QUANTITATIVE_QUALITY_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "special_quantitative_quality.csv"
)

SPECIAL_QUANTITATIVE_QUALITY_COLUMNS = [
    "Ticker",
    "Dimension",
    "Urteil",
    "Kennzahlen",
    "Quelle",
    "Stand",
    "Begründung",
]


def load_special_quantitative_quality() -> pd.DataFrame:
    if not SPECIAL_QUANTITATIVE_QUALITY_PATH.exists():
        return pd.DataFrame(
            columns=SPECIAL_QUANTITATIVE_QUALITY_COLUMNS
        )

    quality_df = pd.read_csv(
        SPECIAL_QUANTITATIVE_QUALITY_PATH
    )

    for column in SPECIAL_QUANTITATIVE_QUALITY_COLUMNS:
        if column not in quality_df.columns:
            quality_df[column] = None

    return quality_df[
        SPECIAL_QUANTITATIVE_QUALITY_COLUMNS
    ]


def get_special_quantitative_quality_details(
    ticker: str,
) -> dict:
    quality_df = load_special_quantitative_quality()

    if quality_df.empty:
        return {}

    matches = quality_df[
        quality_df["Ticker"] == ticker
    ]

    details = {}

    for _, row in matches.iterrows():
        dimension = row.get("Dimension")

        if pd.isna(dimension):
            continue

        metrics = row.get("Kennzahlen")

        details[str(dimension)] = {
            "rating": (
                None
                if pd.isna(row.get("Urteil"))
                else str(row.get("Urteil"))
            ),
            "metrics": (
                []
                if pd.isna(metrics)
                else [
                    item.strip()
                    for item in str(metrics).split(" · ")
                    if item.strip()
                ]
            ),
            "source": row.get("Quelle"),
            "date": row.get("Stand"),
            "reason": row.get("Begründung"),
        }

    return details


def save_special_quantitative_quality_research(
    research_result: dict,
) -> None:
    ticker = research_result.get("Ticker")
    dimensions = research_result.get(
        "Dimensionen",
        {},
    )

    if not ticker:
        raise ValueError(
            "Ticker fehlt im Rechercheergebnis."
        )

    if not dimensions:
        raise ValueError(
            "Keine Sonderanalyse im Rechercheergebnis."
        )

    quality_df = load_special_quantitative_quality()

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

    for dimension, details in dimensions.items():
        if not isinstance(details, dict):
            continue

        metrics = details.get("Kennzahlen", [])

        metrics_text = " · ".join(
            str(item).strip()
            for item in metrics
            if str(item).strip()
        )

        rows.append(
            {
                "Ticker": ticker,
                "Dimension": dimension,
                "Urteil": details.get("Urteil"),
                "Kennzahlen": metrics_text or None,
                "Quelle": source_text,
                "Stand": date.today().isoformat(),
                "Begründung": details.get("Begründung"),
            }
        )

    if not rows:
        raise ValueError(
            "Keine speicherbaren Dimensionen gefunden."
        )

    new_rows = pd.DataFrame(
        rows,
        columns=SPECIAL_QUANTITATIVE_QUALITY_COLUMNS,
    )

    quality_df = pd.concat(
        [quality_df, new_rows],
        ignore_index=True,
    )

    quality_df.to_csv(
        SPECIAL_QUANTITATIVE_QUALITY_PATH,
        index=False,
    )
