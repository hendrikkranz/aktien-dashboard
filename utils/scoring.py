import pandas as pd


def safe_number(value):
    """Wandelt einen Wert sicher in eine Zahl um."""
    if value is None or pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_score(row):
    """
    Fundamental-Score Version 1: 0 bis 100 Punkte.

    Bewertung:
    - Bewertung: 30 Punkte
    - Wachstum: 40 Punkte
    - Dividendenqualität: 20 Punkte
    - Depotkontext: 10 Punkte
    """

    score = 0

    forward_pe = safe_number(row.get("Forward KGV"))
    trailing_pe = safe_number(row.get("KGV"))
    revenue_growth = safe_number(
        row.get("Umsatzwachstum Prozent")
    )
    earnings_growth = safe_number(
        row.get("Gewinnwachstum Prozent")
    )
    dividend_yield = safe_number(
        row.get("Dividendenrendite Prozent")
    )
    payout_ratio = safe_number(
        row.get("Ausschüttungsquote Prozent")
    )
    portfolio_weight = safe_number(
        row.get("Live Gewichtung Prozent")
    )

    # 1. Bewertung – maximal 30 Punkte

    if forward_pe is not None:
        if 0 < forward_pe <= 15:
            score += 18
        elif forward_pe <= 22:
            score += 14
        elif forward_pe <= 30:
            score += 9
        elif forward_pe <= 40:
            score += 4

    if trailing_pe is not None:
        if 0 < trailing_pe <= 15:
            score += 12
        elif trailing_pe <= 22:
            score += 9
        elif trailing_pe <= 30:
            score += 6
        elif trailing_pe <= 40:
            score += 3

    # 2. Wachstum – maximal 40 Punkte

    if revenue_growth is not None:
        if revenue_growth >= 15:
            score += 18
        elif revenue_growth >= 8:
            score += 14
        elif revenue_growth >= 3:
            score += 8
        elif revenue_growth > 0:
            score += 4

    if earnings_growth is not None:
        if earnings_growth >= 20:
            score += 22
        elif earnings_growth >= 10:
            score += 17
        elif earnings_growth >= 5:
            score += 11
        elif earnings_growth > 0:
            score += 5

    # 3. Dividendenqualität – maximal 20 Punkte

    if dividend_yield is not None:
        if 1.5 <= dividend_yield <= 5:
            score += 10
        elif 0.5 <= dividend_yield < 1.5:
            score += 6
        elif 5 < dividend_yield <= 8:
            score += 5

    if payout_ratio is not None:
        if 20 <= payout_ratio <= 60:
            score += 10
        elif 0 < payout_ratio < 20:
            score += 7
        elif 60 < payout_ratio <= 80:
            score += 5

    # 4. Depotkontext – maximal 10 Punkte

    if portfolio_weight is not None:
        if portfolio_weight < 5:
            score += 10
        elif portfolio_weight < 10:
            score += 6
        elif portfolio_weight < 15:
            score += 3

    return min(score, 100)
