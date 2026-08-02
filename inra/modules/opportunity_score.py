def calculate_opportunity_score(data: dict) -> int:
    score = 0

    analyst_upside = data.get("Analystenpotenzial")
    forward_pe = data.get("Forward KGV")
    dividend_yield = data.get("Dividendenrendite")

    if analyst_upside is not None:
        if analyst_upside >= 20:
            score += 40
        elif analyst_upside >= 10:
            score += 25

    if forward_pe is not None:
        if forward_pe <= 20:
            score += 30
        elif forward_pe <= 25:
            score += 20

    if dividend_yield is not None:
        if dividend_yield >= 2:
            score += 20
        elif dividend_yield >= 1:
            score += 10

    return score