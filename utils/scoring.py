import pandas as pd


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
