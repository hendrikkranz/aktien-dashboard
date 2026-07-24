import pandas as pd


<<<<<<< HEAD
def safe_number(value):
    """Wandelt einen Wert sicher in eine Zahl um."""
    if value is None or pd.isna(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None
=======
def calculate_value_score(row):
    """Berechnet den Value Score von 0 bis 100 Punkten."""

    score = 0

    peg = row.get("PEG")
    forward_pe = row.get("Forward KGV")
    analyst_upside = row.get("Analystenpotenzial Prozent")

    # PEG: maximal 40 Punkte
    if pd.notna(peg):
        if 0 < peg <= 1:
            score += 40
        elif peg <= 1.5:
            score += 30
        elif peg <= 2:
            score += 20
        elif peg <= 3:
            score += 10

    # Forward KGV: maximal 30 Punkte
    if pd.notna(forward_pe) and forward_pe > 0:
        if forward_pe <= 12:
            score += 30
        elif forward_pe <= 18:
            score += 22
        elif forward_pe <= 25:
            score += 14
        elif forward_pe <= 35:
            score += 6

    # Analystenpotenzial: maximal 30 Punkte
    if pd.notna(analyst_upside):
        if analyst_upside >= 25:
            score += 30
        elif analyst_upside >= 15:
            score += 22
        elif analyst_upside >= 5:
            score += 14
        elif analyst_upside >= 0:
            score += 6

    return min(score, 100)


def calculate_growth_score(row):
    """Berechnet den Growth Score von 0 bis 100 Punkten."""

    score = 0

    earnings_growth = row.get("Gewinnwachstum Prozent")
    revenue_growth = row.get("Umsatzwachstum Prozent")

    # Gewinnwachstum: maximal 60 Punkte
    if pd.notna(earnings_growth):
        if earnings_growth >= 25:
            score += 60
        elif earnings_growth >= 15:
            score += 48
        elif earnings_growth >= 10:
            score += 38
        elif earnings_growth >= 5:
            score += 25
        elif earnings_growth >= 0:
            score += 10

    # Umsatzwachstum: maximal 40 Punkte
    if pd.notna(revenue_growth):
        if revenue_growth >= 20:
            score += 40
        elif revenue_growth >= 12:
            score += 32
        elif revenue_growth >= 8:
            score += 24
        elif revenue_growth >= 3:
            score += 15
        elif revenue_growth >= 0:
            score += 6

    return min(score, 100)


def calculate_quality_score(row):
    """
    Berechnet einen vorläufigen Quality Score von 0 bis 100 Punkten.

    Später ergänzen wir ROE, ROIC, Verschuldung und Margen.
    """

    score = 0

    trailing_eps = row.get("Trailing EPS")
    forward_eps = row.get("Forward EPS")
    payout_ratio = row.get("Ausschüttungsquote Prozent")
    dividend_yield = row.get("Dividendenrendite Prozent")
    earnings_growth = row.get("Gewinnwachstum Prozent")

    # Aktuell profitables Unternehmen: maximal 30 Punkte
    if pd.notna(trailing_eps) and trailing_eps > 0:
        score += 30

    # Positive Gewinnerwartung: maximal 25 Punkte
    if pd.notna(forward_eps) and forward_eps > 0:
        score += 15

        if (
            pd.notna(trailing_eps)
            and trailing_eps > 0
            and forward_eps >= trailing_eps
        ):
            score += 10

    # Nachhaltige Ausschüttungsquote: maximal 25 Punkte
    # Unternehmen ohne Dividende werden nicht bestraft.
    if pd.notna(dividend_yield) and dividend_yield > 0:
        if pd.notna(payout_ratio):
            if 20 <= payout_ratio <= 60:
                score += 25
            elif 0 <= payout_ratio < 20:
                score += 18
            elif 60 < payout_ratio <= 80:
                score += 15
            elif 80 < payout_ratio <= 100:
                score += 5
    else:
        score += 25

    # Positives Gewinnwachstum: maximal 20 Punkte
    if pd.notna(earnings_growth):
        if earnings_growth >= 10:
            score += 20
        elif earnings_growth >= 5:
            score += 15
        elif earnings_growth >= 0:
            score += 8

    return min(score, 100)


def calculate_momentum_score(row):
    """Berechnet den Momentum Score von 0 bis 100 Punkten."""

    score = 0

    distance_sma_50 = row.get(
        "Abstand 50-Tage-Linie Prozent"
    )
    distance_sma_200 = row.get(
        "Abstand 200-Tage-Linie Prozent"
    )
    momentum_3m = row.get(
        "Momentum 3 Monate Prozent"
    )
    momentum_6m = row.get(
        "Momentum 6 Monate Prozent"
    )

    # Abstand zur 200-Tage-Linie: maximal 35 Punkte
    if pd.notna(distance_sma_200):
        if 0 <= distance_sma_200 <= 15:
            score += 35
        elif -10 <= distance_sma_200 < 0:
            score += 22
        elif 15 < distance_sma_200 <= 30:
            score += 18
        elif -20 <= distance_sma_200 < -10:
            score += 8

    # Abstand zur 50-Tage-Linie: maximal 20 Punkte
    if pd.notna(distance_sma_50):
        if 0 <= distance_sma_50 <= 10:
            score += 20
        elif -5 <= distance_sma_50 < 0:
            score += 12
        elif 10 < distance_sma_50 <= 20:
            score += 8

    # Momentum drei Monate: maximal 20 Punkte
    if pd.notna(momentum_3m):
        if 5 <= momentum_3m <= 20:
            score += 20
        elif 0 < momentum_3m < 5:
            score += 12
        elif 20 < momentum_3m <= 35:
            score += 8

    # Momentum sechs Monate: maximal 25 Punkte
    if pd.notna(momentum_6m):
        if 10 <= momentum_6m <= 30:
            score += 25
        elif 0 < momentum_6m < 10:
            score += 16
        elif 30 < momentum_6m <= 50:
            score += 10

    return min(score, 100)
>>>>>>> 7f8fdf4 (Teil-Scores für Quality, Value, Growth und Momentum ergänzen)


def calculate_score(row):
    """
    Berechnet den gewichteten Gesamtscore.

    Gewichtung:
    - Quality: 35 Prozent
    - Value: 30 Prozent
    - Growth: 20 Prozent
    - Momentum: 15 Prozent
    """

    quality_score = calculate_quality_score(row)
    value_score = calculate_value_score(row)
    growth_score = calculate_growth_score(row)
    momentum_score = calculate_momentum_score(row)

    total_score = (
        quality_score * 0.35
        + value_score * 0.30
        + growth_score * 0.20
        + momentum_score * 0.15
    )

    return min(round(total_score), 100)