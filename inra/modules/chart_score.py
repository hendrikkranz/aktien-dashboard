def calculate_chart_breakdown(data: dict) -> list:
    breakdown = []

    momentum_3m = data.get("Momentum 3M")
    momentum_6m = data.get("Momentum 6M")
    rsi = data.get("RSI 14")
    distance_52w = data.get("Abstand 52W Hoch")

    momentum_points = 0
    rsi_points = 0
    distance_52w_points = 0

    if (
        momentum_3m is not None
        and momentum_6m is not None
    ):
        if momentum_3m > 10 and momentum_6m > 10:
            momentum_points = 10
        elif momentum_3m > 5 and momentum_6m > 5:
            momentum_points = 8
        elif momentum_3m > 0 or momentum_6m > 0:
            momentum_points = 5
        elif momentum_3m < -10 and momentum_6m < -10:
            momentum_points = 0
        else:
            momentum_points = 2

    if rsi is not None:
        if 40 <= rsi <= 60:
            rsi_points = 8
        elif 30 <= rsi < 40:
            rsi_points = 6
        elif 60 < rsi <= 70:
            rsi_points = 5
        elif 20 <= rsi < 30:
            rsi_points = 3
        elif 70 < rsi <= 80:
            rsi_points = 2

    if distance_52w is not None:
        if distance_52w >= -5:
            distance_52w_points = 7
        elif distance_52w >= -10:
            distance_52w_points = 6
        elif distance_52w >= -15:
            distance_52w_points = 5
        elif distance_52w >= -20:
            distance_52w_points = 4
        elif distance_52w >= -30:
            distance_52w_points = 2   

    breakdown.append(
        {
            "Kriterium": "Momentum",
            "Punkte": momentum_points,
            "Maximum": 10,
        }
    )

    breakdown.append(
        {
            "Kriterium": "RSI",
            "Punkte": rsi_points,
            "Maximum": 8,
        }
    )

    breakdown.append(
        {
            "Kriterium": "Abstand 52W-Hoch",
            "Punkte": distance_52w_points,
            "Maximum": 7,
        }
    )

    return breakdown


def calculate_chart_score(data: dict) -> int:
    breakdown = calculate_chart_breakdown(data)

    return sum(
        item["Punkte"]
        for item in breakdown
    )