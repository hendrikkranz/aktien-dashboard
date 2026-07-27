import pandas as pd


def _safe_value(value, default=0):
    """Ersetzt fehlende Kennzahlen durch einen neutralen Standardwert."""
    if pd.isna(value):
        return default

    return value


def get_recommendation(row, strategy="default"):
    """
    Ermittelt eine Investment-Empfehlung.

    Profile:
    - default: Qualitäts- und Wachstumsaktien
    - dividend: Dividendenaktien
    """

    score = _safe_value(row.get("Score"))
    analystenpotenzial = _safe_value(
        row.get("Analystenpotenzial Prozent")
    )
    momentum_score = _safe_value(
        row.get("Momentum Score")
    )
    gewinnwachstum = _safe_value(
        row.get("Gewinnwachstum Prozent")
    )
    dividendenrendite = _safe_value(
        row.get("Dividendenrendite Prozent")
    )

    ausschüttungsquote = row.get(
        "Ausschüttungsquote Prozent"
    )

    # Eigenes Profil für Dividendenaktien
    if strategy == "dividend":

        # Klare Warnsignale
        if (
            score < 40
            or gewinnwachstum < -30
            or momentum_score < 15
        ):
            return "🔴 Vorsicht"

        nachhaltige_ausschüttung = (
            pd.isna(ausschüttungsquote)
            or 0 <= ausschüttungsquote <= 90
        )

        # Attraktive Dividendenaktie mit positivem Gesamtbild
        if (
            score >= 62
            and dividendenrendite >= 2
            and momentum_score >= 40
            and gewinnwachstum >= -5
            and nachhaltige_ausschüttung
        ):
            return "🟢 Kaufkandidat"

        # Gute Dividendenaktie, aber noch kein klares Kaufsignal
        if (
            score >= 55
            and dividendenrendite >= 1.5
        ):
            return "🟡 Beobachten"

        if score >= 45:
            return "🔵 Halten"

        return "🔴 Vorsicht"

    # Standardprofil für Dauergewinner
    if (
        score < 45
        or gewinnwachstum < -20
        or momentum_score < 20
    ):
        return "🔴 Vorsicht"

    if (
        score >= 75
        and analystenpotenzial >= 10
        and momentum_score >= 55
        and gewinnwachstum > 0
    ):
        return "🟢 Kaufkandidat"

    if score >= 65:
        return "🟡 Beobachten"

    if score >= 50:
        return "🔵 Halten"

    return "🔴 Vorsicht"