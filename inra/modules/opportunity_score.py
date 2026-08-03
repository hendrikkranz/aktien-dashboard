from config.scoring import OPPORTUNITY_WEIGHTS


def calculate_opportunity_score(data: dict) -> int:
    score = 0

    analyst_upside = data.get("Analystenpotenzial")
    forward_pe = data.get("Forward KGV")
    dividend_yield = data.get("Dividendenrendite")

    if analyst_upside is not None:
        if analyst_upside >= 20:
            score += OPPORTUNITY_WEIGHTS["analystenpotenzial"]
        elif analyst_upside >= 10:
            score += round(
                OPPORTUNITY_WEIGHTS["analystenpotenzial"] * 0.625
            )

    if forward_pe is not None:
        if forward_pe <= 20:
            score += OPPORTUNITY_WEIGHTS["bewertung"]
        elif forward_pe <= 25:
            score += round(
                OPPORTUNITY_WEIGHTS["bewertung"] * 0.57
            )

    if dividend_yield is not None:
        if dividend_yield >= 2:
            score += OPPORTUNITY_WEIGHTS["dividende"]
        elif dividend_yield >= 1:
            score += round(
                OPPORTUNITY_WEIGHTS["dividende"] * 0.4
            )

    return min(score, 100)