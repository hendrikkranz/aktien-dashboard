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
