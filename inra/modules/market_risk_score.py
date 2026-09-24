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
        "initial_jobless_claims": 3.0,
    },
    "fall_height": {
        "valuation": 25.0,
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



def calculate_market_breadth_score(
    percent_above_sma200: Optional[float],
    max_points: float = 7.0,
) -> Optional[float]:
    """
    Bewertet die US-Marktbreite anhand des Anteils der
    S&P-500-Mitglieder oberhalb ihrer individuellen SMA200.

    V0.1:
    >= 70 % -> 0 / 7
    >= 60 % -> 1 / 7
    >= 50 % -> 2 / 7
    >= 40 % -> 4 / 7
    >= 30 % -> 5 / 7
    >= 20 % -> 6 / 7
    <  20 % -> 7 / 7

    Die 50-%-Marke wird bewusst als Regimegrenze behandelt.
    Coverage wird in der Datenkomponente geprüft.
    """
    if percent_above_sma200 is None:
        return None

    value = float(percent_above_sma200)

    if value < 0.0 or value > 100.0:
        return None

    if value >= 70.0:
        base_score = 0.0
    elif value >= 60.0:
        base_score = 1.0
    elif value >= 50.0:
        base_score = 2.0
    elif value >= 40.0:
        base_score = 4.0
    elif value >= 30.0:
        base_score = 5.0
    elif value >= 20.0:
        base_score = 6.0
    else:
        base_score = 7.0

    return base_score / 7.0 * max_points


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

def is_substantial_yield_curve_inversion(
    monthly_spreads,
    threshold: float = -0.10,
    min_months: int = 3,
) -> bool:
    """
    Erkennt eine substanzielle Zinskurveninversion.

    V0.1:
    - Monatsdurchschnitt des Spreads <= -0,10 Prozentpunkte
    - mindestens 3 aufeinanderfolgende Monate

    Kurze Bewegungen knapp unter null gelten damit nicht automatisch
    als makroökonomisch relevantes Inversionssignal.
    """

    if monthly_spreads is None or len(monthly_spreads) < min_months:
        return False

    consecutive_months = 0

    for spread in monthly_spreads:
        if spread is not None and float(spread) <= threshold:
            consecutive_months += 1

            if consecutive_months >= min_months:
                return True
        else:
            consecutive_months = 0

    return False

def find_last_substantial_yield_curve_inversion(
    monthly_spreads,
    threshold: float = -0.10,
    min_months: int = 3,
):
    """
    Findet die letzte substanzielle Zinskurveninversion.

    Rückgabe:
    - start_index
    - end_index
    - duration_months
    - minimum_spread

    Falls keine substanzielle Inversion vorhanden ist: None.
    """

    if monthly_spreads is None or len(monthly_spreads) < min_months:
        return None

    phases = []
    start_index = None

    for index, spread in enumerate(monthly_spreads):
        is_inverted = (
            spread is not None
            and float(spread) <= threshold
        )

        if is_inverted and start_index is None:
            start_index = index

        if not is_inverted and start_index is not None:
            end_index = index - 1

            if end_index - start_index + 1 >= min_months:
                phases.append((start_index, end_index))

            start_index = None

    if start_index is not None:
        end_index = len(monthly_spreads) - 1

        if end_index - start_index + 1 >= min_months:
            phases.append((start_index, end_index))

    if not phases:
        return None

    start_index, end_index = phases[-1]
    phase_values = monthly_spreads.iloc[start_index:end_index + 1]

    return {
        "start_index": start_index,
        "end_index": end_index,
        "duration_months": end_index - start_index + 1,
        "minimum_spread": float(phase_values.min()),
    }

def calculate_yield_curve_state_risk(
    current_spread: Optional[float],
) -> Optional[float]:
    """
    Bewertet den aktuellen Zustand eines Yield-Curve-Spreads
    als Risikofaktor von 0 bis 1.

    V0.1:
    > +0,50 pp        -> 0,00
    0 bis +0,50 pp    -> 0,25
    0 bis -0,10 pp    -> 0,50
    -0,10 bis -0,50   -> 0,75
    <= -0,50 pp       -> 1,00

    Die vorausgegangene Inversion und das Re-Steepening werden
    separat in der Regime-/Dynamik-Komponente bewertet.
    """

    if current_spread is None:
        return None

    spread = float(current_spread)

    if spread > 0.50:
        return 0.0
    if spread >= 0.0:
        return 0.25
    if spread > -0.10:
        return 0.50
    if spread > -0.50:
        return 0.75

    return 1.0

def calculate_yield_curve_regime_risk(
    months_since_inversion_end: Optional[int],
    resteepening_from_minimum: Optional[float],
) -> Optional[float]:
    """
    Bewertet das Yield-Curve-Regime als Risikofaktor von 0 bis 1.

    V0.1:
    - laufende substanzielle Inversion: 0,75
    - Post-Inversion bis 36 Monate:
        Re-Steepening < 0,50 pp  -> 0,25
        < 1,00 pp                -> 0,50
        < 2,00 pp                -> 0,75
        >= 2,00 pp               -> 1,00
    - mehr als 36 Monate nach Inversionsende: 0,00

    Der Faktor ist ein Frühwarnsignal und keine Crash-Prognose.
    """

    if (
        months_since_inversion_end is None
        or resteepening_from_minimum is None
    ):
        return None

    months = int(months_since_inversion_end)
    resteepening = float(resteepening_from_minimum)

    if months == 0:
        return 0.75

    if months > 36:
        return 0.0

    if resteepening < 0.50:
        return 0.25
    if resteepening < 1.00:
        return 0.50
    if resteepening < 2.00:
        return 0.75

    return 1.0

def calculate_yield_curve_series_score(
    current_spread: Optional[float],
    months_since_inversion_end: Optional[int],
    resteepening_from_minimum: Optional[float],
    max_points: float = 7.0,
) -> Optional[float]:
    """
    Berechnet den Risikoscore einer einzelnen Yield-Curve-Reihe.

    V0.1:
    - 40 % aktueller Kurvenzustand
    - 60 % Inversions-/Re-Steepening-Regime

    Fehlende Teilkomponenten werden nicht als 0 Risiko behandelt.
    Ist nur eine Komponente verfügbar, erhält sie das volle Gewicht.
    """

    state_risk = calculate_yield_curve_state_risk(
        current_spread
    )

    regime_risk = calculate_yield_curve_regime_risk(
        months_since_inversion_end,
        resteepening_from_minimum,
    )

    components = [
        (state_risk, 0.40),
        (regime_risk, 0.60),
    ]

    weighted_risk = 0.0
    available_weight = 0.0

    for risk, weight in components:
        if risk is None:
            continue

        weighted_risk += risk * weight
        available_weight += weight

    if available_weight == 0:
        return None

    normalized_risk = weighted_risk / available_weight

    return _clamp(
        normalized_risk * max_points,
        0.0,
        max_points,
    )

def calculate_oecd_cli_dynamics_risk(
    change_3m: Optional[float],
    change_6m: Optional[float],
) -> Optional[float]:
    """
    Bewertet Stärke und Persistenz der CLI-Bewegung.

    0.0 = klar positive Dynamik
    1.0 = außergewöhnlich starke negative Dynamik

    3M und 6M werden gleich gewichtet. Die Schwellen orientieren sich
    an den historischen Verteilungen von USA, G4E, China und G20.
    """

    def _score_change(change: Optional[float], horizon: str) -> Optional[float]:
        if change is None:
            return None

        change = float(change)

        if horizon == "3m":
            if change >= 0.0:
                return 0.0
            if change > -0.25:
                return 0.25
            if change > -0.50:
                return 0.50
            if change > -0.80:
                return 0.75
            return 1.0

        if change >= 0.0:
            return 0.0
        if change > -0.50:
            return 0.25
        if change > -0.90:
            return 0.50
        if change > -1.50:
            return 0.75
        return 1.0

    scores = [
        score
        for score in [
            _score_change(change_3m, "3m"),
            _score_change(change_6m, "6m"),
        ]
        if score is not None
    ]

    if not scores:
        return None

    return sum(scores) / len(scores)


def calculate_oecd_cli_regime_risk(
    current_value: Optional[float],
    change_3m: Optional[float],
) -> Optional[float]:
    """
    Bewertet das aktuelle CLI-Regime.

    Historische US-Tests zeigen:
    - über 100 + fallend: höchste Frühwarnwirkung
    - unter 100 + fallend: ebenfalls erhöht
    - über 100 + steigend: niedrig
    - unter 100 + steigend: niedrigste Frühwarnwirkung

    Das Niveau unter 100 wird deshalb nicht automatisch als hohes
    Aktienmarktrisiko interpretiert.
    """

    if current_value is None or change_3m is None:
        return None

    above_100 = float(current_value) >= 100.0
    rising = float(change_3m) > 0.0

    if above_100 and rising:
        return 0.20

    if above_100 and not rising:
        return 1.00

    if not above_100 and rising:
        return 0.00

    return 0.85


def calculate_oecd_cli_breadth_risk(
    regional_change_3m: Dict[str, Optional[float]],
) -> Optional[float]:
    """
    Bewertet die globale Breite der CLI-Abschwächung.

    Entscheidend ist der Anteil der verfügbaren Regionen mit
    negativer 3M-Dynamik. Fehlende Regionen werden nicht als
    risikofrei behandelt.
    """

    available = [
        float(change)
        for change in regional_change_3m.values()
        if change is not None
    ]

    if not available:
        return None

    falling_share = sum(
        change < 0.0
        for change in available
    ) / len(available)

    if falling_share == 0.0:
        return 0.0

    if falling_share <= 0.25:
        return 0.25

    if falling_share <= 0.50:
        return 0.50

    if falling_share <= 0.75:
        return 0.75

    return 1.0


def calculate_oecd_cli_score(
    regional_metrics: Dict[str, Dict[str, Optional[float]]],
    max_points: float = 7.0,
) -> Optional[float]:
    """
    Berechnet den OECD-CLI-Frühwarnscore.

    V0.1:
    - 50 % Dynamik
    - 30 % Regime
    - 20 % globale Breite

    Regionale Gewichte:
    - USA 40 %
    - G4E 25 %
    - China 20 %
    - G20 15 %

    Fehlende Regionen werden innerhalb der verfügbaren Gewichte
    normalisiert und niemals als 0 Risiko behandelt.
    """

    region_weights = {
        "USA": 0.40,
        "G4E": 0.25,
        "CHN": 0.20,
        "G20": 0.15,
    }

    weighted_dynamics = 0.0
    dynamics_weight = 0.0

    weighted_regime = 0.0
    regime_weight = 0.0

    regional_change_3m = {}

    for region, weight in region_weights.items():
        metrics = regional_metrics.get(region, {})

        current_value = metrics.get("current_value")
        change_3m = metrics.get("change_3m")
        change_6m = metrics.get("change_6m")

        regional_change_3m[region] = change_3m

        dynamics_risk = calculate_oecd_cli_dynamics_risk(
            change_3m=change_3m,
            change_6m=change_6m,
        )

        if dynamics_risk is not None:
            weighted_dynamics += dynamics_risk * weight
            dynamics_weight += weight

        regime_risk = calculate_oecd_cli_regime_risk(
            current_value=current_value,
            change_3m=change_3m,
        )

        if regime_risk is not None:
            weighted_regime += regime_risk * weight
            regime_weight += weight

    dynamics = (
        weighted_dynamics / dynamics_weight
        if dynamics_weight > 0.0
        else None
    )

    regime = (
        weighted_regime / regime_weight
        if regime_weight > 0.0
        else None
    )

    breadth = calculate_oecd_cli_breadth_risk(
        regional_change_3m
    )

    components = [
        (dynamics, 0.50),
        (regime, 0.30),
        (breadth, 0.20),
    ]

    weighted_score = 0.0
    available_weight = 0.0

    for value, weight in components:
        if value is None:
            continue

        weighted_score += value * weight
        available_weight += weight

    if available_weight == 0.0:
        return None

    normalized_risk = weighted_score / available_weight

    return _clamp(
        normalized_risk * max_points,
        0.0,
        max_points,
    )


def calculate_broad_dollar_change_risk(
    change_pct: Optional[float],
    horizon: str,
) -> Optional[float]:
    """
    Bewertet eine Aufwertung des breiten handelsgewichteten US-Dollars.

    Nur Dollaraufwertungen erzeugen Risikopunkte.
    Ein fallender oder unveränderter Dollar wird mit 0 bewertet.

    Die Schwellen orientieren sich an den historischen Verteilungen
    des Fed Broad Dollar Index seit 2006.
    """

    if change_pct is None:
        return None

    change_pct = float(change_pct)

    if change_pct <= 0.0:
        return 0.0

    if horizon == "3m":
        if change_pct < 2.0:
            return 0.25
        if change_pct < 4.5:
            return 0.50
        if change_pct < 5.5:
            return 0.75
        return 1.0

    if horizon == "6m":
        if change_pct < 3.3:
            return 0.25
        if change_pct < 5.5:
            return 0.50
        if change_pct < 7.2:
            return 0.75
        return 1.0

    raise ValueError(
        "horizon muss '3m' oder '6m' sein."
    )


def calculate_broad_dollar_score(
    change_3m_pct: Optional[float],
    change_6m_pct: Optional[float],
    max_points: float = 5.0,
) -> Optional[float]:
    """
    Berechnet den Broad-Dollar-Frühwarnscore.

    V0.1:
    - 60 % kurzfristige 3M-Dollaraufwertung
    - 40 % 6M-Persistenz

    Fehlende Horizonte werden innerhalb der verfügbaren Gewichte
    normalisiert und niemals als 0 Risiko behandelt.
    """

    components = [
        (
            calculate_broad_dollar_change_risk(
                change_3m_pct,
                "3m",
            ),
            0.60,
        ),
        (
            calculate_broad_dollar_change_risk(
                change_6m_pct,
                "6m",
            ),
            0.40,
        ),
    ]

    weighted_risk = 0.0
    available_weight = 0.0

    for risk, weight in components:
        if risk is None:
            continue

        weighted_risk += risk * weight
        available_weight += weight

    if available_weight == 0.0:
        return None

    normalized_risk = weighted_risk / available_weight

    return _clamp(
        normalized_risk * max_points,
        0.0,
        max_points,
    )

def calculate_inflation_percentile_risk(
    percentile: Optional[float],
) -> Optional[float]:
    """
    Übersetzt das historische Perzentil einer Inflationskennzahl
    in einen Risikowert zwischen 0 und 1.

    V0.1:
    - < P50:       0.00
    - P50 bis P75: 0.25
    - P75 bis P90: 0.50
    - P90 bis P95: 0.75
    - >= P95:      1.00

    Die Perzentile werden regions- und kennzahlenspezifisch aus
    der jeweiligen verfügbaren Historie berechnet.
    """

    if percentile is None:
        return None

    if percentile < 50.0:
        return 0.0

    if percentile < 75.0:
        return 0.25

    if percentile < 90.0:
        return 0.50

    if percentile < 95.0:
        return 0.75

    return 1.0


def calculate_inflation_series_risk(
    yoy_percentile: Optional[float],
    momentum_3m_percentile: Optional[float],
) -> Optional[float]:
    """
    Berechnet das Risiko einer Inflationsreihe.

    V0.1:
    - 60 % Inflationsniveau (YoY)
    - 40 % kurzfristige Dynamik (3M annualisiert)

    Fehlende Teilkomponenten werden innerhalb der verfügbaren
    Gewichte normalisiert.
    """

    components = [
        (
            calculate_inflation_percentile_risk(
                yoy_percentile,
            ),
            0.60,
        ),
        (
            calculate_inflation_percentile_risk(
                momentum_3m_percentile,
            ),
            0.40,
        ),
    ]

    weighted_risk = 0.0
    available_weight = 0.0

    for risk, weight in components:
        if risk is None:
            continue

        weighted_risk += risk * weight
        available_weight += weight

    if available_weight == 0.0:
        return None

    return weighted_risk / available_weight


def calculate_inflation_region_score(
    headline_yoy_percentile: Optional[float],
    headline_3m_percentile: Optional[float],
    core_yoy_percentile: Optional[float] = None,
    core_3m_percentile: Optional[float] = None,
    max_points: float = 5.0,
) -> Optional[float]:
    """
    Berechnet den regionalen Inflation-Trend-Score.

    V0.1:
    - Headline Inflation: 75 %
    - Core Inflation:     25 %

    Core ist optional. Wenn Core fachlich nicht verwendet wird
    oder nicht verfügbar ist, erhält Headline das volle verfügbare
    Gewicht. Fehlende Daten werden niemals als 0 Risiko behandelt.
    """

    headline_risk = calculate_inflation_series_risk(
        headline_yoy_percentile,
        headline_3m_percentile,
    )

    core_risk = calculate_inflation_series_risk(
        core_yoy_percentile,
        core_3m_percentile,
    )

    components = [
        (headline_risk, 0.75),
        (core_risk, 0.25),
    ]

    weighted_risk = 0.0
    available_weight = 0.0

    for risk, weight in components:
        if risk is None:
            continue

        weighted_risk += risk * weight
        available_weight += weight

    if available_weight == 0.0:
        return None

    normalized_risk = weighted_risk / available_weight

    return _clamp(
        normalized_risk * max_points,
        0.0,
        max_points,
    )


def calculate_initial_jobless_claims_score(
    rise_from_52w_low_pct: Optional[float],
    max_points: float = 3.0,
) -> Optional[float]:
    """
    Bewertet die Verschlechterung der US Initial Jobless Claims.

    Grundlage ist der 4-Wochen-Durchschnitt der Erstanträge relativ
    zu seinem niedrigsten Stand der vergangenen 52 Wochen.

    V0.1 ist bewusst nicht monoton:
    Der historische Test zeigt die stärkste Frühwarnwirkung bei einer
    Verschlechterung um etwa 20 bis 50 Prozent. Bei noch höheren Werten
    ist die Arbeitsmarktverschlechterung häufig bereits weit fortgeschritten.
    """

    if rise_from_52w_low_pct is None:
        return None

    if rise_from_52w_low_pct < 10.0:
        risk = 0.0
    elif rise_from_52w_low_pct < 20.0:
        risk = 0.5 / 3.0
    elif rise_from_52w_low_pct < 30.0:
        risk = 1.0
    elif rise_from_52w_low_pct < 50.0:
        risk = 2.0 / 3.0
    else:
        risk = 1.0 / 3.0

    return _clamp(
        risk * max_points,
        0.0,
        max_points,
    )


def calculate_valuation_cape_score(
    historical_percentile,
    max_points=10.0,
):
    """Score market valuation risk from the historical CAPE percentile."""
    if historical_percentile is None:
        return None

    percentile = _clamp(float(historical_percentile), 0.0, 100.0)

    if percentile < 60.0:
        risk = 0.0
    elif percentile < 80.0:
        risk = 2.0 / 10.0
    elif percentile < 90.0:
        risk = 4.0 / 10.0
    elif percentile < 97.0:
        risk = 7.0 / 10.0
    else:
        risk = 1.0

    return risk * max_points

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
