from typing import Dict, List, Optional

from utils.fundamental_interpreter import (
    interpret_debt_equity,
    interpret_net_margin,
    interpret_revenue_growth,
    interpret_roe,
)


Interpretation = Optional[Dict[str, object]]


def format_list(items: List[str]) -> str:
    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return " und ".join(items)

    return ", ".join(items[:-1]) + " sowie " + items[-1]


def create_investment_summary(data: dict) -> str:
    interpretations = (
        interpret_roe(data.get("Eigenkapitalrendite")),
        interpret_net_margin(data.get("Nettomarge")),
        interpret_revenue_growth(data.get("Umsatzwachstum")),
        interpret_debt_equity(data.get("Verschuldungsgrad")),
    )

    strengths = []
    neutral_observations = []
    warnings = []

    for result in interpretations:
        if result is None:
            continue

        text = result.get("text")
        category = result.get("category")

        if not isinstance(text, str):
            continue

        if category == "strength":
            strengths.append(text)
        elif category == "warning":
            warnings.append(text)
        else:
            neutral_observations.append(text)

    sentences = []

    if strengths:
        sentences.append(
            f"Zu den Stärken zählen {format_list(strengths)}."
        )

    if neutral_observations:
        if len(neutral_observations) == 1:
            sentences.append(
                f"Neutral einzuordnen ist {neutral_observations[0]}."
            )
        else:
            sentences.append(
                f"Neutral einzuordnen sind "
                f"{format_list(neutral_observations)}."
            )

    if warnings:
        if len(warnings) == 1:
            sentences.append(
                f"Zu beachten ist {warnings[0]}."
            )
        else:
            sentences.append(
                f"Zu beachten sind {format_list(warnings)}."
            )

    if not sentences:
        return (
            "Für eine belastbare fundamentale Einordnung "
            "liegen derzeit nicht genügend Daten vor."
        )

    return " ".join(sentences)