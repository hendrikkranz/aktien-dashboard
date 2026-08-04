from config.scoring import OPPORTUNITY_WEIGHTS


def calculate_opportunity_breakdown(data: dict) -> list:
    breakdown = []

    analyst_upside = data.get("Analystenpotenzial")
    forward_pe = data.get("Forward KGV")
    dividend_yield = data.get("Dividendenrendite")

    analyst_points = 0

    if analyst_upside is not None:
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

    valuation_points = 0

    if forward_pe is not None:
        if forward_pe <= 20:
            valuation_points = OPPORTUNITY_WEIGHTS[
                "bewertung"
            ]
        elif forward_pe <= 22:
            valuation_points = 30
        elif forward_pe <= 25:
            valuation_points = 25
        elif forward_pe <= 30:
            valuation_points = 15

    breakdown.append(
        {
            "Kriterium": "Forward KGV",
            "Punkte": valuation_points,
            "Maximum": OPPORTUNITY_WEIGHTS["bewertung"],
        }
    )

    dividend_points = 0

    if dividend_yield is not None:
        if dividend_yield >= 2:
            dividend_points = OPPORTUNITY_WEIGHTS[
                "dividende"
            ]
        elif dividend_yield >= 1:
            dividend_points = round(
                OPPORTUNITY_WEIGHTS["dividende"] * 0.6
            )
        elif dividend_yield > 0:
            dividend_points = round(
                OPPORTUNITY_WEIGHTS["dividende"] * 0.4
            )

    breakdown.append(
        {
            "Kriterium": "Dividendenrendite",
            "Punkte": dividend_points,
            "Maximum": OPPORTUNITY_WEIGHTS["dividende"],
        }
    )

    return breakdown


def calculate_opportunity_score(data: dict) -> int:
    breakdown = calculate_opportunity_breakdown(data)

    score = sum(
        item["Punkte"]
        for item in breakdown
    )

    return min(score, 100)