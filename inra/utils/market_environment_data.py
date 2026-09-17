"""
Datenebene für das InRA Market Risk Model V0.1.

Grundprinzipien:
- vorhandene InRA-Marktdatenfunktionen wiederverwenden
- fehlende Daten niemals künstlich als niedriges Risiko interpretieren
- Datenbeschaffung und Scoring strikt voneinander trennen
"""

from typing import Dict, Optional

import pandas as pd

from utils.market_data import load_price_history


MARKET_TREND_REGIONS = {
    "usa": {
        "name": "USA",
        "benchmark": "S&P 500",
        "ticker": "^GSPC",
        "weight": 0.40,
    },
    "europe": {
        "name": "Europa",
        "benchmark": "STOXX Europe 600",
        "ticker": "^STOXX",
        "weight": 0.25,
    },
    "china": {
        "name": "China",
        "benchmark": "MSCI China",
        "ticker": "MCHI",
        "weight": 0.20,
    },
    "em_ex_china": {
        "name": "EM ex China",
        "benchmark": "MSCI Emerging Markets ex China",
        "ticker": "EMXC",
        "weight": 0.15,
    },
}


def calculate_market_trend_metrics(
    price_history: pd.DataFrame,
) -> Optional[Dict[str, float]]:
    """
    Berechnet die Rohdaten für den Markttrend.

    Benötigt mindestens 220 Handelstage:
    - aktuelle 200-Tage-Linie
    - 200-Tage-Linie vor 20 Handelstagen

    Die eigentliche Risikobewertung erfolgt später separat
    in modules/market_risk_score.py.
    """

    if price_history.empty:
        return None

    prices = price_history.copy()

    prices = prices.sort_values("Datum")
    prices["SMA200"] = (
        prices["Schlusskurs"]
        .rolling(window=200)
        .mean()
    )

    valid = prices.dropna(
        subset=["Schlusskurs", "SMA200"]
    )

    if len(valid) < 21:
        return None

    current = valid.iloc[-1]
    previous = valid.iloc[-21]

    current_price = float(current["Schlusskurs"])
    current_sma200 = float(current["SMA200"])
    previous_sma200 = float(previous["SMA200"])

    if current_sma200 <= 0 or previous_sma200 <= 0:
        return None

    distance_to_sma200 = (
        current_price / current_sma200 - 1
    ) * 100

    sma200_slope_20d = (
        current_sma200 / previous_sma200 - 1
    ) * 100

    return {
        "price": current_price,
        "sma200": current_sma200,
        "distance_to_sma200_pct": distance_to_sma200,
        "sma200_slope_20d_pct": sma200_slope_20d,
    }


def load_market_trend_data(
    period: str = "2y",
) -> Dict[str, dict]:
    """
    Lädt die Markttrend-Rohdaten für alle V0.1-Regionen.

    Noch keine Risikopunkte:
    Diese Funktion liefert ausschließlich Daten und Kennzahlen.
    """

    results = {}

    for region_key, config in MARKET_TREND_REGIONS.items():
        history = load_price_history(
            config["ticker"],
            period=period,
        )

        metrics = calculate_market_trend_metrics(history)

        results[region_key] = {
            **config,
            "available": metrics is not None,
            "metrics": metrics,
        }

    return results


def build_market_trend_component(
    period: str = "2y",
) -> Dict[str, object]:
    """
    Erstellt den vollständigen regional gewichteten Markttrend-Baustein.

    Regionalgewichtung V0.1:
    - USA:        40 %
    - Europa:     25 %
    - China:      20 %
    - EM ex China 15 %

    Fehlende Regionen erhalten keine künstlichen 0 Risikopunkte.
    Die verfügbaren Regionalgewichte werden stattdessen auf 100 %
    normalisiert.
    """

    from modules.market_risk_score import (
        calculate_market_trend_score,
    )

    regional_data = load_market_trend_data(period=period)

    weighted_score = 0.0
    available_weight = 0.0

    for region_key, item in regional_data.items():
        metrics = item["metrics"]

        if metrics is None:
            item["risk_score"] = None
            continue

        risk_score = calculate_market_trend_score(
            metrics["distance_to_sma200_pct"],
            metrics["sma200_slope_20d_pct"],
        )

        item["risk_score"] = risk_score

        if risk_score is None:
            continue

        weight = float(item["weight"])

        weighted_score += risk_score * weight
        available_weight += weight

    if available_weight == 0:
        score = None
    else:
        score = weighted_score / available_weight

    return {
        "score": (
            round(score, 4)
            if score is not None
            else None
        ),
        "max_points": 14.0,
        "coverage": round(available_weight, 4),
        "regions": regional_data,
    }
