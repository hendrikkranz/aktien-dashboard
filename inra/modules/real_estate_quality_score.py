"""
Immobilien-Quality V0.1.

Separate Quality-Logik für Immobilienunternehmen.
Die reguläre quantitative Quality-V2-Logik bleibt unverändert.

Score:
- Operative Ertragsentwicklung: 30 Punkte
- Portfolio-Wachstum:           20 Punkte
- Portfolio-Stabilität:         20 Punkte
- Finanzierung:                 30 Punkte

Gesamt:                         100 Punkte
"""


REAL_ESTATE_QUALITY_WEIGHTS = {
    "earnings_growth": 30,
    "portfolio_growth": 20,
    "portfolio_stability": 20,
    "financing": 30,
}

REAL_ESTATE_MIN_COVERAGE = 0.60


def _score_descending(value, thresholds):
    """
    Höherer Wert = besser.

    thresholds:
        [(minimum_value, points), ...]
        absteigend nach minimum_value.
    """
    if value is None:
        return None

    for minimum, points in thresholds:
        if value >= minimum:
            return points

    return 0


def _score_ascending(value, thresholds):
    """
    Niedrigerer Wert = besser.

    thresholds:
        [(maximum_value, points), ...]
        aufsteigend nach maximum_value.
    """
    if value is None:
        return None

    for maximum, points in thresholds:
        if value <= maximum:
            return points

    return 0


# ------------------------------------------------------------------
# Operative Ertragsentwicklung – 30 Punkte
# Bevorzugt: AFFO-/FFO-Wachstum je Aktie.
# Alternativ eine fachlich vergleichbare operative Immobilien-KPI.
# ------------------------------------------------------------------

def calculate_real_estate_growth_score(growth_pct):
    return _score_descending(
        growth_pct,
        [
            (10.0, 30),
            (7.0, 27),
            (5.0, 24),
            (3.0, 20),
            (0.0, 15),
            (-3.0, 9),
            (-7.0, 5),
        ],
    )


# ------------------------------------------------------------------
# Portfolio-Wachstum – 20 Punkte
# Same-store NOI / Like-for-like rents / vergleichbare operative KPI.
# ------------------------------------------------------------------

def calculate_portfolio_growth_score(growth_pct):
    return _score_descending(
        growth_pct,
        [
            (6.0, 20),
            (4.0, 18),
            (3.0, 16),
            (2.0, 12),
            (0.0, 8),
            (-2.0, 4),
        ],
    )


# ------------------------------------------------------------------
# Portfolio-Stabilität – 20 Punkte
# Standardfall: Occupancy.
# Subtyp-spezifische Alternativen können auf dieselbe
# 0–20-Skala abgebildet werden.
# ------------------------------------------------------------------

def calculate_occupancy_score(occupancy_pct):
    return _score_descending(
        occupancy_pct,
        [
            (97.0, 20),
            (95.0, 18),
            (93.0, 16),
            (90.0, 12),
            (87.0, 8),
            (83.0, 4),
        ],
    )


def calculate_vacancy_score(vacancy_pct):
    if vacancy_pct is None:
        return None

    return calculate_occupancy_score(100.0 - vacancy_pct)


# ------------------------------------------------------------------
# Finanzierung – Verschuldung – 18 Punkte
# Primär: LTV.
# ------------------------------------------------------------------

def calculate_ltv_score(ltv_pct):
    return _score_ascending(
        ltv_pct,
        [
            (30.0, 18),
            (35.0, 16),
            (40.0, 14),
            (45.0, 11),
            (50.0, 7),
            (55.0, 3),
        ],
    )


# Fallback, wenn kein belastbarer LTV verfügbar ist.
def calculate_net_debt_ebitda_score(net_debt_ebitda):
    return _score_ascending(
        net_debt_ebitda,
        [
            (4.0, 18),
            (4.5, 16),
            (5.0, 14),
            (5.5, 11),
            (6.0, 8),
            (6.5, 5),
            (7.0, 2),
        ],
    )


# ------------------------------------------------------------------
# Finanzierung – Tragfähigkeit – 12 Punkte
# Interest Coverage / Fixed-Charge Coverage.
# ------------------------------------------------------------------

def calculate_coverage_score(coverage):
    return _score_descending(
        coverage,
        [
            (6.0, 12),
            (5.0, 11),
            (4.0, 9),
            (3.0, 7),
            (2.5, 5),
            (2.0, 3),
        ],
    )


# ------------------------------------------------------------------
# Block-Helfer
# ------------------------------------------------------------------

def _normalize_block(parts):
    """
    Summiert die tatsächlich verfügbaren Teilkennzahlen eines Blocks.

    parts:
        [(points, maximum_points), ...]

    Fehlende Kennzahlen werden nicht als 0 gewertet.
    Eine Normalisierung auf 100 erfolgt ausschließlich im Gesamtmodell.
    """
    available = [
        (points, maximum)
        for points, maximum in parts
        if points is not None
    ]

    if not available:
        return None, 0

    raw_points = sum(points for points, _ in available)
    available_maximum = sum(maximum for _, maximum in available)

    return raw_points, available_maximum


def calculate_portfolio_quality_score(
    portfolio_growth_pct=None,
    occupancy_pct=None,
    vacancy_pct=None,
    stability_score=None,
):
    growth_score = calculate_portfolio_growth_score(
        portfolio_growth_pct
    )

    if stability_score is not None:
        stability_points = max(
            0,
            min(float(stability_score), 20),
        )
        stability_source = "subtype_specific"
    elif occupancy_pct is not None:
        stability_points = calculate_occupancy_score(
            occupancy_pct
        )
        stability_source = "occupancy"
    else:
        stability_points = calculate_vacancy_score(
            vacancy_pct
        )
        stability_source = (
            "vacancy"
            if vacancy_pct is not None
            else None
        )

    score, available_maximum = _normalize_block(
        [
            (growth_score, 20),
            (stability_points, 20),
        ]
    )

    return {
        "score": score,
        "available_maximum": available_maximum,
        "growth_score": growth_score,
        "stability_score": stability_points,
        "stability_source": stability_source,
    }


def calculate_financing_quality_score(
    ltv_pct=None,
    net_debt_ebitda=None,
    coverage=None,
):
    if ltv_pct is not None:
        leverage_score = calculate_ltv_score(ltv_pct)
        leverage_source = "ltv"
    else:
        leverage_score = calculate_net_debt_ebitda_score(
            net_debt_ebitda
        )
        leverage_source = (
            "net_debt_ebitda"
            if net_debt_ebitda is not None
            else None
        )

    coverage_score = calculate_coverage_score(coverage)

    score, available_maximum = _normalize_block(
        [
            (leverage_score, 18),
            (coverage_score, 12),
        ]
    )

    return {
        "score": score,
        "available_maximum": available_maximum,
        "leverage_score": leverage_score,
        "leverage_source": leverage_source,
        "coverage_score": coverage_score,
    }


# ------------------------------------------------------------------
# Gesamtmodell
#
# Bewusst schlankes Immobilien-Quality-Modell:
# - operative Ertragsentwicklung: 30 Punkte
# - Portfolio-Wachstum:           20 Punkte
# - Portfolio-Stabilität:         20 Punkte
# - Finanzierung:                 30 Punkte
#
# Kursabhängige Bewertungskennzahlen wie P/FFO oder Kurs/NAV
# gehören nicht in den Quality-Score.
# ------------------------------------------------------------------

def calculate_real_estate_quality_score(
    growth_pct=None,
    portfolio_growth_pct=None,
    occupancy_pct=None,
    vacancy_pct=None,
    stability_score=None,
    ltv_pct=None,
    net_debt_ebitda=None,
    coverage=None,
):
    earnings_growth_score = calculate_real_estate_growth_score(
        growth_pct
    )

    portfolio = calculate_portfolio_quality_score(
        portfolio_growth_pct=portfolio_growth_pct,
        occupancy_pct=occupancy_pct,
        vacancy_pct=vacancy_pct,
        stability_score=stability_score,
    )

    financing = calculate_financing_quality_score(
        ltv_pct=ltv_pct,
        net_debt_ebitda=net_debt_ebitda,
        coverage=coverage,
    )

    blocks = [
        (
            earnings_growth_score,
            30 if earnings_growth_score is not None else 0,
        ),
        (
            portfolio["score"],
            portfolio["available_maximum"],
        ),
        (
            financing["score"],
            financing["available_maximum"],
        ),
    ]

    available = [
        (points, maximum)
        for points, maximum in blocks
        if points is not None
    ]

    available_maximum = sum(
        maximum
        for _, maximum in available
    )

    coverage_ratio = available_maximum / 100

    if (
        not available
        or coverage_ratio < REAL_ESTATE_MIN_COVERAGE
    ):
        total_score = None
    else:
        total_score = round(
            sum(points for points, _ in available)
            / available_maximum
            * 100
        )

    return {
        "score": total_score,
        "available_maximum": available_maximum,
        "coverage_ratio": coverage_ratio,
        "earnings_growth_score": earnings_growth_score,
        "portfolio_score": portfolio["score"],
        "financing_score": financing["score"],
        "portfolio": portfolio,
        "financing": financing,
    }
