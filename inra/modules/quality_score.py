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

def calculate_operating_margin_ratio(
    operating_margin: Optional[float],
) -> Optional[float]:
    if operating_margin is None:
        return None

    if operating_margin >= 35:
        return 1.0
    if operating_margin >= 25:
        return 0.90
    if operating_margin >= 15:
        return 0.75
    if operating_margin >= 10:
        return 0.60
    if operating_margin >= 5:
        return 0.45
    if operating_margin >= 0:
        return 0.25

    return 0.0


def calculate_profitability_score(
    roe: Optional[float],
    net_margin: Optional[float],
    operating_margin: Optional[float],
    max_points: int,
) -> int:
    weighted_ratios = [
        (calculate_roe_ratio(roe), 0.40),
        (calculate_margin_ratio(net_margin), 0.30),
        (
            calculate_operating_margin_ratio(
                operating_margin
            ),
            0.30,
        ),
    ]

    available_ratios = [
        (ratio, weight)
        for ratio, weight in weighted_ratios
        if ratio is not None
    ]

    if not available_ratios:
        return 0

    weighted_score = sum(
        ratio * weight
        for ratio, weight in available_ratios
    )

    available_weight = sum(
        weight
        for _, weight in available_ratios
    )

    normalized_ratio = (
        weighted_score / available_weight
    )

    return round(max_points * normalized_ratio)


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


def calculate_earnings_growth_ratio(
    earnings_growth: Optional[float],
) -> Optional[float]:
    if earnings_growth is None:
        return None

    if earnings_growth >= 25:
        return 1.0
    if earnings_growth >= 15:
        return 0.85
    if earnings_growth >= 10:
        return 0.75
    if earnings_growth >= 5:
        return 0.60
    if earnings_growth >= 0:
        return 0.45
    if earnings_growth >= -5:
        return 0.25
    if earnings_growth >= -15:
        return 0.10

    return 0.0
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
    revenue_growth_median: Optional[float],
    income_growth_median: Optional[float],
    growth_history_reliable: Optional[bool],
    max_points: int,
    positive_revenue_years: Optional[int] = None,
    revenue_growth_annual: Optional[float] = None,
    earnings_growth_annual: Optional[float] = None,
    positive_income_years: Optional[int] = None,
    extreme_revenue_jump: Optional[bool] = None,
    income_sign_change: Optional[bool] = None,
) -> int:
    if revenue_growth_annual is not None:
        revenue_growth = revenue_growth_annual
    if earnings_growth_annual is not None:
        earnings_growth = earnings_growth_annual
    if revenue_growth_median is not None:
        if positive_revenue_years is None:
            revenue_growth = revenue_growth_median
        elif positive_revenue_years >= 2:
            revenue_growth = revenue_growth_median

    if income_growth_median is not None:
        if positive_income_years is None:
            earnings_growth = income_growth_median
        elif positive_income_years >= 2:
            earnings_growth = income_growth_median
    
    revenue_ratio = calculate_revenue_growth_ratio(
        revenue_growth
    )

    if revenue_ratio is None:
        return 0

    base_score = round(max_points * revenue_ratio)

    earnings_ratio = calculate_earnings_growth_ratio(
        earnings_growth
    )

    if earnings_ratio is None:
        return base_score

    final_score = round(
        max_points * (
            revenue_ratio * 0.60
            + earnings_ratio * 0.40
        )
    )

    return max(0, min(final_score, max_points))


def calculate_balance_score(
    debt_ratio: Optional[float],
    cash_to_debt_ratio: Optional[float],
    ocf_to_debt_ratio: Optional[float],
    max_points: int,
) -> int:
    if (
        debt_ratio is None
        and cash_to_debt_ratio is None
        and ocf_to_debt_ratio is None
    ):
        return 0

    weighted_scores = []

    if debt_ratio is not None:
        if debt_ratio <= 20:
            debt_score = 1.00
        elif debt_ratio <= 40:
            debt_score = 0.90
        elif debt_ratio <= 70:
            debt_score = 0.80
        elif debt_ratio <= 100:
            debt_score = 0.65
        elif debt_ratio <= 150:
            debt_score = 0.45
        elif debt_ratio <= 200:
            debt_score = 0.25
        else:
            debt_score = 0.00

        weighted_scores.append((debt_score, 0.50))

    if cash_to_debt_ratio is not None:
        if cash_to_debt_ratio >= 1.0:
            cash_score = 1.00
        elif cash_to_debt_ratio >= 0.6:
            cash_score = 0.80
        elif cash_to_debt_ratio >= 0.4:
            cash_score = 0.60
        elif cash_to_debt_ratio >= 0.2:
            cash_score = 0.40
        else:
            cash_score = 0.20

        weighted_scores.append((cash_score, 0.25))

    if ocf_to_debt_ratio is not None:
        if ocf_to_debt_ratio >= 1.0:
            ocf_score = 1.00
        elif ocf_to_debt_ratio >= 0.6:
            ocf_score = 0.80
        elif ocf_to_debt_ratio >= 0.3:
            ocf_score = 0.60
        elif ocf_to_debt_ratio >= 0.15:
            ocf_score = 0.40
        elif ocf_to_debt_ratio > 0:
            ocf_score = 0.20
        else:
            ocf_score = 0.00

        weighted_scores.append((ocf_score, 0.25))

    available_weight = sum(weight for _, weight in weighted_scores)

    if available_weight == 0:
        return 0

    normalized_score = (
        sum(score * weight for score, weight in weighted_scores)
        / available_weight
    )

    return round(max_points * normalized_score)


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
            data.get("Operative Marge"),
            profit_weight,
        ),
        "Wachstum": calculate_growth_score(
            data.get("Umsatzwachstum"),
            data.get("Gewinnwachstum"),
            data.get("Umsatzwachstum Median 3J"),
            data.get("Gewinnwachstum Median 3J"),
            data.get("Wachstumshistorie belastbar"),
            growth_weight,
            data.get("Positive Umsatzjahre"),
            data.get("Umsatzwachstum Jahresabschluss"),
            data.get("Gewinnwachstum Jahresabschluss"),
            data.get("Positive Gewinnjahre"),
            data.get("Extremer Umsatzsprung"),
            data.get("Gewinn Vorzeichenwechsel"),
        ),
        "Bilanz": calculate_balance_score(
            data.get("Verschuldungsgrad"),
            (
                data.get("Gesamtliquidität") / data.get("Gesamtverschuldung")
                if data.get("Gesamtliquidität") is not None
                and data.get("Gesamtverschuldung") not in (None, 0)
                else None
            ),
            (
                data.get("Operativer Cashflow") / data.get("Gesamtverschuldung")
                if data.get("Operativer Cashflow") is not None
                and data.get("Gesamtverschuldung") not in (None, 0)
                else None
            ),
            balance_weight,
            ),
    }


def calculate_quality_score(data: dict) -> int:
    breakdown = calculate_quality_breakdown(data)

    return min(sum(breakdown.values()), 100)