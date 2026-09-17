"""
InRA Market Risk Model V0.1

Ziel:
Einschätzung des Risikos, dass eine allgemeine Marktverschlechterung
eine grundsätzlich attraktive Aktie in den kommenden Wochen bis Monaten
mit nach unten zieht.

Score:
    0   = niedriges allgemeines Marktrisiko
    100 = sehr hohes allgemeines Marktrisiko

Architektur:
    Aktueller Marktstress   40 Punkte
    Frühwarnung             35 Punkte
    Fallhöhe                25 Punkte

Fehlende Daten erhalten niemals künstlich 0 Risikopunkte.
Der Score wird auf Basis der tatsächlich bewertbaren Komponenten
auf das jeweilige Blockmaximum normalisiert.
"""

from typing import Dict, Optional


MARKET_RISK_WEIGHTS = {
    "current_stress": {
        "market_trend": 14.0,
        "credit_stress": 11.0,
        "volatility_stress": 8.0,
        "market_breadth": 7.0,
    },
    "early_warning": {
        "global_liquidity": 8.0,
        "yield_curve": 7.0,
        "oecd_cli": 7.0,
        "broad_dollar": 5.0,
        "inflation_trend": 5.0,
        "seasonality": 3.0,
    },
    "fall_height": {
        "valuation": 10.0,
        "equity_bond_yield_gap": 7.0,
        "market_concentration": 5.0,
        "leverage": 3.0,
    },
}


BLOCK_MAX_POINTS = {
    block: sum(components.values())
    for block, components in MARKET_RISK_WEIGHTS.items()
}


TOTAL_MAX_POINTS = sum(BLOCK_MAX_POINTS.values())


def _clamp(value: float, minimum: float, maximum: float) -> float:
    """Begrenzt einen Wert auf den angegebenen Bereich."""
    return max(minimum, min(value, maximum))



def calculate_market_trend_score(
    distance_to_sma200_pct: Optional[float],
    sma200_slope_20d_pct: Optional[float],
    max_points: float = 14.0,
) -> Optional[float]:
    """
    Bewertet den Markttrend anhand von:
    - Abstand des Kurses zur 200-Tage-Linie
    - Veränderung der 200-Tage-Linie über 20 Handelstage

    V0.1-Arbeitsschwellen:
    - SMA200 steigend:  > +0.25 % in 20 Handelstagen
    - SMA200 fallend:   < -0.25 %
    - dazwischen:       seitwärts
    - deutlich unter SMA200: <= -5 %

    Risikostufen:
    0/14  = intakter Aufwärtstrend
    4/14  = nachlassender Trend
    5/14  = Korrektur bei noch steigender SMA200
    9/14  = beschädigter Trend
    14/14 = ausgeprägter Abwärtstrend

    Die Schwellen werden später historisch kalibriert.
    """

    if (
        distance_to_sma200_pct is None
        or sma200_slope_20d_pct is None
    ):
        return None

    distance = float(distance_to_sma200_pct)
    slope = float(sma200_slope_20d_pct)

    if distance <= -5.0 and slope < -0.25:
        risk_fraction = 1.0

    elif distance < 0.0 and slope <= 0.25:
        risk_fraction = 9.0 / 14.0

    elif distance < 0.0 and slope > 0.25:
        risk_fraction = 5.0 / 14.0

    elif distance >= 0.0 and slope <= 0.25:
        risk_fraction = 4.0 / 14.0

    else:
        risk_fraction = 0.0

    return round(max_points * risk_fraction, 4)



def calculate_credit_level_risk(
    spread_pct: Optional[float],
    percentile_3y: Optional[float],
) -> Optional[float]:
    """
    Bewertet das aktuelle High-Yield-Spread-Niveau auf 0 bis 1.

    V0.1 kombiniert:
    - absolutes Spread-Niveau
    - Perzentil innerhalb der verfügbaren 3-Jahres-Historie

    Die kurze FRED-Historie entscheidet damit nicht allein über
    die Einstufung. Die Schwellen werden später historisch kalibriert.
    """

    if spread_pct is None or percentile_3y is None:
        return None

    spread = float(spread_pct)
    percentile = _clamp(float(percentile_3y), 0.0, 100.0)

    if spread < 3.0:
        absolute_risk = 0.0
    elif spread < 4.0:
        absolute_risk = 0.25
    elif spread < 5.0:
        absolute_risk = 0.50
    elif spread < 7.0:
        absolute_risk = 0.75
    else:
        absolute_risk = 1.0

    if percentile < 50.0:
        percentile_risk = 0.0
    elif percentile < 75.0:
        percentile_risk = 0.25
    elif percentile < 90.0:
        percentile_risk = 0.50
    elif percentile < 95.0:
        percentile_risk = 0.75
    else:
        percentile_risk = 1.0

    return round(
        0.70 * absolute_risk
        + 0.30 * percentile_risk,
        4,
    )


def calculate_credit_dynamics_risk(
    change_20d_pp: Optional[float],
    change_60d_pp: Optional[float],
) -> Optional[float]:
    """
    Bewertet die Verschlechterungsdynamik des High-Yield-Spreads
    auf 0 bis 1.

    Positive Veränderungen bedeuten steigende Spreads und damit
    zunehmenden Kreditstress.

    20 Handelstage und 60 Handelstage werden gleich gewichtet.
    """

    if change_20d_pp is None or change_60d_pp is None:
        return None

    def _change_risk(change: float) -> float:
        if change <= 0.0:
            return 0.0
        if change < 0.15:
            return 0.20
        if change < 0.30:
            return 0.40
        if change < 0.50:
            return 0.60
        if change < 1.00:
            return 0.80
        return 1.0

    risk_20d = _change_risk(float(change_20d_pp))
    risk_60d = _change_risk(float(change_60d_pp))

    return round(
        0.50 * risk_20d
        + 0.50 * risk_60d,
        4,
    )


def calculate_credit_region_score(
    spread_pct: Optional[float],
    percentile_3y: Optional[float],
    change_20d_pp: Optional[float],
    change_60d_pp: Optional[float],
    max_points: float = 11.0,
) -> Optional[float]:
    """
    Regionaler Credit-Stress-Score.

    V0.1:
    - 70 % aktuelles Spread-Niveau
    - 30 % Spread-Dynamik

    max_points dient nur zur Skalierung. Die spätere globale
    Aggregation gewichtet USA und Europa separat.
    """

    level_risk = calculate_credit_level_risk(
        spread_pct,
        percentile_3y,
    )
    dynamics_risk = calculate_credit_dynamics_risk(
        change_20d_pp,
        change_60d_pp,
    )

    if level_risk is None and dynamics_risk is None:
        return None

    weighted_risk = 0.0
    available_weight = 0.0

    if level_risk is not None:
        weighted_risk += 0.70 * level_risk
        available_weight += 0.70

    if dynamics_risk is not None:
        weighted_risk += 0.30 * dynamics_risk
        available_weight += 0.30

    normalized_risk = weighted_risk / available_weight

    return round(
        max_points * normalized_risk,
        4,
    )



def calculate_volatility_level_risk(
    percentile_history: Optional[float],
) -> Optional[float]:
    """
    Bewertet das aktuelle Volatilitätsniveau auf 0 bis 1.

    V0.1 verwendet das langfristige Perzentil der jeweiligen
    Volatilitätsreihe. Dadurch werden strukturell unterschiedliche
    Normalniveaus von VIX, VSTOXX und VXEEM berücksichtigt.

    Arbeitsschwellen:
    - unter P50:  0.00
    - P50-P75:    0.25
    - P75-P90:    0.50
    - P90-P95:    0.75
    - ab P95:     1.00

    Die Schwellen werden später historisch kalibriert.
    """

    if percentile_history is None:
        return None

    percentile = _clamp(
        float(percentile_history),
        0.0,
        100.0,
    )

    if percentile < 50.0:
        return 0.0
    if percentile < 75.0:
        return 0.25
    if percentile < 90.0:
        return 0.50
    if percentile < 95.0:
        return 0.75

    return 1.0


def calculate_volatility_dynamics_risk(
    change_20d: Optional[float],
    change_60d: Optional[float],
) -> Optional[float]:
    """
    Bewertet die Verschlechterungsdynamik der Volatilität auf 0 bis 1.

    Nur steigende Volatilität erhöht das Risiko.

    V0.1-Arbeitsschwellen je Zeitraum:
    - <= 0:       0.00
    - < +2.5:     0.20
    - < +5.0:     0.40
    - < +8.0:     0.60
    - < +15.0:    0.80
    - >= +15.0:   1.00

    20 und 60 Handelstage werden gleich gewichtet.
    Die Schwellen orientieren sich an den empirisch geprüften
    Verteilungen von VIX und VXEEM und werden später historisch
    kalibriert.
    """

    if change_20d is None or change_60d is None:
        return None

    def _change_risk(change: float) -> float:
        if change <= 0.0:
            return 0.0
        if change < 2.5:
            return 0.20
        if change < 5.0:
            return 0.40
        if change < 8.0:
            return 0.60
        if change < 15.0:
            return 0.80
        return 1.0

    risk_20d = _change_risk(float(change_20d))
    risk_60d = _change_risk(float(change_60d))

    return round(
        0.50 * risk_20d
        + 0.50 * risk_60d,
        4,
    )


def calculate_volatility_region_score(
    percentile_history: Optional[float],
    change_20d: Optional[float],
    change_60d: Optional[float],
    max_points: float = 8.0,
) -> Optional[float]:
    """
    Regionaler Volatility-Stress-Score.

    V0.1:
    - 80 % aktuelles Volatilitätsniveau
    - 20 % Volatilitätsdynamik

    max_points dient nur zur Skalierung. Die spätere globale
    Aggregation gewichtet VIX, VSTOXX und VXEEM separat.
    """

    level_risk = calculate_volatility_level_risk(
        percentile_history,
    )
    dynamics_risk = calculate_volatility_dynamics_risk(
        change_20d,
        change_60d,
    )

    if level_risk is None and dynamics_risk is None:
        return None

    weighted_risk = 0.0
    available_weight = 0.0

    if level_risk is not None:
        weighted_risk += 0.80 * level_risk
        available_weight += 0.80

    if dynamics_risk is not None:
        weighted_risk += 0.20 * dynamics_risk
        available_weight += 0.20

    normalized_risk = weighted_risk / available_weight

    return round(
        max_points * normalized_risk,
        4,
    )



def calculate_global_liquidity_percentile_risk(
    percentile: Optional[float],
) -> Optional[float]:
    """
    Übersetzt die historische Position einer Zentralbank-Bilanzentwicklung
    in einen Risikofaktor von 0 bis 1.

    Niedrige Perzentile bedeuten ungewöhnlich schwache bzw. restriktive
    Bilanzentwicklung und damit höheres Liquiditätsrisiko.
    """

    if percentile is None:
        return None

    percentile = _clamp(float(percentile), 0.0, 100.0)

    if percentile >= 50.0:
        return 0.0
    if percentile >= 25.0:
        return 0.25
    if percentile >= 10.0:
        return 0.50
    if percentile >= 5.0:
        return 0.75

    return 1.0


def calculate_global_liquidity_region_score(
    percentile_3m: Optional[float],
    percentile_12m: Optional[float],
    max_points: float = 8.0,
) -> Optional[float]:
    """
    Bewertet die Liquiditätsentwicklung einer Zentralbank.

    Gewichtung V0.1:
    - 12M-Trend: 70 %
    - 3M-Dynamik: 30 %

    Falls nur einer der beiden Horizonte verfügbar ist, wird der
    verfügbare Teil auf das volle Komponentenmaximum normalisiert.
    """

    risk_3m = calculate_global_liquidity_percentile_risk(
        percentile_3m
    )
    risk_12m = calculate_global_liquidity_percentile_risk(
        percentile_12m
    )

    weighted_risk = 0.0
    available_weight = 0.0

    if risk_12m is not None:
        weighted_risk += risk_12m * 0.70
        available_weight += 0.70

    if risk_3m is not None:
        weighted_risk += risk_3m * 0.30
        available_weight += 0.30

    if available_weight == 0.0:
        return None

    normalized_risk = weighted_risk / available_weight

    return _clamp(
        normalized_risk * max_points,
        0.0,
        max_points,
    )


def calculate_block_score(
    component_scores: Dict[str, Optional[float]],
    block_name: str,
) -> Dict[str, object]:
    """
    Berechnet einen normalisierten Blockscore.

    component_scores enthält bereits Risikopunkte der einzelnen Komponenten.
    Beispiel:
        {
            "market_trend": 7.0,
            "credit_stress": 4.5,
            "volatility_stress": None,
            "market_breadth": None,
        }

    None bedeutet: nicht bewertbar / Daten fehlen.

    Fehlende Komponenten werden NICHT mit 0 bewertet.
    Stattdessen werden die verfügbaren Punkte proportional auf das
    vollständige Blockmaximum normalisiert.
    """

    if block_name not in MARKET_RISK_WEIGHTS:
        raise ValueError(f"Unbekannter Markt-Risiko-Block: {block_name}")

    weights = MARKET_RISK_WEIGHTS[block_name]
    block_max = BLOCK_MAX_POINTS[block_name]

    raw_score = 0.0
    assessable_max = 0.0
    available_components = 0

    details = {}

    for component, max_points in weights.items():
        score = component_scores.get(component)

        if score is None:
            details[component] = {
                "score": None,
                "max_points": max_points,
                "available": False,
            }
            continue

        score = _clamp(float(score), 0.0, max_points)

        raw_score += score
        assessable_max += max_points
        available_components += 1

        details[component] = {
            "score": score,
            "max_points": max_points,
            "available": True,
        }

    if assessable_max == 0:
        return {
            "score": None,
            "raw_score": None,
            "max_points": block_max,
            "assessable_max": 0.0,
            "coverage": 0.0,
            "available_components": 0,
            "total_components": len(weights),
            "details": details,
        }

    normalized_score = raw_score / assessable_max * block_max
    coverage = assessable_max / block_max

    return {
        "score": round(normalized_score, 4),
        "raw_score": round(raw_score, 4),
        "max_points": block_max,
        "assessable_max": assessable_max,
        "coverage": round(coverage, 4),
        "available_components": available_components,
        "total_components": len(weights),
        "details": details,
    }


def calculate_market_risk_score(
    component_scores: Dict[str, Optional[float]],
) -> Dict[str, object]:
    """
    Berechnet den vollständigen InRA Market Risk Score.

    Erwartet ein flaches Dictionary mit den 14 Komponenten.

    Der Gesamtscore wird ebenfalls nur aus bewertbaren Blöcken berechnet.
    Innerhalb der Blöcke gilt die Missing-Data-Normalisierung.
    """

    block_results = {}

    for block_name in MARKET_RISK_WEIGHTS:
        block_results[block_name] = calculate_block_score(
            component_scores=component_scores,
            block_name=block_name,
        )

    weighted_score = 0.0
    assessable_total = 0.0

    for block_name, result in block_results.items():
        block_score = result["score"]
        block_max = BLOCK_MAX_POINTS[block_name]

        if block_score is None:
            continue

        weighted_score += block_score
        assessable_total += block_max

    if assessable_total == 0:
        total_score = None
    else:
        total_score = weighted_score / assessable_total * TOTAL_MAX_POINTS
        total_score = round(total_score, 4)

    assessable_component_max = sum(
        result["assessable_max"]
        for result in block_results.values()
    )

    overall_coverage = (
        assessable_component_max / TOTAL_MAX_POINTS
        if TOTAL_MAX_POINTS
        else 0.0
    )

    return {
        "score": total_score,
        "max_points": TOTAL_MAX_POINTS,
        "coverage": round(overall_coverage, 4),
        "blocks": block_results,
    }


def get_market_risk_label(score: Optional[float]) -> str:
    """
    Vorläufige V0.1-Risikostufen.

    Die Grenzen werden nach historischen Tests kalibriert.
    """

    if score is None:
        return "Nicht bewertbar"

    if score < 25:
        return "Niedrig"

    if score < 45:
        return "Moderat"

    if score < 65:
        return "Erhöht"

    if score < 80:
        return "Hoch"

    return "Sehr hoch"
