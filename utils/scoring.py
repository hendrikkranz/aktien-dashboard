import pandas as pd
def calculate_value_score(row):
    """Berechnet den Value Score (0–100)."""

    score = 0

    peg = row.get("PEG")
    forward_pe = row.get("Forward KGV")

    if pd.notna(peg):
        if 0 < peg <= 1:
            score += 40
        elif peg <= 1.5:
            score += 30
        elif peg <= 2:
            score += 20
        elif peg <= 3:
            score += 10

        

    if pd.notna(forward_pe) and forward_pe > 0:
        if forward_pe <= 12:
            score += 30
        elif forward_pe <= 18:
            score += 22
        elif forward_pe <= 25:
            score += 14
        elif forward_pe <= 35:
            score += 6

    return score


def calculate_score(row):

    score = 0

    # Performance
    if row["Live Gewinn Verlust Prozent"] > 20:
        score += 20

    # Diversifikation
    if row["Live Gewichtung Prozent"] < 10:
        score += 15

    # Dividende
    if row.get("Dividend Yield", 0) > 2:
        score += 15

    # Gewinnwachstum
    if row.get("Earnings Growth", 0) > 0.10:
        score += 20

    # Umsatzwachstum
    if row.get("Revenue Growth", 0) > 0.08:
        score += 15

    # Bewertung
    pe = row.get("PE Ratio", 999)

    if 10 < pe < 25:
        score += 15

    return score
