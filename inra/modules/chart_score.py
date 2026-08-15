def calculate_chart_breakdown(data: dict) -> list:
    breakdown = []

    momentum_3m = data.get("Momentum 3M")
    momentum_6m = data.get("Momentum 6M")
    rsi = data.get("RSI 14")
    distance_52w = data.get("Abstand 52W Hoch")
    momentum_12m = data.get("Momentum 12M")
    cm_macd_weekly = data.get("CM MACD Weekly")
    cm_signal_weekly = data.get("CM Signal Weekly")
    cm_histogram_weekly = data.get("CM Histogram Weekly")

    momentum_points = 0
    rsi_points = 0
    distance_52w_points = 0
    cm_macd_points = 0
    trend_channel_points = 0
    overheating_points = 0
    overheating_risk = 0
    prime_entry_points = 0

    if rsi is not None:
        if rsi >= 80:
            overheating_risk += 3
        elif rsi >= 70:
            overheating_risk += 2
        elif rsi >= 60:
            overheating_risk += 1

    if distance_52w is not None:
        if distance_52w >= -3:
            overheating_risk += 2
        elif distance_52w >= -8:
            overheating_risk += 1

    if (
        momentum_3m is not None
        and momentum_6m is not None
        and momentum_12m is not None
    ):
        if (
            momentum_3m >= 25
            and momentum_6m >= 35
            and momentum_12m >= 50
        ):
            overheating_risk += 3
        elif (
            momentum_3m >= 15
            and momentum_6m >= 25
        ):
            overheating_risk += 2
        elif momentum_3m >= 10:
            overheating_risk += 1

    if overheating_risk >= 7:
        overheating_points = -8
    elif overheating_risk >= 5:
        overheating_points = -4
    elif overheating_risk >= 3:
        overheating_points = -2
    else:
        overheating_points = 0

    if (
        rsi is not None
        and distance_52w is not None
        and momentum_3m is not None
    ):
        if (
            45 <= rsi <= 60
            and -15 <= distance_52w <= -5
            and momentum_3m > 0
        ):
            prime_entry_points = 4
        elif (
            40 <= rsi <= 65
            and -20 <= distance_52w <= -3
        ):
            prime_entry_points = 2

    long_term_trend_points = data.get(
    "Langfristiger Trend Score",
    0,
    )

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

            # CM MACD Refined
    if (
        cm_histogram_weekly is not None
        and cm_macd_weekly is not None
        and cm_signal_weekly is not None
        and len(cm_histogram_weekly) >= 5
        and len(cm_macd_weekly) >= 5
        and len(cm_signal_weekly) >= 5
    ):
        # 1. Histogramm steigt
        if (
            cm_histogram_weekly[-1]
            > cm_histogram_weekly[-2]
        ):
            cm_macd_points += 1

        # 2. Histogramm beschleunigt sich
        if (
            cm_histogram_weekly[-1]
            > cm_histogram_weekly[-2]
            > cm_histogram_weekly[-3]
        ):
            cm_macd_points += 1

        # 3. Histogramm erst seit max. 3 Wochen positiv
        positive_weeks = 0

        for value in reversed(cm_histogram_weekly):
            if value > 0:
                positive_weeks += 1
            else:
                break

        if 1 <= positive_weeks <= 3:
            cm_macd_points += 1

        # 4. MACD steigt seit mindestens 3 Wochen
        if (
            cm_macd_weekly[-1] > cm_macd_weekly[-2]
            and cm_macd_weekly[-2] > cm_macd_weekly[-3]
        ):
            cm_macd_points += 1

        # 5. MACD erst seit max. 3 Wochen über Signallinie
        crossover_weeks = 0

        for macd_value, signal_value in reversed(
            list(zip(cm_macd_weekly, cm_signal_weekly))
        ):
            if macd_value > signal_value:
                crossover_weeks += 1
            else:
                break

        if 1 <= crossover_weeks <= 3:
            cm_macd_points += 1

    breakdown.append(
        {
            "Kriterium": "Trendkanal",
            "Punkte": trend_channel_points,
            "Maximum": 8,
        }
    )

    breakdown.append(
        {
            "Kriterium": "Langfristiger Trend",
            "Punkte": long_term_trend_points,
            "Maximum": 3,
        }
    )

    breakdown.append(
        {
            "Kriterium": "CM MACD Refined",
            "Punkte": cm_macd_points,
            "Maximum": 5,
        }
    )

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

    breakdown.append(
        {
            "Kriterium": "Prime Entry",
            "Punkte": prime_entry_points,
            "Maximum": 4,
        }
    )

    breakdown.append(
        {
            "Kriterium": "Überhitzungsgefahr",
            "Punkte": overheating_points,
            "Maximum": 0,
        }
    )

    return breakdown


def calculate_chart_score(data: dict) -> int:
    breakdown = calculate_chart_breakdown(data)

    return sum(
        item["Punkte"]
        for item in breakdown
    )