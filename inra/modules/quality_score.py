from typing import Optional

from config.scoring import QUALITY_WEIGHTS


def calculate_roe_ratio(
    roe: Optional[float],
) -> Optional[float]:
    if roe is None:
        return None

    if roe >= 35:
        return 1.0
    if roe >= 30:
        return 0.90
    if roe >= 20:
        return 0.80
    if roe >= 15:
        return 0.65
    if roe >= 10:
        return 0.50
    if roe >= 5:
        return 0.30

    return 0.0


def calculate_margin_ratio(
    net_margin: Optional[float],
) -> Optional[float]:
    if net_margin is None:
        return None

    if net_margin >= 35:
        return 1.0
    if net_margin >= 25:
        return 0.90
    if net_margin >= 15:
        return 0.75
    if net_margin >= 10:
        return 0.60
    if net_margin >= 5:
        return 0.45
    if net_margin >= 0:
        return 0.25

    return 0.0


def calculate_profitability_score(
    roe: Optional[float],
    net_margin: Optional[float],
    max_points: int,
) -> int:
    available_ratios = [
        ratio
        for ratio in (
            calculate_roe_ratio(roe),
            calculate_margin_ratio(net_margin),
        )
        if ratio is not None
    ]

    if not available_ratios:
        return 0

    average_ratio = sum(available_ratios) / len(
        available_ratios
    )

    return round(max_points * average_ratio)


def calculate_revenue_growth_ratio(
    revenue_growth: Optional[float],
) -> Optional[float]:
    if revenue_growth is None:
        return None

    if revenue_growth >= 25:
        return 0.95
    if revenue_growth >= 15:
        return 0.82
    if revenue_growth >= 10:
        return 0.72
    if revenue_growth >= 6:
        return 0.62
    if revenue_growth >= 3:
        return 0.53
    if revenue_growth >= 0:
        return 0.45
    if revenue_growth >= -3:
        return 0.30
    if revenue_growth >= -8:
        return 0.15

    return 0.0


def calculate_earnings_modifier(
    earnings_growth: Optional[float],
    max_points: int,
) -> int:
    if earnings_growth is None:
        return 0

    if earnings_growth >= 25:
        return round(max_points * 0.10)
    if earnings_growth >= 10:
        return round(max_points * 0.07)
    if earnings_growth >= 3:
        return round(max_points * 0.04)
    if earnings_growth >= -10:
        return 0
    if earnings_growth >= -25:
        return -round(max_points * 0.04)

    return -round(max_points * 0.07)


def calculate_growth_score(
    revenue_growth: Optional[float],
    earnings_growth: Optional[float],
    max_points: int,
) -> int:
    revenue_ratio = calculate_revenue_growth_ratio(
        revenue_growth
    )

    if revenue_ratio is None:
        return 0

    base_score = round(max_points * revenue_ratio)

    earnings_modifier = calculate_earnings_modifier(
        earnings_growth,
        max_points,
    )

    final_score = base_score + earnings_modifier

    return max(0, min(final_score, max_points))


def calculate_balance_score(
    debt_ratio: Optional[float],
    max_points: int,
) -> int:
    if debt_ratio is None:
        return 0

    if debt_ratio <= 20:
        ratio = 1.0
    elif debt_ratio <= 40:
        ratio = 0.90
    elif debt_ratio <= 70:
        ratio = 0.80
    elif debt_ratio <= 100:
        ratio = 0.70
    elif debt_ratio <= 150:
        ratio = 0.60
    elif debt_ratio <= 200:
        ratio = 0.50
    elif debt_ratio <= 250:
        ratio = 0.35
    elif debt_ratio <= 300:
        ratio = 0.20
    else:
        ratio = 0.0

    return round(max_points * ratio)


def calculate_dividend_score(
    dividend_yield: Optional[float],
) -> int:
    if dividend_yield is None or dividend_yield <= 0:
        return 0

    if dividend_yield >= 6:
        return 15
    if dividend_yield >= 5:
        return 12
    if dividend_yield >= 4:
        return 10
    if dividend_yield >= 3:
        return 8
    if dividend_yield >= 2:
        return 6
    if dividend_yield >= 1:
        return 4

    return 3


def calculate_quality_breakdown(data: dict) -> dict:
    profit_weight = QUALITY_WEIGHTS["profitabilitaet"]
    growth_weight = QUALITY_WEIGHTS["wachstum"]
    balance_weight = QUALITY_WEIGHTS["bilanz"]

    return {
        "Profitabilität": calculate_profitability_score(
            data.get("Eigenkapitalrendite"),
            data.get("Nettomarge"),
            profit_weight,
        ),
        "Wachstum": calculate_growth_score(
            data.get("Umsatzwachstum"),
            data.get("Gewinnwachstum"),
            growth_weight,
        ),
        "Bilanz": calculate_balance_score(
            data.get("Verschuldungsgrad"),
            balance_weight,
        ),
        "Dividende": calculate_dividend_score(
            data.get("Dividendenrendite"),
        ),
    }


def calculate_quality_score(data: dict) -> int:
    breakdown = calculate_quality_breakdown(data)

    return min(sum(breakdown.values()), 100)