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

def detect_research_candidates(snapshot: dict) -> list:
    candidates = []

    if snapshot.get("Extremer Umsatzsprung"):
        candidates.append(
            {
                "Bereich": "Wachstum",
                "Kennzahl": "Umsatzwachstum",
                "Grund": "Extremer Umsatzsprung erkannt",
            }
        )

    if snapshot.get("Gewinn Vorzeichenwechsel"):
        candidates.append(
            {
                "Bereich": "Wachstum",
                "Kennzahl": "Gewinnwachstum",
                "Grund": "Vorzeichenwechsel beim Nettogewinn erkannt",
            }
        )

    return candidates

def apply_research_adjustments(
    snapshot: dict,
    ticker: str,
) -> dict:
    """
    Wendet fachliche Research-Bereinigungen auf einen
    vollständig aufgebauten Unternehmens-Snapshot an.
    """
    
    candidates = detect_research_candidates(snapshot)

    snapshot["Research Kandidaten"] = candidates
    snapshot["Research erforderlich"] = bool(candidates)
    
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
            and pd.notna(replacement_value)
        ):
            adjustment["Originalwert"] = snapshot.get(
                original_field
            )
            snapshot[original_field] = replacement_value
            adjustment["Angewendet"] = True
        else:
            adjustment["Angewendet"] = False

    resolved_metrics = {
        adjustment.get("Kennzahl")
        for adjustment in adjustments
        if (
            adjustment.get("Angewendet")
            or adjustment.get("Status") == "Research-geprüft"
        )
    }

    open_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("Kennzahl") not in resolved_metrics
    ]

    snapshot["Research Kandidaten offen"] = open_candidates
    snapshot["Research erforderlich"] = bool(open_candidates)

    snapshot["Research Bereinigung aktiv"] = bool(
        adjustments
    )
    snapshot["Research Bereinigungen"] = adjustments

    return snapshot