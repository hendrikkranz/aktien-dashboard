from typing import Optional


def _result(
    level: str,
    score: int,
    category: str,
    text: str,
    label: Optional[str] = None,
) -> dict:
    result = {
        "level": level,
        "score": score,
        "category": category,
        "text": text,
    }

    if label is not None:
        result["label"] = label

    return result


def interpret_roe(value: Optional[float]) -> Optional[dict]:
    if value is None:
        return None

    if value >= 25:
        return _result(
            "excellent",
            5,
            "strength",
            "eine außergewöhnlich hohe Eigenkapitalrendite",
        )
    if value >= 15:
        return _result(
            "good",
            4,
            "strength",
            "eine starke Eigenkapitalrendite",
        )
    if value >= 10:
        return _result(
            "solid",
            3,
            "neutral",
            "eine solide Eigenkapitalrendite",
        )
    if value >= 5:
        return _result(
            "weak",
            2,
            "warning",
            "eine eher niedrige Eigenkapitalrendite",
        )

    return _result(
        "poor",
        1,
        "warning",
        "eine schwache Eigenkapitalrendite",
    )


def interpret_net_margin(
    value: Optional[float],
) -> Optional[dict]:
    if value is None:
        return None

    if value >= 25:
        return _result(
            "excellent",
            5,
            "strength",
            "eine außergewöhnlich hohe Nettomarge",
        )
    if value >= 15:
        return _result(
            "good",
            4,
            "strength",
            "eine starke Nettomarge",
        )
    if value >= 8:
        return _result(
            "solid",
            3,
            "neutral",
            "eine solide Nettomarge",
        )
    if value >= 3:
        return _result(
            "weak",
            2,
            "warning",
            "eine eher niedrige Nettomarge",
        )

    return _result(
        "poor",
        1,
        "warning",
        "eine schwache Nettomarge",
    )

def interpret_operating_margin(
    value: Optional[float],
) -> Optional[dict]:
    if value is None:
        return None

    if value >= 30:
        return _result(
            "excellent",
            5,
            "strength",
            "eine außergewöhnlich hohe operative Marge",
        )
    if value >= 20:
        return _result(
            "good",
            4,
            "strength",
            "eine starke operative Marge",
        )
    if value >= 10:
        return _result(
            "solid",
            3,
            "neutral",
            "eine solide operative Marge",
        )
    if value >= 5:
        return _result(
            "weak",
            2,
            "warning",
            "eine eher niedrige operative Marge",
        )

    return _result(
        "poor",
        1,
        "warning",
        "eine schwache operative Marge",
    )


def interpret_revenue_growth(
    value: Optional[float],
) -> Optional[dict]:
    if value is None:
        return None

    if value >= 15:
        return _result(
            "excellent",
            5,
            "strength",
            "ein starkes Umsatzwachstum",
        )
    if value >= 6:
        return _result(
            "solid",
            3,
            "neutral",
            "ein solides Umsatzwachstum",
        )
    if value >= 0:
        return _result(
            "solid",
            3,
            "neutral",
            "ein verhaltenes Umsatzwachstum",
        )
    if value >= -5:
        return _result(
            "weak",
            2,
            "warning",
            "einen leichten Umsatzrückgang",
        )

    return _result(
        "poor",
        1,
        "warning",
        "einen deutlichen Umsatzrückgang",
    )


def interpret_debt_equity(
    value: Optional[float],
) -> Optional[dict]:
    if value is None:
        return None

    if value <= 40:
        return _result(
            "excellent",
            5,
            "strength",
            "eine sehr solide Bilanz",
        )
    if value <= 100:
        return _result(
            "good",
            4,
            "strength",
            "eine solide Bilanz",
        )
    if value <= 200:
        return _result(
            "weak",
            2,
            "warning",
            "eine erhöhte Verschuldung",
        )

    return _result(
        "poor",
        1,
        "warning",
        "eine hohe Verschuldung",
    )


def interpret_dividend_yield(
    value: Optional[float],
) -> Optional[dict]:
    if value is None or value <= 0:
        return None

    if value >= 5:
        return _result(
            "excellent",
            5,
            "strength",
            "eine hohe Dividendenrendite",
        )
    if value >= 3:
        return _result(
            "good",
            4,
            "strength",
            "eine attraktive Dividendenrendite",
        )
    if value >= 1:
        return _result(
            "solid",
            3,
            "neutral",
            "eine moderate Dividendenrendite",
        )

    return _result(
        "low",
        2,
        "neutral",
        "eine niedrige Dividendenrendite",
    )


def interpret_momentum(
    value: Optional[float],
) -> Optional[dict]:
    if value is None:
        return None

    if value >= 20:
        return _result(
            "excellent",
            5,
            "strength",
            "ein sehr starkes Momentum",
        )

    if value >= 10:
        return _result(
            "good",
            4,
            "strength",
            "ein starkes Momentum",
        )

    if value >= 0:
        return _result(
            "solid",
            3,
            "neutral",
            "ein positives Momentum",
        )

    if value >= -10:
        return _result(
            "weak",
            2,
            "warning",
            "ein schwaches Momentum",
        )

    return _result(
        "poor",
        1,
        "warning",
        "ein deutlich negatives Momentum",
    )

def interpret_rsi(
    value: Optional[float],
) -> Optional[dict]:
    if value is None:
        return None

    if value >= 70:
        return _result(
            "poor",
            1,
            "warning",
            "eine überkaufte Situation",
        )

    if value >= 60:
        return _result(
            "weak",
            2,
            "warning",
            "ein erhöhtes Kursniveau",
        )

    if value >= 40:
        return _result(
            "good",
            4,
            "neutral",
            "ein neutrales Kursniveau",
        )

    if value >= 30:
        return _result(
            "weak",
            2,
            "warning",
            "ein erhöhtes Rückschlagpotenzial",
        )

    return _result(
        "excellent",
        5,
        "strength",
        "eine überverkaufte Situation",
    )