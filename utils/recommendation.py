import pandas as pd


def get_recommendation(row):
    """
    Ermittelt eine einfache Investment-Empfehlung.

    Grundlage:
    - Gesamtscore
    - Analystenpotenzial
    - Momentum-Score
    - Gewinnwachstum

    Rückgabe:
    - 🟢 Kaufkandidat
    - 🟡 Beobachten
    - 🔵 Halten
    - 🔴 Vorsicht
    """

    score = row.get("Score")
    analystenpotenzial = row.get(
        "Analystenpotenzial Prozent"
    )
    momentum_score = row.get("Momentum Score")
    gewinnwachstum = row.get(
        "Gewinnwachstum Prozent"
    )

    # Fehlende Werte neutral behandeln
    if pd.isna(score):
        score = 0

    if pd.isna(analystenpotenzial):
        analystenpotenzial = 0

    if pd.isna(momentum_score):
        momentum_score = 0

    if pd.isna(gewinnwachstum):
        gewinnwachstum = 0

    # Klare Warnsignale
    if (
        score < 45
        or gewinnwachstum < -20
        or momentum_score < 20
    ):
        return "🔴 Vorsicht"

    # Kaufkandidat nur bei mehreren positiven Signalen
    if (
        score >= 75
        and analystenpotenzial >= 10
        and momentum_score >= 55
        and gewinnwachstum > 0
    ):
        return "🟢 Kaufkandidat"

    # Gute Aktie, aber noch kein klares Kaufsignal
    if score >= 65:
        return "🟡 Beobachten"

    # Solides Mittelfeld
    if score >= 50:
        return "🔵 Halten"

    return "🔴 Vorsicht"