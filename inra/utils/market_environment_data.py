"""
Datenebene für das InRA Market Risk Model V0.1.

Grundprinzipien:
- vorhandene InRA-Marktdatenfunktionen wiederverwenden
- fehlende Daten niemals künstlich als niedriges Risiko interpretieren
- Datenbeschaffung und Scoring strikt voneinander trennen
"""

from pathlib import Path
from functools import lru_cache
from typing import Dict, Optional
import re

import pandas as pd
import requests

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



VOLATILITY_STRESS_REGIONS = {
    "usa": {
        "name": "USA",
        "series_name": "CBOE Volatility Index (VIX)",
        "fred_id": "VIXCLS",
        "weight": 0.50,
    },
    "europe": {
        "name": "Europa",
        "series_name": "EURO STOXX 50 Volatility (VSTOXX)",
        "fred_id": None,
        "weight": 0.30,
    },
    "em": {
        "name": "Emerging Markets",
        "series_name": "CBOE Emerging Markets ETF Volatility Index (VXEEM)",
        "fred_id": "VXEEMCLS",
        "weight": 0.20,
    },
}



GLOBAL_LIQUIDITY_CENTRAL_BANKS = {
    "fed": {
        "name": "Federal Reserve",
        "region": "USA",
        "source": "FRED",
        "series_name": "Federal Reserve Total Assets",
        "series_id": "WALCL",
        "frequency": "weekly",
        "fresh_days": 14,
        "warning_days": 21,
        "weight": 0.35,
    },
    "ecb": {
        "name": "European Central Bank",
        "region": "Eurozone",
        "source": "ECB",
        "series_name": "Total Assets of the Eurosystem",
        "series_id": "BSI.M.U2.N.C.T00.A.1.Z5.0000.Z01.E",
        "frequency": "monthly",
        "fresh_days": 45,
        "warning_days": 75,
        "weight": 0.25,
    },
    "pboc": {
        "name": "People's Bank of China",
        "region": "China",
        "source": "PBoC",
        "series_name": "Balance Sheet of Monetary Authority - Total Assets",
        "series_id": None,
        "frequency": "monthly",
        "fresh_days": 45,
        "warning_days": 75,
        "weight": 0.25,
    },
    "boj": {
        "name": "Bank of Japan",
        "region": "Japan",
        "source": "BoJ",
        "series_name": "Bank of Japan Accounts - Assets - Total",
        "database": "BS01",
        "series_id": "MABJMTA",
        "frequency": "monthly",
        "fresh_days": 45,
        "warning_days": 75,
        "weight": 0.15,
    },
}


@lru_cache(maxsize=32)
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



@lru_cache(maxsize=32)
def load_ecb_series(
    series_id: str,
) -> pd.DataFrame:
    """
    Lädt eine öffentliche Zeitreihe über die ECB Data API.

    Rückgabe:
    - Datum
    - Wert

    Bei Fehlern wird ein leeres DataFrame zurückgegeben.
    """

    url = (
        "https://data-api.ecb.europa.eu/service/data/"
        f"{series_id.replace('.', '/', 1)}"
        "?format=csvdata"
    )

    try:
        data = pd.read_csv(url)
    except Exception:
        return pd.DataFrame(columns=["Datum", "Wert"])

    if (
        "TIME_PERIOD" not in data.columns
        or "OBS_VALUE" not in data.columns
    ):
        return pd.DataFrame(columns=["Datum", "Wert"])

    result = data[
        ["TIME_PERIOD", "OBS_VALUE"]
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




def load_boj_series(
    database: str,
    series_id: str,
) -> pd.DataFrame:
    """
    Lädt eine öffentliche Zeitreihe über die BoJ Data API.

    Rückgabe:
    - Datum
    - Wert

    Bei Fehlern wird ein leeres DataFrame zurückgegeben.
    """

    import json
    from urllib.request import urlopen

    url = (
        "https://www.stat-search.boj.or.jp/api/v1/getDataCode"
        "?format=json"
        "&lang=en"
        f"&db={database}"
        f"&code={series_id}"
    )

    try:
        with urlopen(url, timeout=20) as response:
            data = json.load(response)
    except Exception:
        return pd.DataFrame(columns=["Datum", "Wert"])

    resultset = data.get("RESULTSET", [])

    if not resultset:
        return pd.DataFrame(columns=["Datum", "Wert"])

    values = resultset[0].get("VALUES", {})

    dates = values.get("SURVEY_DATES", [])
    observations = values.get("VALUES", [])

    if not dates or not observations:
        return pd.DataFrame(columns=["Datum", "Wert"])

    result = pd.DataFrame(
        {
            "Datum": dates,
            "Wert": observations,
        }
    )

    result["Datum"] = pd.to_datetime(
        result["Datum"].astype(str),
        format="%Y%m",
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




def _get_data_freshness_status(
    as_of: Optional[pd.Timestamp],
    fresh_days: int,
    warning_days: int,
) -> tuple:
    """
    Klassifiziert das Alter eines Datenstands.

    Rückgabe:
    - status
    - age_days

    None beim Datenstand bedeutet: Daten nicht verfügbar.
    """

    if as_of is None:
        return "unavailable", None

    today = pd.Timestamp.now().normalize()
    age_days = max(
        0,
        (today - pd.Timestamp(as_of).normalize()).days,
    )

    if age_days <= fresh_days:
        status = "fresh"
    elif age_days <= warning_days:
        status = "warning"
    else:
        status = "stale"

    return status, age_days


def load_global_liquidity_data() -> Dict[str, dict]:
    """
    Lädt die Rohdaten für den Global-Liquidity-Baustein.

    Quellen V0.1:
    - Fed: FRED / WALCL
    - EZB: ECB Data API
    - PBoC: derzeit nicht automatisiert verfügbar
    - BoJ: BoJ Data API / MABJMTA

    Fehlende Quellen werden als nicht verfügbar geführt.
    Zusätzlich wird das Alter des letzten Datenstands klassifiziert.
    """

    results = {}

    for bank_key, config in GLOBAL_LIQUIDITY_CENTRAL_BANKS.items():
        series_id = config.get("series_id")

        if series_id is None:
            history = pd.DataFrame(
                columns=["Datum", "Wert"]
            )
        elif bank_key == "fed":
            history = load_fred_series(series_id)
        elif bank_key == "ecb":
            history = load_ecb_series(series_id)
        elif bank_key == "boj":
            history = load_boj_series(
                config["database"],
                series_id,
            )
        else:
            history = pd.DataFrame(
                columns=["Datum", "Wert"]
            )

        available = not history.empty

        if available:
            as_of = history["Datum"].iloc[-1]
            observations = int(len(history))
            status, age_days = _get_data_freshness_status(
                as_of,
                config["fresh_days"],
                config["warning_days"],
            )
        else:
            as_of = None
            observations = 0
            status = "unavailable"
            age_days = None

        results[bank_key] = {
            **config,
            "available": available,
            "status": status,
            "as_of": as_of,
            "age_days": age_days,
            "observations": observations,
            "history": history,
        }

    return results



def _get_value_at_or_before(
    history: pd.DataFrame,
    target_date: pd.Timestamp,
) -> Optional[float]:
    """
    Liefert den letzten verfügbaren Wert am oder vor einem Stichtag.

    Funktioniert unabhängig von der Frequenz der Zeitreihe.
    """

    if history.empty:
        return None

    valid = history[
        history["Datum"] <= target_date
    ]

    if valid.empty:
        return None

    return float(valid.iloc[-1]["Wert"])



def calculate_global_liquidity_metrics(
    history: pd.DataFrame,
) -> Optional[Dict[str, object]]:
    """
    Berechnet die Rohkennzahlen einer Zentralbank-Bilanz.

    Für die gemeinsame Global-Liquidity-Bewertung werden alle
    Zentralbankreihen auf Monatsbasis standardisiert.

    Verglichen werden:
    - aktueller Monatswert
    - Veränderung über 3 Monate
    - Veränderung über 12 Monate
    - historische Einordnung der 3M- und 12M-Veränderung
    """

    if history.empty:
        return None

    history = (
        history
        .dropna(subset=["Datum", "Wert"])
        .sort_values("Datum")
        .reset_index(drop=True)
    )

    if history.empty:
        return None

    source_as_of = pd.Timestamp(
        history.iloc[-1]["Datum"]
    )

    monthly = (
        history
        .set_index("Datum")["Wert"]
        .resample("MS")
        .last()
        .dropna()
    )

    if len(monthly) < 13:
        return None

    current_value = float(monthly.iloc[-1])
    value_3m = float(monthly.iloc[-4])
    value_12m = float(monthly.iloc[-13])

    change_3m_pct = (
        (current_value / value_3m) - 1
    ) * 100

    change_12m_pct = (
        (current_value / value_12m) - 1
    ) * 100

    historical_3m = (
        monthly.pct_change(3) * 100
    ).dropna()

    historical_12m = (
        monthly.pct_change(12) * 100
    ).dropna()

    percentile_3m = float(
        (historical_3m <= change_3m_pct).mean() * 100
    )

    percentile_12m = float(
        (historical_12m <= change_12m_pct).mean() * 100
    )

    return {
        "current_value": current_value,
        "as_of": source_as_of,
        "value_3m": value_3m,
        "value_12m": value_12m,
        "change_3m_pct": change_3m_pct,
        "change_12m_pct": change_12m_pct,
        "percentile_3m": percentile_3m,
        "percentile_12m": percentile_12m,
        "observations": int(len(history)),
    }



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



def calculate_volatility_stress_metrics(
    history: pd.DataFrame,
) -> Optional[Dict[str, float]]:
    """
    Berechnet die Rohkennzahlen einer Volatilitätsreihe.

    Benötigt mindestens 61 gültige Beobachtungen für:
    - aktuelles Volatilitätsniveau
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
        "volatility_level": current,
        "percentile_history": percentile,
        "change_20d": current - value_20d,
        "change_60d": current - value_60d,
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



def load_volatility_stress_data() -> Dict[str, dict]:
    """
    Lädt die Volatility-Stress-Rohdaten.

    Regionale Zielabdeckung V0.1:
    - USA / VIX: 50 %
    - Europa / VSTOXX: 30 %
    - Emerging Markets / VXEEM: 20 %

    VSTOXX bleibt nicht verfügbar, solange keine robuste,
    automatisierbare Datenquelle eingebunden ist.
    Fehlende Daten werden nicht als 0 Risiko interpretiert.
    """

    results = {}

    for region_key, config in VOLATILITY_STRESS_REGIONS.items():
        fred_id = config.get("fred_id")

        if fred_id is None:
            metrics = None
        else:
            history = load_fred_series(
                fred_id,
            )
            metrics = calculate_volatility_stress_metrics(
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



def build_volatility_stress_component() -> Dict[str, object]:
    """
    Erstellt den vollständigen regional gewichteten
    Volatility-Stress-Baustein.

    Regionalgewichtung V0.1:
    - USA / VIX:                  50 %
    - Europa / VSTOXX:           30 %
    - Emerging Markets / VXEEM:  20 %

    Je Region:
    - 80 % aktuelles Volatilitätsniveau
    - 20 % Volatilitätsdynamik über 20 und 60 Handelstage

    Fehlende Regionen erhalten keine künstlichen 0 Risikopunkte.
    Die verfügbaren Regionalgewichte werden stattdessen auf 100 %
    normalisiert. Die tatsächliche Datenabdeckung bleibt separat
    als coverage sichtbar.
    """

    from modules.market_risk_score import (
        calculate_volatility_region_score,
    )

    regional_data = load_volatility_stress_data()

    weighted_score = 0.0
    available_weight = 0.0

    for region_key, item in regional_data.items():
        metrics = item["metrics"]

        if metrics is None:
            item["risk_score"] = None
            continue

        risk_score = calculate_volatility_region_score(
            metrics["percentile_history"],
            metrics["change_20d"],
            metrics["change_60d"],
            max_points=8.0,
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
        "max_points": 8.0,
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


def build_global_liquidity_component() -> Dict[str, object]:
    """
    Erstellt den gewichteten Global-Liquidity-Baustein.

    Zentralbankgewichtung V0.1:
    - Fed:   35 %
    - EZB:   25 %
    - PBoC:  25 %
    - BoJ:   15 %

    Je Zentralbank:
    - 70 % 12M-Trend
    - 30 % 3M-Dynamik

    Fehlende Zentralbanken erhalten keine künstlichen 0 Risikopunkte.
    Die verfügbaren Gewichte werden auf 100 % normalisiert.
    Die tatsächliche Datenabdeckung bleibt separat sichtbar.
    """

    from modules.market_risk_score import (
        calculate_global_liquidity_region_score,
    )

    central_bank_data = load_global_liquidity_data()

    weighted_score = 0.0
    available_weight = 0.0

    for bank_key, item in central_bank_data.items():
        history = item["history"]

        metrics = calculate_global_liquidity_metrics(
            history
        )

        item["metrics"] = metrics

        if metrics is None:
            item["risk_score"] = None
            continue

        risk_score = calculate_global_liquidity_region_score(
            metrics["percentile_3m"],
            metrics["percentile_12m"],
            max_points=8.0,
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
        "max_points": 8.0,
        "coverage": round(available_weight, 4),
        "central_banks": central_bank_data,
    }
def load_yield_curve_data() -> Dict[str, object]:
    """
    Lädt und berechnet die Rohdaten für den US-Yield-Curve-Frühwarnindikator.

    V0.1:
    - 10Y-2Y: FRED T10Y2Y
    - 10Y-3M: FRED T10Y3M
    - Monatsdurchschnitte zur robusten Regimeerkennung
    - substanzielle Inversion:
      mindestens 3 aufeinanderfolgende Monate <= -0,10 Prozentpunkte

    Die Funktion berechnet noch keinen Risikoscore.
    """

    from modules.market_risk_score import (
        find_last_substantial_yield_curve_inversion,
    )

    series_config = {
        "10y_2y": {
            "series_id": "T10Y2Y",
            "series_name": "10-Year Treasury Minus 2-Year Treasury",
        },
        "10y_3m": {
            "series_id": "T10Y3M",
            "series_name": "10-Year Treasury Minus 3-Month Treasury",
        },
    }

    result = {}

    for key, config in series_config.items():
        history = load_fred_series(config["series_id"])

        if history.empty:
            result[key] = {
                **config,
                "available": False,
                "metrics": None,
            }
            continue

        clean = (
            history
            .dropna(subset=["Datum", "Wert"])
            .sort_values("Datum")
        )

        monthly = (
            clean
            .set_index("Datum")["Wert"]
            .resample("ME")
            .mean()
            .dropna()
        )

        if monthly.empty:
            result[key] = {
                **config,
                "available": False,
                "metrics": None,
            }
            continue

        inversion = (
            find_last_substantial_yield_curve_inversion(monthly)
        )

        months_since_inversion_end = None
        resteepening_from_minimum = None
        inversion_start = None
        inversion_end = None
        inversion_duration_months = None
        inversion_minimum_spread = None

        if inversion is not None:
            start_index = inversion["start_index"]
            end_index = inversion["end_index"]

            inversion_start = monthly.index[start_index]
            inversion_end = monthly.index[end_index]
            inversion_duration_months = inversion["duration_months"]
            inversion_minimum_spread = inversion["minimum_spread"]

            months_since_inversion_end = (
                len(monthly) - 1 - end_index
            )

            resteepening_from_minimum = (
                float(monthly.iloc[-1])
                - float(inversion_minimum_spread)
            )

        result[key] = {
            **config,
            "available": True,
            "metrics": {
                "current_spread": float(monthly.iloc[-1]),
                "as_of": clean["Datum"].iloc[-1],
                "monthly_as_of": monthly.index[-1],
                "observations": int(len(clean)),
                "monthly_observations": int(len(monthly)),
                "inversion_start": inversion_start,
                "inversion_end": inversion_end,
                "inversion_duration_months": inversion_duration_months,
                "inversion_minimum_spread": inversion_minimum_spread,
                "months_since_inversion_end": months_since_inversion_end,
                "resteepening_from_minimum": resteepening_from_minimum,
            },
        }

    return result

def build_yield_curve_component() -> Dict[str, object]:
    """
    Erstellt den Yield-Curve-Frühwarnbaustein.

    V0.1:
    - 10Y-3M: 60 %
    - 10Y-2Y: 40 %

    Je Zinskurve:
    - 40 % aktueller Kurvenzustand
    - 60 % Inversions-/Re-Steepening-Regime

    Fehlende Reihen erhalten keine künstlichen 0 Risikopunkte.
    Verfügbare Gewichte werden auf 100 % normalisiert.
    """

    from modules.market_risk_score import (
        calculate_yield_curve_series_score,
    )

    curve_data = load_yield_curve_data()

    series_weights = {
        "10y_2y": 0.40,
        "10y_3m": 0.60,
    }

    weighted_score = 0.0
    available_weight = 0.0

    for key, item in curve_data.items():
        metrics = item["metrics"]
        weight = series_weights[key]

        item["weight"] = weight

        if metrics is None:
            item["risk_score"] = None
            continue

        risk_score = calculate_yield_curve_series_score(
            metrics["current_spread"],
            metrics["months_since_inversion_end"],
            metrics["resteepening_from_minimum"],
            max_points=7.0,
        )

        item["risk_score"] = risk_score

        if risk_score is None:
            continue

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
        "max_points": 7.0,
        "coverage": round(available_weight, 4),
        "series": curve_data,
    }


OECD_CLI_REGIONS = {
    "USA": {
        "name": "USA",
        "weight": 0.40,
    },
    "G4E": {
        "name": "Major four European countries",
        "weight": 0.25,
    },
    "CHN": {
        "name": "China",
        "weight": 0.20,
    },
    "G20": {
        "name": "G20",
        "weight": 0.15,
    },
}


def load_oecd_cli_data() -> Dict[str, object]:
    """
    Lädt den OECD Composite Leading Indicator (CLI).

    Offizielle OECD-SDMX-Reihe:
    - monatlich
    - amplitude adjusted
    - USA, G4E, China und G20

    Berechnet je Region:
    - aktuellen CLI-Wert
    - Veränderung über 3 Monate
    - Veränderung über 6 Monate

    Fehlende oder nicht ausreichend lange Reihen bleiben nicht bewertbar.
    """

    import io
    import requests

    url = (
        "https://sdmx.oecd.org/public/rest/v1/data/"
        "OECD.SDD.STES,DSD_STES@DF_CLI,/"
        ".M.LI...AA...H"
    )

    try:
        response = requests.get(
            url,
            headers={"Accept": "text/csv"},
            timeout=30,
        )
        response.raise_for_status()

        raw = pd.read_csv(io.StringIO(response.text))

    except Exception as exc:
        return {
            area: {
                **config,
                "available": False,
                "metrics": None,
                "error": str(exc),
            }
            for area, config in OECD_CLI_REGIONS.items()
        }

    result = {}

    for area, config in OECD_CLI_REGIONS.items():
        region = (
            raw[raw["REF_AREA"] == area]
            [["TIME_PERIOD", "OBS_VALUE"]]
            .dropna()
            .sort_values("TIME_PERIOD")
            .copy()
        )

        if len(region) < 7:
            result[area] = {
                **config,
                "available": False,
                "metrics": None,
                "error": "Nicht genügend OECD-CLI-Beobachtungen.",
            }
            continue

        values = region["OBS_VALUE"].astype(float).reset_index(drop=True)

        current_value = float(values.iloc[-1])
        change_3m = current_value - float(values.iloc[-4])
        change_6m = current_value - float(values.iloc[-7])

        result[area] = {
            **config,
            "available": True,
            "metrics": {
                "current_value": current_value,
                "change_3m": change_3m,
                "change_6m": change_6m,
                "as_of": region["TIME_PERIOD"].iloc[-1],
                "observations": int(len(region)),
                "history_start": region["TIME_PERIOD"].iloc[0],
            },
        }

    return result


def build_oecd_cli_component() -> Dict[str, object]:
    """
    Erstellt den OECD-CLI-Frühwarnbaustein.

    V0.1:
    - 50 % Dynamik
    - 30 % Regime
    - 20 % globale Breite

    Regionale Grundgewichte:
    - USA 40 %
    - G4E 25 %
    - China 20 %
    - G20 15 %

    Fehlende Regionen werden nicht als 0 Risiko behandelt.
    """

    from modules.market_risk_score import calculate_oecd_cli_score

    cli_data = load_oecd_cli_data()

    regional_metrics = {
        area: item["metrics"]
        for area, item in cli_data.items()
        if item["metrics"] is not None
    }

    score = calculate_oecd_cli_score(
        regional_metrics=regional_metrics,
        max_points=7.0,
    )

    available_weight = sum(
        item["weight"]
        for item in cli_data.values()
        if item["metrics"] is not None
    )

    return {
        "score": (
            round(score, 4)
            if score is not None
            else None
        ),
        "max_points": 7.0,
        "coverage": round(available_weight, 4),
        "regions": cli_data,
    }


def load_broad_dollar_data() -> Dict:
    """
    Lädt den Fed Broad Dollar Index (DTWEXBGS) von FRED.

    V0.1 verwendet:
    - 3M-Veränderung für kurzfristigen Dollarstress
    - 6M-Veränderung für Persistenz

    Die tägliche Reihe wird für die Veränderungsberechnung
    auf Monatsultimo verdichtet.
    """

    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        "?id=DTWEXBGS"
    )

    try:
        df = pd.read_csv(url)

        df["observation_date"] = pd.to_datetime(
            df["observation_date"]
        )
        df["DTWEXBGS"] = pd.to_numeric(
            df["DTWEXBGS"],
            errors="coerce",
        )

        df = (
            df.dropna(subset=["DTWEXBGS"])
            .sort_values("observation_date")
        )

        if len(df) < 130:
            raise ValueError(
                "Zu wenige gültige Broad-Dollar-Beobachtungen."
            )

        as_of = df["observation_date"].iloc[-1]
        history_start = df["observation_date"].iloc[0]
        current_value = float(df["DTWEXBGS"].iloc[-1])

        monthly = (
            df.set_index("observation_date")["DTWEXBGS"]
            .resample("ME")
            .last()
            .dropna()
        )

        if len(monthly) < 7:
            raise ValueError(
                "Zu wenige monatliche Broad-Dollar-Beobachtungen."
            )

        change_3m = (
            float(monthly.iloc[-1] / monthly.iloc[-4] - 1.0)
            * 100.0
        )
        change_6m = (
            float(monthly.iloc[-1] / monthly.iloc[-7] - 1.0)
            * 100.0
        )

        return {
            "series": "DTWEXBGS",
            "current_value": current_value,
            "change_3m_pct": change_3m,
            "change_6m_pct": change_6m,
            "as_of": as_of,
            "history_start": history_start,
            "observations": int(len(df)),
            "error": None,
        }

    except Exception as exc:
        return {
            "series": "DTWEXBGS",
            "current_value": None,
            "change_3m_pct": None,
            "change_6m_pct": None,
            "as_of": None,
            "history_start": None,
            "observations": 0,
            "error": str(exc),
        }


def build_broad_dollar_component() -> Dict:
    """
    Baut den Broad-Dollar-Frühwarnbaustein mit maximal 5 Punkten.
    """

    from modules.market_risk_score import (
        calculate_broad_dollar_score,
    )

    data = load_broad_dollar_data()

    score = calculate_broad_dollar_score(
        change_3m_pct=data["change_3m_pct"],
        change_6m_pct=data["change_6m_pct"],
        max_points=5.0,
    )

    return {
        "score": (
            round(score, 4)
            if score is not None
            else None
        ),
        "max_points": 5.0,
        "coverage": 1.0 if score is not None else 0.0,
        "data": data,
    }
def load_inflation_series(
    series_id: str,
) -> Dict:
    """
    Lädt eine monatliche Inflations-Indexreihe von FRED und
    berechnet YoY-Inflation sowie annualisierte 3M-Dynamik.

    Zusätzlich werden die aktuellen Werte innerhalb der
    verfügbaren eigenen Historie in Perzentile übersetzt.
    """

    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}"
    )

    try:
        df = pd.read_csv(url)

        df["observation_date"] = pd.to_datetime(
            df["observation_date"]
        )
        df[series_id] = pd.to_numeric(
            df[series_id],
            errors="coerce",
        )

        df = (
            df.dropna(subset=[series_id])
            .sort_values("observation_date")
        )

        if len(df) < 60:
            raise ValueError(
                "Zu wenige gültige Inflationsbeobachtungen."
            )

        series = (
            df.set_index("observation_date")[series_id]
            .sort_index()
        )

        yoy = series.pct_change(12) * 100.0

        momentum_3m = (
            (series / series.shift(3)) ** 4 - 1.0
        ) * 100.0

        yoy_valid = yoy.dropna()
        momentum_3m_valid = momentum_3m.dropna()

        if yoy_valid.empty or momentum_3m_valid.empty:
            raise ValueError(
                "Inflationsänderungen konnten nicht berechnet werden."
            )

        current_yoy = float(yoy_valid.iloc[-1])
        current_3m = float(momentum_3m_valid.iloc[-1])

        yoy_percentile = float(
            (yoy_valid <= current_yoy).mean() * 100.0
        )
        momentum_3m_percentile = float(
            (
                momentum_3m_valid <= current_3m
            ).mean()
            * 100.0
        )

        return {
            "series": series_id,
            "current_value": float(series.iloc[-1]),
            "yoy_pct": current_yoy,
            "momentum_3m_annualized_pct": current_3m,
            "yoy_percentile": yoy_percentile,
            "momentum_3m_percentile": momentum_3m_percentile,
            "as_of": series.index[-1],
            "history_start": series.index[0],
            "observations": int(len(series)),
            "error": None,
        }

    except Exception as exc:
        return {
            "series": series_id,
            "current_value": None,
            "yoy_pct": None,
            "momentum_3m_annualized_pct": None,
            "yoy_percentile": None,
            "momentum_3m_percentile": None,
            "as_of": None,
            "history_start": None,
            "observations": 0,
            "error": str(exc),
        }

def build_inflation_trend_component() -> Dict:
    """
    Baut den globalen Inflation-Trend-Frühwarnbaustein
    mit maximal 5 Punkten.

    V0.1 Regionen:
    - USA:      50 %
    - Eurozone: 30 %
    - China:    20 %

    China bleibt derzeit bewusst ohne Score, da keine ausreichend
    aktuelle und robuste monatliche Reihe verfügbar ist.

    Verfügbare Regionen werden für den Score normalisiert.
    Die Coverage zeigt weiterhin die tatsächlich verfügbare
    regionale Abdeckung.

    USA:
    - Headline + Core

    Eurozone:
    - nur Headline bepunktet
    - Core wird derzeit nicht in den Score einbezogen, da der
      historische Test keinen überzeugenden zusätzlichen
      Frühwarnnutzen gezeigt hat.
    """

    from modules.market_risk_score import (
        calculate_inflation_region_score,
    )

    usa_headline = load_inflation_series(
        "CPIAUCSL"
    )
    usa_core = load_inflation_series(
        "CPILFESL"
    )

    eurozone_headline = load_inflation_series(
        "CP00MI15EA20M086NEST"
    )
    eurozone_core = load_inflation_series(
        "TOTNRGFOODEA20MI15XM"
    )

    usa_score = calculate_inflation_region_score(
        headline_yoy_percentile=usa_headline[
            "yoy_percentile"
        ],
        headline_3m_percentile=usa_headline[
            "momentum_3m_percentile"
        ],
        core_yoy_percentile=usa_core[
            "yoy_percentile"
        ],
        core_3m_percentile=usa_core[
            "momentum_3m_percentile"
        ],
        max_points=5.0,
    )

    eurozone_score = calculate_inflation_region_score(
        headline_yoy_percentile=eurozone_headline[
            "yoy_percentile"
        ],
        headline_3m_percentile=eurozone_headline[
            "momentum_3m_percentile"
        ],
        core_yoy_percentile=None,
        core_3m_percentile=None,
        max_points=5.0,
    )

    regions = {
        "USA": {
            "weight": 0.50,
            "score": usa_score,
            "headline": usa_headline,
            "core": usa_core,
        },
        "Eurozone": {
            "weight": 0.30,
            "score": eurozone_score,
            "headline": eurozone_headline,
            "core": eurozone_core,
            "core_scored": False,
        },
        "China": {
            "weight": 0.20,
            "score": None,
            "headline": None,
            "core": None,
            "reason": (
                "Keine ausreichend aktuelle und robuste "
                "monatliche Inflationsreihe für V0.1."
            ),
        },
    }

    weighted_score = 0.0
    available_weight = 0.0

    for region in regions.values():
        score = region["score"]
        weight = region["weight"]

        if score is None:
            continue

        weighted_score += score * weight
        available_weight += weight

    if available_weight == 0.0:
        score = None
    else:
        score = weighted_score / available_weight

    return {
        "score": (
            round(score, 4)
            if score is not None
            else None
        ),
        "max_points": 5.0,
        "coverage": round(available_weight, 4),
        "regions": regions,
    }

def load_initial_jobless_claims() -> Dict[str, object]:
    """
    Lädt die wöchentlichen US Initial Jobless Claims von FRED.

    V0.1-Signal:
    4-Wochen-Durchschnitt relativ zu seinem niedrigsten
    Stand der vergangenen 52 Wochen.
    """

    series_id = "ICSA"
    url = (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}"
    )

    try:
        df = pd.read_csv(url)

        df["observation_date"] = pd.to_datetime(
            df["observation_date"],
            errors="coerce",
        )
        df[series_id] = pd.to_numeric(
            df[series_id],
            errors="coerce",
        )

        df = (
            df.dropna(
                subset=["observation_date", series_id]
            )
            .sort_values("observation_date")
            .reset_index(drop=True)
        )

        df["ma4"] = (
            df[series_id]
            .rolling(window=4, min_periods=4)
            .mean()
        )

        df["low52"] = (
            df["ma4"]
            .rolling(window=52, min_periods=52)
            .min()
        )

        df["rise_from_52w_low_pct"] = (
            df["ma4"] / df["low52"] - 1.0
        ) * 100.0

        valid = df.dropna(
            subset=["rise_from_52w_low_pct"]
        )

        if valid.empty:
            raise ValueError(
                "Keine ausreichenden ICSA-Daten "
                "für das 52-Wochen-Signal."
            )

        latest = valid.iloc[-1]

        return {
            "series_id": series_id,
            "value": float(latest[series_id]),
            "ma4": float(latest["ma4"]),
            "low52": float(latest["low52"]),
            "rise_from_52w_low_pct": float(
                latest["rise_from_52w_low_pct"]
            ),
            "as_of": latest["observation_date"],
            "history_start": df[
                "observation_date"
            ].iloc[0],
            "observations": int(len(df)),
            "error": None,
        }

    except Exception as exc:
        return {
            "series_id": series_id,
            "value": None,
            "ma4": None,
            "low52": None,
            "rise_from_52w_low_pct": None,
            "as_of": None,
            "history_start": None,
            "observations": 0,
            "error": str(exc),
        }


def build_initial_jobless_claims_component() -> Dict[str, object]:
    """
    Baut die V0.1-Komponente Initial Jobless Claims.

    US-only Frühwarnindikator mit maximal 3 Risikopunkten.
    """

    from modules.market_risk_score import (
        calculate_initial_jobless_claims_score,
    )

    data = load_initial_jobless_claims()

    score = calculate_initial_jobless_claims_score(
        rise_from_52w_low_pct=data[
            "rise_from_52w_low_pct"
        ],
        max_points=3.0,
    )

    return {
        "score": (
            round(score, 4)
            if score is not None
            else None
        ),
        "max_points": 3.0,
        "coverage": (
            1.0
            if score is not None
            else 0.0
        ),
        "region": "USA",
        "data": data,
    }


VALUATION_REGIONS = {
    "USA": {
        "weight": 0.40,
    },
    "Europe": {
        "weight": 0.25,
    },
    "China": {
        "weight": 0.20,
    },
    "Emerging Markets": {
        "weight": 0.15,
    },
}


def calculate_historical_percentile(
    current_value,
    historical_values,
) -> Optional[float]:
    """
    Berechnet die historische Rangposition eines aktuellen Werts.

    Rückgabe:
        0.0 bis 100.0 = Anteil der gültigen historischen
        Beobachtungen, die kleiner oder gleich dem aktuellen Wert sind.
        None = keine verwertbaren Daten.
    """
    if current_value is None:
        return None

    values = pd.to_numeric(
        pd.Series(historical_values),
        errors="coerce",
    ).dropna()

    if values.empty:
        return None

    current_value = float(current_value)

    percentile = (
        (values <= current_value).sum()
        / len(values)
        * 100.0
    )

    return float(percentile)


def load_usa_valuation_history(
    current_trailing_pe=None,
    current_cape=None,
) -> Dict[str, object]:
    """
    Lädt die historische USA-Bewertungsreferenz nach Shiller
    und ordnet aktuelle KGV- und CAPE-Werte historisch ein.
    """
    path = Path(
        "data/market_risk/valuation_usa_history.csv"
    )

    try:
        df = pd.read_csv(path)

        pe_values = pd.to_numeric(
            df["trailing_pe"],
            errors="coerce",
        ).dropna()

        cape_values = pd.to_numeric(
            df["cape"],
            errors="coerce",
        ).dropna()

        pe_percentile = calculate_historical_percentile(
            current_trailing_pe,
            pe_values,
        )

        cape_percentile = calculate_historical_percentile(
            current_cape,
            cape_values,
        )

        return {
            "current_trailing_pe": current_trailing_pe,
            "trailing_pe_percentile": pe_percentile,
            "current_cape": current_cape,
            "cape_percentile": cape_percentile,
            "pe_history_start": (
                float(df.loc[pe_values.index, "date"].iloc[0])
                if not pe_values.empty
                else None
            ),
            "pe_history_end": (
                float(df.loc[pe_values.index, "date"].iloc[-1])
                if not pe_values.empty
                else None
            ),
            "pe_observations": int(len(pe_values)),
            "cape_history_start": (
                float(df.loc[cape_values.index, "date"].iloc[0])
                if not cape_values.empty
                else None
            ),
            "cape_history_end": (
                float(df.loc[cape_values.index, "date"].iloc[-1])
                if not cape_values.empty
                else None
            ),
            "cape_observations": int(len(cape_values)),
            "source": "Robert J. Shiller",
            "error": None,
        }

    except Exception as exc:
        return {
            "current_trailing_pe": current_trailing_pe,
            "trailing_pe_percentile": None,
            "current_cape": current_cape,
            "cape_percentile": None,
            "pe_history_start": None,
            "pe_history_end": None,
            "pe_observations": 0,
            "cape_history_start": None,
            "cape_history_end": None,
            "cape_observations": 0,
            "source": "Robert J. Shiller",
            "error": str(exc),
        }


def load_current_usa_valuation() -> Dict[str, object]:
    """
    Lädt aktuelle USA-Bewertungskennzahlen von Multpl.

    Trailing-KGV und Shiller-CAPE werden unabhängig abgerufen.
    Fehlende oder nicht mehr parsebare Werte bleiben None.
    """
    indicators = {
        "trailing_pe": {
            "url": "https://www.multpl.com/s-p-500-pe-ratio",
            "pattern": (
                r"Current S&P 500 PE Ratio is "
                r"([0-9]+(?:\.[0-9]+)?)"
            ),
        },
        "cape": {
            "url": "https://www.multpl.com/shiller-pe",
            "pattern": (
                r"Current Shiller PE Ratio is "
                r"([0-9]+(?:\.[0-9]+)?)"
            ),
        },
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    result = {
        "trailing_pe": None,
        "cape": None,
        "source": "Multpl",
        "errors": {},
    }

    for name, config in indicators.items():
        try:
            response = requests.get(
                config["url"],
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()

            match = re.search(
                config["pattern"],
                response.text,
            )

            if match is None:
                raise ValueError(
                    "Aktueller Wert im HTML nicht gefunden."
                )

            result[name] = float(match.group(1))

        except Exception as exc:
            result["errors"][name] = str(exc)

    return result


def load_global_cape_valuations() -> Dict[str, object]:
    """
    Lädt aktuelle CAPE-Werte und historische CAPE-Perzentile
    für die Market-Risk-Regionen.

    Technischer Abrufpunkt:
        Portfolio Lab

    Zugrunde liegende Datenquelle:
        Research Affiliates Asset Allocation Interactive

    Die Perzentile vergleichen jeden Markt mit seiner eigenen
    historischen CAPE-Verteilung.
    """
    url = "https://www.portfoliolab.app/tools/global-cape-valuations"

    markets = {
        "USA": "US-Large",
        "Europe": "Europe",
        "China": "China",
        "Emerging Markets": "Emerging-Markets",
    }

    result = {
        "regions": {},
        "source": "Research Affiliates",
        "retrieval_source": "Portfolio Lab",
        "url": url,
        "as_of": None,
        "frequency": "monthly",
        "error": None,
    }

    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        response.raise_for_status()
        text = response.text

        as_of_match = re.search(
            r"RESEARCH AFFILIATES,\s*AS OF\s+"
            r"([A-Z]+\s+\d{1,2},\s+\d{4})",
            text,
            flags=re.IGNORECASE,
        )
        if as_of_match is not None:
            result["as_of"] = as_of_match.group(1).title()

        for region, market_id in markets.items():
            try:
                start = text.find(f'id="cape-row-{market_id}"')

                if start == -1:
                    raise ValueError(
                        f"CAPE-Zeile für {market_id} nicht gefunden."
                    )

                block = text[start:start + 1800]

                values = re.findall(
                    r">([0-9]+(?:\.[0-9]+)?)%?<",
                    block,
                )

                if len(values) < 2:
                    raise ValueError(
                        f"CAPE/Perzentil für {market_id} "
                        "nicht eindeutig gefunden."
                    )

                cape = float(values[0])
                percentile = float(values[1])

                if cape <= 0:
                    raise ValueError(
                        f"Unplausibles CAPE für {market_id}: {cape}"
                    )

                if not 0.0 <= percentile <= 100.0:
                    raise ValueError(
                        f"Unplausibles Perzentil für {market_id}: "
                        f"{percentile}"
                    )

                result["regions"][region] = {
                    "cape": cape,
                    "cape_percentile": percentile,
                    "market_id": market_id,
                    "error": None,
                }

            except Exception as exc:
                result["regions"][region] = {
                    "cape": None,
                    "cape_percentile": None,
                    "market_id": market_id,
                    "error": str(exc),
                }

    except Exception as exc:
        result["error"] = str(exc)

        for region, market_id in markets.items():
            result["regions"][region] = {
                "cape": None,
                "cape_percentile": None,
                "market_id": market_id,
                "error": str(exc),
            }

    return result


def build_global_cape_component() -> Dict[str, object]:
    """
    Baut den globalen CAPE-Baustein für Market Risk.

    Regionen und Gewichte:
        USA               40 %
        Europe            25 %
        China             20 %
        Emerging Markets  15 %

    Jede Region wird anhand ihres historischen CAPE-Perzentils
    separat bewertet. Fehlende Regionen reduzieren die Coverage;
    verfügbare Regionen werden auf die vollen 25 Punkte normalisiert.
    """
    from modules.market_risk_score import calculate_valuation_cape_score

    data = load_global_cape_valuations()

    regions = {}
    weighted_score = 0.0
    available_weight = 0.0

    for region, config in VALUATION_REGIONS.items():
        weight = config["weight"]
        values = data["regions"].get(region, {})

        cape = values.get("cape")
        percentile = values.get("cape_percentile")

        score = calculate_valuation_cape_score(
            percentile,
            max_points=25.0,
        )

        if score is not None:
            weighted_score += score * weight
            available_weight += weight

        regions[region] = {
            "weight": weight,
            "cape": cape,
            "cape_percentile": percentile,
            "score": score,
            "max_points": 25.0,
            "error": values.get("error"),
        }

    if available_weight > 0:
        score = weighted_score / available_weight
    else:
        score = None

    return {
        "score": score,
        "max_points": 25.0,
        "coverage": available_weight,
        "available_weight": available_weight,
        "regions": regions,
        "source": data["source"],
        "retrieval_source": data["retrieval_source"],
        "url": data["url"],
        "as_of": data["as_of"],
        "frequency": data["frequency"],
        "error": data["error"],
    }



def build_anfcI_under_the_radar() -> Dict[str, object]:
    """
    Under-the-Radar-Signal:
    schnelle Verschärfung der US-Finanzbedingungen.

    Eingefrorene Research-Regel:
        ANFCI-Veränderung über 13 Wochen > +0,5.
    """
    history = load_fred_series("ANFCI")

    if history.empty or len(history) < 14:
        return {
            "name": "ANFCI",
            "status": "unavailable",
            "label": "Nicht verfügbar",
            "value": None,
            "as_of": None,
            "detail": (
                "Die ANFCI-Daten konnten nicht ausreichend "
                "geladen werden."
            ),
        }

    history = history.sort_values("Datum").copy()
    history["change_13w"] = history["Wert"].diff(13)

    latest = history.dropna(
        subset=["change_13w"]
    ).iloc[-1]

    value = float(latest["Wert"])
    change = float(latest["change_13w"])
    signal = change > 0.5

    return {
        "name": "ANFCI",
        "status": "warning" if signal else "normal",
        "label": (
            "Schnelle Verschärfung"
            if signal
            else "Kein Warnsignal"
        ),
        "value": value,
        "change_13w": change,
        "as_of": latest["Datum"],
        "detail": (
            f"13-Wochen-Veränderung: {change:+.2f}. "
            "Warnsignal bei mehr als +0,50. "
            "Das Signal zeigt eine ungewöhnlich schnelle "
            "Verschärfung der US-Finanzbedingungen."
        ),
    }


def build_sahm_under_the_radar() -> Dict[str, object]:
    """
    Sahm Rule als US-Rezessionsregime.

    Offizielle Schwelle:
        SAHMREALTIME >= 0,50 Prozentpunkte.
    """
    history = load_fred_series("SAHMREALTIME")

    if history.empty:
        return {
            "name": "Sahm Rule",
            "status": "unavailable",
            "label": "Nicht verfügbar",
            "value": None,
            "as_of": None,
            "detail": (
                "Die Sahm-Rule-Daten konnten nicht "
                "geladen werden."
            ),
        }

    latest = history.sort_values("Datum").iloc[-1]
    value = float(latest["Wert"])
    signal = value >= 0.50

    return {
        "name": "Sahm Rule",
        "status": "warning" if signal else "normal",
        "label": (
            "Rezessionssignal aktiv"
            if signal
            else "Kein Rezessionssignal"
        ),
        "value": value,
        "as_of": latest["Datum"],
        "detail": (
            f"Aktueller Wert: {value:.2f}. "
            "Das US-Rezessionssignal gilt ab 0,50 als aktiv. "
            "Die Sahm Rule bestätigt eine deutliche "
            "Arbeitsmarktverschlechterung, ist aber kein "
            "frühes Börsenwarnsignal."
        ),
    }


def build_gebert_under_the_radar() -> Dict[str, object]:
    """
    Gebert-Indikator für Europa/DAX.

    Festgelegte Komponenten:
    - Eurozone HICP
    - letzte tatsächliche EZB-MRO-Zinsänderung
    - EUR/USD
    - Saison November bis April

    Regime:
        3-4 Punkte = positiv
        0-1 Punkte = negativ
        2 Punkte   = vorheriges Regime bleibt bestehen
    """
    hicp = load_ecb_series(
        "HICP.M.U2.N.000000.4D0.INX"
    ).copy()

    mro = load_ecb_series(
        "FM.B.U2.EUR.4F.KR.MRR.CHG"
    ).copy()

    fx = load_ecb_series(
        "EXR.D.USD.EUR.SP00.A"
    ).copy()

    if hicp.empty or mro.empty or fx.empty:
        return {
            "name": "Gebert",
            "status": "unavailable",
            "label": "Nicht verfügbar",
            "value": None,
            "as_of": None,
            "detail": (
                "Mindestens eine benötigte ECB-Reihe "
                "konnte nicht geladen werden."
            ),
        }

    start = pd.Timestamp("1999-01-31")
    end = min(
        hicp["Datum"].max() + pd.offsets.MonthEnd(0),
        fx["Datum"].max() + pd.offsets.MonthEnd(0),
    )

    monthly = pd.DataFrame({
        "Datum": pd.date_range(
            start,
            end,
            freq="ME",
        )
    })

    # 1. Inflation
    h = hicp.copy()

    h["available_date"] = (
        h["Datum"]
        + pd.offsets.MonthBegin(1)
        + pd.Timedelta(days=23)
    )

    h["hicp_yoy_pct"] = (
        h["Wert"].pct_change(
            12,
            fill_method=None,
        ) * 100
    )

    h["inflation_point"] = (
        h["hicp_yoy_pct"]
        < h["hicp_yoy_pct"].shift(12)
    ).astype(int)

    h_available = h[
        [
            "available_date",
            "Datum",
            "Wert",
            "hicp_yoy_pct",
            "inflation_point",
        ]
    ].rename(
        columns={
            "Datum": "hicp_reference_month",
            "Wert": "hicp_index",
        }
    ).sort_values("available_date")

    monthly = pd.merge_asof(
        monthly.sort_values("Datum"),
        h_available,
        left_on="Datum",
        right_on="available_date",
        direction="backward",
    )

    # 2. EZB-MRO: nur tatsächliche Änderungen
    rate = mro.copy().sort_values("Datum")

    rate = rate.loc[
        rate["Wert"].abs() > 1e-12
    ].copy()

    rate["interest_point"] = (
        rate["Wert"] < 0
    ).astype(int)

    rate = rate.rename(
        columns={
            "Datum": "mro_change_date",
            "Wert": "mro_change_pp",
        }
    )

    monthly = pd.merge_asof(
        monthly.sort_values("Datum"),
        rate[
            [
                "mro_change_date",
                "mro_change_pp",
                "interest_point",
            ]
        ],
        left_on="Datum",
        right_on="mro_change_date",
        direction="backward",
    )

    # 3. EUR/USD
    fx_monthly = (
        fx.set_index("Datum")["Wert"]
        .resample("ME")
        .last()
        .dropna()
        .rename("eurusd")
        .to_frame()
    )

    fx_monthly["eurusd_12m_ago"] = (
        fx_monthly["eurusd"].shift(12)
    )

    fx_monthly["currency_point"] = (
        fx_monthly["eurusd"]
        < fx_monthly["eurusd_12m_ago"]
    ).astype(int)

    fx_monthly = (
        fx_monthly
        .rename_axis("Datum")
        .reset_index()
    )

    monthly = pd.merge(
        monthly,
        fx_monthly,
        on="Datum",
        how="left",
    )

    # 4. Saison
    monthly["season_point"] = (
        monthly["Datum"].dt.month.isin(
            [11, 12, 1, 2, 3, 4]
        )
    ).astype(int)

    component_cols = [
        "inflation_point",
        "interest_point",
        "currency_point",
        "season_point",
    ]

    valid = monthly[
        [
            "hicp_yoy_pct",
            "mro_change_pp",
            "eurusd_12m_ago",
        ]
    ].notna().all(axis=1)

    monthly["gebert_points"] = pd.NA

    monthly.loc[
        valid,
        "gebert_points",
    ] = (
        monthly.loc[
            valid,
            component_cols,
        ].sum(axis=1)
    )

    # Regime rekonstruieren
    regime = None
    regimes = []

    for points in monthly["gebert_points"]:
        if pd.isna(points):
            regimes.append(None)
            continue

        if points >= 3:
            new_regime = "positiv"
        elif points <= 1:
            new_regime = "negativ"
        else:
            new_regime = regime

        regime = new_regime
        regimes.append(regime)

    monthly["gebert_regime"] = regimes

    current = monthly.dropna(
        subset=["gebert_points", "gebert_regime"]
    )

    if current.empty:
        return {
            "name": "Gebert",
            "status": "unavailable",
            "label": "Nicht verfügbar",
            "value": None,
            "as_of": None,
            "detail": (
                "Der Gebert-Indikator konnte nicht "
                "vollständig berechnet werden."
            ),
        }

    latest = current.iloc[-1]
    points = int(latest["gebert_points"])
    regime = latest["gebert_regime"]

    return {
        "name": "Gebert",
        "status": (
            "normal"
            if regime == "positiv"
            else "warning"
        ),
        "label": (
            "Positives Europa-Regime"
            if regime == "positiv"
            else "Negatives Europa-Regime"
        ),
        "value": points,
        "regime": regime,
        "as_of": latest["Datum"],
        "detail": (
            f"{points} von 4 Komponenten positiv. "
            "3–4 Punkte wechseln ins positive Regime, "
            "0–1 ins negative; bei 2 Punkten bleibt "
            "das vorherige Regime bestehen. "
            "Das Signal ist als ergänzendes "
            "Europa/DAX-Regime zu verstehen."
        ),
    }


def build_under_the_radar_snapshot() -> Dict[str, object]:
    """
    Experimentelle Zusatzebene außerhalb des
    eigentlichen InRA Market Risk Scores.
    """
    builders = {
        "anfci": build_anfcI_under_the_radar,
        "gebert": build_gebert_under_the_radar,
        "sahm": build_sahm_under_the_radar,
    }

    result = {}

    for key, builder in builders.items():
        try:
            result[key] = builder()
        except Exception as exc:
            result[key] = {
                "status": "unavailable",
                "label": "Nicht verfügbar",
                "value": None,
                "as_of": None,
                "detail": f"Datenfehler: {exc}",
            }

    return result


def build_market_risk_snapshot() -> Dict[str, object]:
    """
    Baut den vollständigen aktuellen InRA Market Risk Snapshot V0.1.

    Diese Funktion ist die zentrale Schnittstelle zwischen
    Marktdaten, Komponenten-Scores und Benutzeroberfläche.

    Die Benutzeroberfläche soll keine eigene Scoring-Logik enthalten.
    """

    from modules.market_risk_score import (
        calculate_market_risk_score,
        get_market_risk_label,
    )

    components = {
        "market_trend": build_market_trend_component(),
        "credit_stress": build_credit_stress_component(),
        "volatility_stress": build_volatility_stress_component(),

        # Für Market Breadth existiert in V0.1 bewusst
        # noch keine belastbare historische Datenbasis.
        "market_breadth": None,

        "global_liquidity": build_global_liquidity_component(),
        "yield_curve": build_yield_curve_component(),
        "oecd_cli": build_oecd_cli_component(),
        "broad_dollar": build_broad_dollar_component(),
        "inflation_trend": build_inflation_trend_component(),
        "initial_jobless_claims": (
            build_initial_jobless_claims_component()
        ),

        "valuation": build_global_cape_component(),
    }

    component_scores = {
        name: (
            component.get("score")
            if component is not None
            else None
        )
        for name, component in components.items()
    }

    risk = calculate_market_risk_score(
        component_scores
    )

    return {
        "score": risk["score"],
        "max_points": risk["max_points"],
        "label": get_market_risk_label(
            risk["score"]
        ),
        "coverage": risk["coverage"],
        "blocks": risk["blocks"],
        "components": components,
    }


def _prepare_market_risk_snapshot_for_json(value):
    """
    Bereitet einen Market-Risk-Snapshot für die persistente
    JSON-Speicherung vor.

    Historische DataFrames werden nicht im UI-Snapshot gespeichert.
    Zeitstempel werden als ISO-Strings gespeichert.
    """

    if isinstance(value, pd.DataFrame):
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: _prepare_market_risk_snapshot_for_json(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            _prepare_market_risk_snapshot_for_json(item)
            for item in value
        ]

    return value


def load_market_risk_history(
    path="data/market_risk/market_risk_history.csv",
) -> pd.DataFrame:
    """
    Lädt die lokal aufgebaute Market-Risk-Tageshistorie.
    """
    input_path = Path(path)

    if not input_path.exists():
        return pd.DataFrame()

    try:
        history = pd.read_csv(input_path)
    except Exception:
        return pd.DataFrame()

    if "Datum" in history.columns:
        history["Datum"] = pd.to_datetime(
            history["Datum"],
            errors="coerce",
        )

        history = (
            history
            .dropna(subset=["Datum"])
            .sort_values("Datum")
            .reset_index(drop=True)
        )

    return history


def save_market_risk_history(
    snapshot,
    path="data/market_risk/market_risk_history.csv",
):
    """
    Speichert pro Kalendertag genau einen Market-Risk-Historienwert.

    Die drei Ebenen werden auf 0–100 normalisiert gespeichert.
    Ein erneutes Update am selben Tag ersetzt den vorhandenen Tageswert.
    """
    from datetime import datetime

    def normalize_block(block):
        if not isinstance(block, dict):
            return None

        score = block.get("score")
        max_points = block.get("max_points")

        if (
            score is None
            or max_points is None
            or max_points <= 0
        ):
            return None

        return round(
            float(score) / float(max_points) * 100,
            2,
        )

    generated_at = snapshot.get("generated_at")

    if generated_at:
        timestamp = pd.Timestamp(generated_at)
    else:
        timestamp = pd.Timestamp(
            datetime.now().astimezone()
        )

    blocks = snapshot.get("blocks", {})

    row = {
        "Datum": timestamp.date().isoformat(),
        "Zeitpunkt": timestamp.isoformat(),
        "Gesamt": snapshot.get("score"),
        "Aktueller Stress": normalize_block(
            blocks.get("current_stress")
        ),
        "Frühwarnung": normalize_block(
            blocks.get("early_warning")
        ),
        "Fallhöhe": normalize_block(
            blocks.get("fall_height")
        ),
        "Abdeckung Gesamt": snapshot.get("coverage"),
        "Abdeckung Aktueller Stress": (
            blocks.get("current_stress", {}).get("coverage")
        ),
        "Abdeckung Frühwarnung": (
            blocks.get("early_warning", {}).get("coverage")
        ),
        "Abdeckung Fallhöhe": (
            blocks.get("fall_height", {}).get("coverage")
        ),
    }

    output_path = Path(path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if output_path.exists():
        history = pd.read_csv(output_path)
    else:
        history = pd.DataFrame()

    new_row = pd.DataFrame([row])

    if not history.empty and "Datum" in history.columns:
        history = history[
            history["Datum"].astype(str) != row["Datum"]
        ]

    history = pd.concat(
        [history, new_row],
        ignore_index=True,
    )

    history = history.sort_values("Datum")

    history.to_csv(
        output_path,
        index=False,
    )

    return history


def save_market_risk_snapshot(
    path="data/market_risk/latest_snapshot.json",
):
    """
    Berechnet den aktuellen Market-Risk-Snapshot und speichert
    eine kompakte UI-Version persistent als JSON.
    """

    import json
    from pathlib import Path

    from datetime import datetime

    snapshot = build_market_risk_snapshot()
    snapshot["generated_at"] = datetime.now().astimezone().isoformat(
        timespec="seconds"
    )
    snapshot = _prepare_market_risk_snapshot_for_json(snapshot)

    save_market_risk_history(snapshot)

    output_path = Path(path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            snapshot,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return snapshot


def load_market_risk_snapshot(
    path="data/market_risk/latest_snapshot.json",
):
    """
    Lädt den zuletzt erfolgreich gespeicherten
    Market-Risk-Snapshot für die Benutzeroberfläche.
    """

    import json
    from pathlib import Path

    input_path = Path(path)

    if not input_path.exists():
        return None

    return json.loads(
        input_path.read_text(
            encoding="utf-8",
        )
    )
