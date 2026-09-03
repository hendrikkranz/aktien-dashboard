from pathlib import Path

import pandas as pd


RESEARCH_ADJUSTMENTS_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "research_adjustments.csv"
)


def load_research_adjustments() -> pd.DataFrame:
    if not RESEARCH_ADJUSTMENTS_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(RESEARCH_ADJUSTMENTS_PATH)

def apply_research_adjustments(
    snapshot: dict,
    ticker: str,
) -> dict:
    """
    Wendet fachliche Research-Bereinigungen auf einen
    vollständig aufgebauten Unternehmens-Snapshot an.
    """
    research_df = load_research_adjustments()

    if research_df.empty:
        adjustments = []
    else:
        adjustments = (
            research_df[research_df["Ticker"] == ticker]
            .to_dict("records")
        )

    for adjustment in adjustments:
        original_field = adjustment.get("Originalfeld")
        replacement_value = adjustment.get("Ersatzwert")

        if (
            original_field
            and replacement_value is not None
        ):
            adjustment["Originalwert"] = snapshot.get(
                original_field
            )
            snapshot[original_field] = replacement_value
            adjustment["Angewendet"] = True
        else:
            adjustment["Angewendet"] = False

    snapshot["Research Bereinigung aktiv"] = bool(
        adjustments
    )
    snapshot["Research Bereinigungen"] = adjustments

    return snapshot