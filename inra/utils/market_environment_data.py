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
