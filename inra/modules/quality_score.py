from typing import Optional

from config.scoring import QUALITY_WEIGHTS

from config.industry_mapping import (
    get_industry_model,
    get_quality_benchmarks_for_yahoo_industry,
    get_roe_benchmark_for_yahoo_industry,
)

def calculate_roc_base_points(
    return_on_capital: Optional[float],
) -> Optional[float]:
    if return_on_capital is None:
        return None

    if return_on_capital >= 30:
        return 25.0
    if return_on_capital >= 20:
        return 22.5
    if return_on_capital >= 15:
        return 20.0
    if return_on_capital >= 10:
        return 16.25
    if return_on_capital >= 5:
        return 11.25
    if return_on_capital >= 0:
        return 6.25

    return 0.0


def calculate_roe_base_points(
    roe: Optional[float],
) -> Optional[float]:
    if roe is None:
        return None

    if roe >= 30:
        return 15.0
    if roe >= 25:
        return 13.5
    if roe >= 20:
        return 12.0
    if roe >= 15:
        return 10.5
    if roe >= 10:
        return 8.0
    if roe >= 7.5:
        return 6.0
    if roe >= 5:
        return 4.0
    if roe >= 0:
        return 2.0

    return 0.0

def calculate_margin_fallback_points(
    net_margin: Optional[float],
    operating_margin: Optional[float],
) -> Optional[float]:
    scores = []

    if net_margin is not None:
        if net_margin >= 25:
            scores.append(5)
        elif net_margin >= 15:
            scores.append(4)
        elif net_margin >= 8:
            scores.append(3)
        elif net_margin >= 3:
            scores.append(2)
        else:
            scores.append(1)

    if operating_margin is not None:
        if operating_margin >= 30:
            scores.append(5)
        elif operating_margin >= 20:
            scores.append(4)
        elif operating_margin >= 10:
            scores.append(3)
        elif operating_margin >= 5:
            scores.append(2)
        else:
            scores.append(1)

    if not scores:
        return None

    average_score = sum(scores) / len(scores)

    return (average_score / 5) * 10

def calculate_profitability_breakdown(
    return_on_capital: Optional[float],
    roe: Optional[float],
    sector: Optional[str],
    industry: Optional[str],
    max_points: int = 40,
    net_margin: Optional[float] = None,
    operating_margin: Optional[float] = None,
    stockholders_equity: Optional[float] = None,
) -> dict:
    benchmarks = get_quality_benchmarks_for_yahoo_industry(
        sector,
        industry,
    )

    roc_benchmark = (
        benchmarks
        .get("mgnroc", {})
        .get("Return_on_Capital")
    )

    roe_benchmark = (
        benchmarks
        .get("roe", {})
        .get("ROE_Unadjusted")
    )

    roc_score = calculate_roc_base_points(
        return_on_capital
    )
    roc_correction = 0.0

    if (
        roc_score is not None
        and return_on_capital is not None
        and roc_benchmark is not None
        and roc_benchmark > 0
    ):
        benchmark_percent = roc_benchmark * 100
        relative = return_on_capital / benchmark_percent

        roc_correction = max(
            -5.0,
            min(5.0, (relative - 1.0) * 5.0),
        )

        roc_score = max(
            0.0,
            min(25.0, roc_score + roc_correction),
        )

    roe_score = calculate_roe_base_points(roe)
    roe_correction = 0.0
    margin_fallback_score = None

    if (
        roe_score is None
        and stockholders_equity is not None
        and stockholders_equity <= 0
    ):
        margin_fallback_score = calculate_margin_fallback_points(
            net_margin,
            operating_margin,
        )

    if (
        roe_score is not None
        and roe is not None
        and roe_benchmark is not None
        and roe_benchmark > 0
    ):
        benchmark_percent = roe_benchmark * 100
        relative = roe / benchmark_percent

        roe_correction = max(
            -3.0,
            min(3.0, (relative - 1.0) * 3.0),
        )

        roe_score = max(
            0.0,
            min(15.0, roe_score + roe_correction),
        )

    available_scores = []

    if roc_score is not None:
        available_scores.append((roc_score, 25.0))

    if roe_score is not None:
        available_scores.append((roe_score, 15.0))

    elif margin_fallback_score is not None:
        available_scores.append((margin_fallback_score, 15.0))

    if available_scores:
        achieved = sum(
            score
            for score, _ in available_scores
        )

        available_max = sum(
            maximum
            for _, maximum in available_scores
        )

        normalized_score = (
            achieved / available_max
        ) * max_points
    else:
        normalized_score = 0.0

    return {
        "score": round(normalized_score),
        "roc_score": roc_score,
        "roc_max": 25.0,
        "roc_benchmark": (
            roc_benchmark * 100
            if roc_benchmark is not None
            else None
        ),
        "roc_correction": roc_correction,
        "roe_score": roe_score,
        "roe_max": 15.0,
        "margin_fallback_score": margin_fallback_score,
        "margin_fallback_used": margin_fallback_score is not None,
        "roe_benchmark": (
            roe_benchmark * 100
            if roe_benchmark is not None
            else None
        ),
        "roe_correction": roe_correction,
    }


def calculate_profitability_score(
    return_on_capital: Optional[float],
    roe: Optional[float],
    sector: Optional[str],
    industry: Optional[str],
    max_points: int,
    net_margin: Optional[float] = None,
    operating_margin: Optional[float] = None,
    stockholders_equity: Optional[float] = None,
) -> int:
    breakdown = calculate_profitability_breakdown(
        return_on_capital,
        roe,
        sector,
        industry,
        max_points,
        net_margin,
        operating_margin,
        stockholders_equity,
    )

    return breakdown["score"]


def calculate_revenue_growth_ratio(
    revenue_growth: Optional[float],
) -> Optional[float]:
    if revenue_growth is None:
        return None

    if revenue_growth >= 25:
        return 1.00
    if revenue_growth >= 15:
        return 0.85
    if revenue_growth >= 10:
        return 0.72
    if revenue_growth >= 6:
        return 0.60
    if revenue_growth >= 3:
        return 0.45
    if revenue_growth >= 0:
        return 0.30
    if revenue_growth >= -3:
        return 0.15
    if revenue_growth >= -8:
        return 0.05

    return 0.00


def calculate_earnings_growth_ratio(
    earnings_growth: Optional[float],
) -> Optional[float]:
    if earnings_growth is None:
        return None

    if earnings_growth >= 25:
        return 1.00
    if earnings_growth >= 15:
        return 0.85
    if earnings_growth >= 10:
        return 0.72
    if earnings_growth >= 5:
        return 0.58
    if earnings_growth >= 0:
        return 0.35
    if earnings_growth >= -5:
        return 0.18
    if earnings_growth >= -15:
        return 0.05

    return 0.00


def calculate_growth_breakdown(
    revenue_growth: Optional[float],
    earnings_growth: Optional[float],
    revenue_growth_median: Optional[float],
    income_growth_median: Optional[float],
    growth_history_reliable: Optional[bool],
    max_points: int = 35,
    positive_revenue_years: Optional[int] = None,
    revenue_growth_annual: Optional[float] = None,
    earnings_growth_annual: Optional[float] = None,
    positive_income_years: Optional[int] = None,
    extreme_revenue_jump: Optional[bool] = None,
    income_sign_change: Optional[bool] = None,
) -> dict:
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

    earnings_ratio = calculate_earnings_growth_ratio(
        earnings_growth
    )

    weighted_scores = []

    if revenue_ratio is not None:
        weighted_scores.append((revenue_ratio, 0.60))

    if earnings_ratio is not None:
        weighted_scores.append((earnings_ratio, 0.40))

    available_weight = sum(
        weight
        for _, weight in weighted_scores
    )

    if available_weight == 0:
        final_score = 0
    else:
        normalized_score = (
            sum(
                score * weight
                for score, weight in weighted_scores
            )
            / available_weight
        )

        final_score = round(
            max_points * normalized_score
        )

    revenue_max = (
        max_points * 0.60 / available_weight
        if revenue_ratio is not None and available_weight > 0
        else None
    )

    earnings_max = (
        max_points * 0.40 / available_weight
        if earnings_ratio is not None and available_weight > 0
        else None
    )

    revenue_points = (
        revenue_ratio * revenue_max
        if revenue_ratio is not None and revenue_max is not None
        else None
    )

    earnings_points = (
        earnings_ratio * earnings_max
        if earnings_ratio is not None and earnings_max is not None
        else None
    )

    return {
        "score": max(0, min(final_score, max_points)),
        "revenue_growth": revenue_growth,
        "revenue_ratio": revenue_ratio,
        "revenue_points": revenue_points,
        "revenue_max": revenue_max,
        "earnings_growth": earnings_growth,
        "earnings_ratio": earnings_ratio,
        "earnings_points": earnings_points,
        "earnings_max": earnings_max,
    }


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
    breakdown = calculate_growth_breakdown(
        revenue_growth,
        earnings_growth,
        revenue_growth_median,
        income_growth_median,
        growth_history_reliable,
        max_points,
        positive_revenue_years,
        revenue_growth_annual,
        earnings_growth_annual,
        positive_income_years,
        extreme_revenue_jump,
        income_sign_change,
    )

    return breakdown["score"]


def calculate_balance_score(
    total_debt: Optional[float],
    total_cash: Optional[float],
    operating_cashflow: Optional[float],
    ebitda: Optional[float],
    interest_coverage: Optional[float],
    max_points: int,
    industry: Optional[str] = None,
) -> int:
    net_debt_to_ebitda = (
        (total_debt - total_cash) / ebitda
        if total_debt is not None
        and total_cash is not None
        and ebitda not in (None, 0)
        else None
    )

    cash_to_debt_ratio = (
        total_cash / total_debt
        if total_cash is not None
        and total_debt not in (None, 0)
        else None
    )

    ocf_to_debt_ratio = (
        operating_cashflow / total_debt
        if operating_cashflow is not None
        and total_debt not in (None, 0)
        else None
    )

    is_auto_manufacturer = industry == "Auto Manufacturers"

    net_debt_weight = 0.15 if is_auto_manufacturer else 0.40
    coverage_weight = 0.55 if is_auto_manufacturer else 0.30
    ocf_weight = 0.15 if is_auto_manufacturer else 0.20
    cash_weight = 0.15 if is_auto_manufacturer else 0.10

    weighted_scores = []

    if net_debt_to_ebitda is not None:
        if net_debt_to_ebitda <= 0:
            net_debt_score = 1.00
        elif net_debt_to_ebitda <= 1:
            net_debt_score = 0.90
        elif net_debt_to_ebitda <= 2:
            net_debt_score = 0.75
        elif net_debt_to_ebitda <= 3:
            net_debt_score = 0.55
        elif net_debt_to_ebitda <= 4:
            net_debt_score = 0.30
        else:
            net_debt_score = 0.00

        weighted_scores.append((net_debt_score, net_debt_weight))

    if interest_coverage is not None:
        if interest_coverage >= 10:
            coverage_score = 1.00
        elif interest_coverage >= 6:
            coverage_score = 0.85
        elif interest_coverage >= 4:
            coverage_score = 0.65
        elif interest_coverage >= 2.5:
            coverage_score = 0.40
        elif interest_coverage >= 1.5:
            coverage_score = 0.20
        else:
            coverage_score = 0.00

        weighted_scores.append((coverage_score, coverage_weight))

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

        weighted_scores.append((ocf_score, ocf_weight))

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

        weighted_scores.append((cash_score, cash_weight))

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

    industry_model = get_industry_model(
        data.get("Sektor", ""),
        data.get("Branche", ""),
        data.get("Ticker", ""),
    )

    balance_score = None

    if industry_model not in {
        "banking",
        "insurance",
        "financial_services",
        "diversified_holding",
    }:
        balance_score = calculate_balance_score(
            data.get("Gesamtverschuldung"),
            data.get("Gesamtliquidität"),
            data.get("Operativer Cashflow"),
            data.get("EBITDA"),
            data.get("Zinsdeckung"),
            balance_weight,
            data.get("Branche"),
        )

    return {
        "Profitabilität": calculate_profitability_score(
            data.get("Kapitalrendite"),
            data.get("Eigenkapitalrendite"),
            data.get("Sektor"),
            data.get("Branche"),
            profit_weight,
            data.get("Nettomarge"),
            data.get("Operative Marge"),
            data.get("Eigenkapital"),
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
        "Bilanz": balance_score,
    }


def calculate_quality_score(data: dict) -> int:
    breakdown = calculate_quality_breakdown(data)

    score_weights = {
        "Profitabilität": QUALITY_WEIGHTS["profitabilitaet"],
        "Wachstum": QUALITY_WEIGHTS["wachstum"],
        "Bilanz": QUALITY_WEIGHTS["bilanz"],
    }

    available_score = 0
    available_max = 0

    for category, score in breakdown.items():
        if score is None:
            continue

        available_score += score
        available_max += score_weights[category]

    if available_max == 0:
        return 0

    normalized_score = (
        available_score / available_max
    ) * 100

    return min(round(normalized_score), 100)