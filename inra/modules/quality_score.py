from config.scoring import QUALITY_WEIGHTS


def calculate_quality_score(data: dict) -> int:
    score = 0

    # Profitabilität
    profit_weight = QUALITY_WEIGHTS["profitabilitaet"]

    roe = data.get("Eigenkapitalrendite")

    if roe is not None:
        if roe >= 30:
            score += profit_weight
        elif roe >= 20:
            score += int(profit_weight * 0.8)
        elif roe >= 15:
            score += int(profit_weight * 0.6)
        elif roe >= 10:
            score += int(profit_weight * 0.4)

    # Nettomarge
    margin = data.get("Nettomarge")
    if margin is not None:
        if margin >= 30:
            score += 15
        elif margin >= 20:
            score += 12
        elif margin >= 10:
            score += 8
        elif margin >= 5:
            score += 4

    # Verschuldung
    debt = data.get("Verschuldungsgrad")
    if debt is not None:
        if debt <= 30:
            score += 10
        elif debt <= 60:
            score += 8
        elif debt <= 100:
            score += 5

    # Wachstum
    revenue = data.get("Umsatzwachstum")
    if revenue is not None:
        if revenue >= 20:
            score += 15
        elif revenue >= 10:
            score += 10
        elif revenue >= 5:
            score += 5

    earnings = data.get("Gewinnwachstum")
    if earnings is not None:
        if earnings >= 20:
            score += 15
        elif earnings >= 10:
            score += 10
        elif earnings >= 5:
            score += 5

    # Dividende
    dividend = data.get("Dividendenrendite")
    if dividend is not None:
        if dividend >= 3:
            score += 10
        elif dividend >= 2:
            score += 8
        elif dividend >= 1:
            score += 5

    return min(score, 100)