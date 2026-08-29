from config.scoring import OPPORTUNITY_WEIGHTS
from modules.chart_score import calculate_chart_score


def calculate_opportunity_breakdown(data: dict) -> list:
    breakdown = []

    analyst_upside = data.get("Analystenpotenzial")
    forward_pe = data.get("Forward KGV")

    analyst_points = None

    if analyst_upside is not None:
        analyst_points = 0

        if analyst_upside >= 20:
            analyst_points = OPPORTUNITY_WEIGHTS[
                "analystenpotenzial"
            ]
        elif analyst_upside >= 10:
            analyst_points = round(
                OPPORTUNITY_WEIGHTS["analystenpotenzial"]
                * 0.625
            )

    breakdown.append(
        {
            "Kriterium": "Analystenpotenzial",
            "Punkte": analyst_points,
            "Maximum": OPPORTUNITY_WEIGHTS[
                "analystenpotenzial"
            ],
        }
    )

    valuation_points = None

    if forward_pe is not None:
        if forward_pe <= 0:
            valuation_points = 0
        elif forward_pe <= 20:
            valuation_points = OPPORTUNITY_WEIGHTS[
                "bewertung"
            ]
        elif forward_pe <= 22:
            valuation_points = 17
        elif forward_pe <= 25:
            valuation_points = 14
        elif forward_pe <= 30:
            valuation_points = 8

    breakdown.append(
        {
            "Kriterium": "Forward KGV",
            "Punkte": valuation_points,
            "Maximum": OPPORTUNITY_WEIGHTS["bewertung"],
        }
    )

    return breakdown


def calculate_opportunity_score(data: dict) -> int:
    breakdown = calculate_opportunity_breakdown(data)

    score = sum(
        item["Punkte"]
        for item in breakdown
        if item["Punkte"] is not None
    )

    score += calculate_chart_score(data)

    return min(score, 100)