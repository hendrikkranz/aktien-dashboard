from config.scoring import QUALITY_WEIGHTS


def calculate_quality_score(data: dict) -> int:
    score = 0

    profit_weight = QUALITY_WEIGHTS["profitabilitaet"]
    growth_weight = QUALITY_WEIGHTS["wachstum"]
    balance_weight = QUALITY_WEIGHTS["bilanz"]
    dividend_weight = QUALITY_WEIGHTS["dividende"]

    # Profitabilität
    roe = data.get("Eigenkapitalrendite")

    if roe is not None:
        if roe >= 30:
            score += profit_weight
        elif roe >= 20:
            score += round(profit_weight * 0.8)
        elif roe >= 15:
            score += round(profit_weight * 0.6)
        elif roe >= 10:
            score += round(profit_weight * 0.4)

    # Wachstum
    growth_score = 0

    revenue = data.get("Umsatzwachstum")
    if revenue is not None:
        if revenue >= 20:
            growth_score += growth_weight / 2
        elif revenue >= 10:
            growth_score += growth_weight * 0.35
        elif revenue >= 5:
            growth_score += growth_weight * 0.2

    earnings = data.get("Gewinnwachstum")
    if earnings is not None:
        if earnings >= 20:
            growth_score += growth_weight / 2
        elif earnings >= 10:
            growth_score += growth_weight * 0.35
        elif earnings >= 5:
            growth_score += growth_weight * 0.2

    score += round(growth_score)

    # Bilanz
    debt = data.get("Verschuldungsgrad")

    if debt is not None:
        if debt <= 30:
            score += balance_weight
        elif debt <= 60:
            score += round(balance_weight * 0.8)
        elif debt <= 100:
            score += round(balance_weight * 0.5)

    # Dividende
    dividend = data.get("Dividendenrendite")

    if dividend is not None:
        if dividend >= 3:
            score += dividend_weight
        elif dividend >= 2:
            score += round(dividend_weight * 0.8)
        elif dividend >= 1:
            score += round(dividend_weight * 0.5)

    return min(score, 100)