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


CREDIT_STRESS_REGIONS = {
    "usa": {
        "name": "USA",
        "series_name": "ICE BofA US High Yield OAS",
        "fred_id": "BAMLH0A0HYM2",
        "weight": 0.60,
    },
    "europe": {
        "name": "Europa",
        "series_name": "ICE BofA Euro High Yield OAS",
        "fred_id": "BAMLHE00EHYIOAS",
        "weight": 0.40,
    },
}


def load_fred_series(
    fred_id: str,
) -> pd.DataFrame:
    """
    Lädt eine öffentliche FRED-Reihe über den CSV-Endpunkt.

    Kein API-Key erforderlich.

    Rückgabe:
    - Datum
    - Wert

    Bei Fehlern wird ein leeres DataFrame zurückgegeben.
    """

    url = (
        "https://fred.stlouisfed.org/graph/"
        f"fredgraph.csv?id={fred_id}"
    )

    try:
        data = pd.read_csv(url)
    except Exception:
        return pd.DataFrame(columns=["Datum", "Wert"])

    if (
        "observation_date" not in data.columns
        or fred_id not in data.columns
    ):
        return pd.DataFrame(columns=["Datum", "Wert"])

    result = data[
        ["observation_date", fred_id]
    ].copy()

    result.columns = ["Datum", "Wert"]

    result["Datum"] = pd.to_datetime(
        result["Datum"],
        errors="coerce",
    )
    result["Wert"] = pd.to_numeric(
        result["Wert"],
        errors="coerce",
    )

    return (
        result
        .dropna(subset=["Datum", "Wert"])
        .sort_values("Datum")
        .reset_index(drop=True)
    )


def calculate_credit_stress_metrics(
    history: pd.DataFrame,
) -> Optional[Dict[str, float]]:
    """
    Berechnet die Rohkennzahlen einer High-Yield-Spread-Reihe.

    Benötigt mindestens 61 gültige Beobachtungen für:
    - aktuelles Spread-Niveau
    - Perzentil innerhalb der verfügbaren Historie
    - Veränderung über 20 Handelstage
    - Veränderung über 60 Handelstage

    Die eigentliche Risikobewertung erfolgt separat
    in modules/market_risk_score.py.
    """

    if history.empty or len(history) < 61:
        return None

    values = history["Wert"]

    current = float(values.iloc[-1])
    value_20d = float(values.iloc[-21])
    value_60d = float(values.iloc[-61])

    percentile = float(
        (values <= current).mean() * 100
    )

    return {
        "spread_pct": current,
        "percentile_history": percentile,
        "change_20d_pp": current - value_20d,
        "change_60d_pp": current - value_60d,
        "as_of": history.iloc[-1]["Datum"],
        "observations": int(len(history)),
    }


def load_credit_stress_data() -> Dict[str, dict]:
    """
    Lädt die Credit-Stress-Rohdaten für USA und Europa.

    Regionale Abdeckung V0.1:
    - USA: 60 %
    - Europa: 40 %

    China und Emerging Markets werden nicht künstlich
    durch ungeeignete Proxy-Reihen ergänzt.
    """

    results = {}

    for region_key, config in CREDIT_STRESS_REGIONS.items():
        history = load_fred_series(
            config["fred_id"],
        )

        metrics = calculate_credit_stress_metrics(
            history,
        )

        results[region_key] = {
            **config,
            "available": metrics is not None,
            "metrics": metrics,
        }

    return results


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


def build_credit_stress_component() -> Dict[str, object]:
    """
    Erstellt den vollständigen regional gewichteten Credit-Stress-Baustein.

    Regionalgewichtung V0.1:
    - USA:     60 %
    - Europa:  40 %

    Je Region:
    - 70 % aktuelles Spread-Niveau
    - 30 % Spread-Dynamik über 20 und 60 Handelstage

    Fehlende Regionen erhalten keine künstlichen 0 Risikopunkte.
    Die verfügbaren Regionalgewichte werden stattdessen auf 100 %
    normalisiert.
    """

    from modules.market_risk_score import (
        calculate_credit_region_score,
    )

    regional_data = load_credit_stress_data()

    weighted_score = 0.0
    available_weight = 0.0

    for region_key, item in regional_data.items():
        metrics = item["metrics"]

        if metrics is None:
            item["risk_score"] = None
            continue

        risk_score = calculate_credit_region_score(
            metrics["spread_pct"],
            metrics["percentile_history"],
            metrics["change_20d_pp"],
            metrics["change_60d_pp"],
            max_points=11.0,
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
        "max_points": 11.0,
        "coverage": round(available_weight, 4),
        "regions": regional_data,
    }
