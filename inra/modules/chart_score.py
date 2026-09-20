def calculate_chart_breakdown(data: dict) -> list:
    breakdown = []

    momentum_3m = data.get("Momentum 3M")
    momentum_6m = data.get("Momentum 6M")
    momentum_12m = data.get("Momentum 12M")
    rsi = data.get("RSI 14")
    distance_52w = data.get("Abstand 52W Hoch")
    pressure_balance = data.get("Pressure Balance")

    cm_macd_weekly = data.get("CM MACD Weekly")
    cm_signal_weekly = data.get("CM Signal Weekly")
    cm_histogram_weekly = data.get("CM Histogram Weekly")

    trend_channel_normalized = data.get(
        "Trendkanal Position Normalisiert"
    )

    momentum_points = None
    rsi_points = None
    distance_52w_points = None
    cm_macd_points = None
    trend_channel_points = None
    pressure_balance_points = None

    overheating_points = 0
    overheating_risk = 0

    # ---------------------------------------------------------
    # Überhitzungsgefahr
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Pressure Balance V0.1
    # ---------------------------------------------------------

    if pressure_balance is not None:
        if pressure_balance >= 0.40:
            pressure_balance_points = 6
        elif pressure_balance >= 0.20:
            pressure_balance_points = 5
        elif pressure_balance >= 0.05:
            pressure_balance_points = 4
        elif pressure_balance >= -0.10:
            pressure_balance_points = 3
        elif pressure_balance >= -0.30:
            pressure_balance_points = 2
        elif pressure_balance >= -0.50:
            pressure_balance_points = 1
        else:
            pressure_balance_points = 0

    # ---------------------------------------------------------
    # Trendkanal
    # ---------------------------------------------------------

    long_term_trend_status = data.get(
        "Langfristiger Trend Status"
    )
    long_term_trend = data.get("Langfristiger Trend")

    if (
        trend_channel_normalized is not None
        and long_term_trend_status is not None
        and long_term_trend is not None
    ):
        trend_channel_points = 0

        if (
            long_term_trend_status == "Belastbar"
            and long_term_trend == "Aufwärtstrend"
        ):
            if trend_channel_normalized <= -1.0:
                trend_channel_points = 4
            elif trend_channel_normalized <= -0.5:
                trend_channel_points = 3
            elif trend_channel_normalized < 0.5:
                trend_channel_points = 2
            elif trend_channel_normalized < 1.0:
                trend_channel_points = 1

    # ---------------------------------------------------------
    # Langfristiger Trend
    # ---------------------------------------------------------

    if long_term_trend_status == "Belastbar":
        long_term_trend_points = data.get(
            "Langfristiger Trend Score"
        )
    else:
        long_term_trend_points = None

    # ---------------------------------------------------------
    # Momentum V2
    #
    # 10/10 verlangt Bestätigung durch alle drei Horizonte.
    # Starkes 3M-/6M-Momentum bleibt bei negativem 12M
    # attraktiv, erhält aber nicht mehr automatisch Maximum.
    # ---------------------------------------------------------

    if (
        momentum_3m is not None
        and momentum_6m is not None
    ):
        if (
            momentum_12m is not None
            and momentum_3m > 10
            and momentum_6m > 10
            and momentum_12m > 10
        ):
            momentum_points = 10
        elif (
            momentum_3m > 10
            and momentum_6m > 10
        ):
            momentum_points = 8
        elif (
            momentum_12m is not None
            and momentum_3m > 5
            and momentum_6m > 5
            and momentum_12m >= 0
        ):
            momentum_points = 8
        elif (
            momentum_3m > 0
            or momentum_6m > 0
        ):
            momentum_points = 5
        elif (
            momentum_3m < -10
            and momentum_6m < -10
        ):
            momentum_points = 0
        else:
            momentum_points = 2

    # ---------------------------------------------------------
    # RSI
    # ---------------------------------------------------------

    if rsi is not None:
        rsi_points = 0

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

    # ---------------------------------------------------------
    # Abstand zum 52-Wochen-Hoch
    # ---------------------------------------------------------

    if distance_52w is not None:
        distance_52w_points = 0

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

    # ---------------------------------------------------------
    # CM MACD Refined
    # ---------------------------------------------------------

    if (
        cm_histogram_weekly is not None
        and cm_macd_weekly is not None
        and cm_signal_weekly is not None
        and len(cm_histogram_weekly) >= 5
        and len(cm_macd_weekly) >= 5
        and len(cm_signal_weekly) >= 5
    ):
        cm_macd_points = 0

        if (
            cm_histogram_weekly[-1]
            > cm_histogram_weekly[-2]
        ):
            cm_macd_points += 1

        if (
            cm_histogram_weekly[-1]
            > cm_histogram_weekly[-2]
            > cm_histogram_weekly[-3]
        ):
            cm_macd_points += 2

        positive_weeks = 0

        for value in reversed(cm_histogram_weekly):
            if value > 0:
                positive_weeks += 1
            else:
                break

        if 1 <= positive_weeks <= 3:
            cm_macd_points += 1

        if (
            cm_macd_weekly[-1] > cm_macd_weekly[-2]
            and cm_macd_weekly[-2] > cm_macd_weekly[-3]
        ):
            cm_macd_points += 2

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
            "Maximum": 4,
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
            "Maximum": 7,
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
            "Kriterium": "Pressure Balance",
            "Punkte": pressure_balance_points,
            "Maximum": 6,
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


def calculate_chart_score(data: dict):
    breakdown = calculate_chart_breakdown(data)

    score_items = [
        item
        for item in breakdown
        if item["Kriterium"] != "Überhitzungsgefahr"
    ]

    available_items = [
        item
        for item in score_items
        if item["Punkte"] is not None
    ]

    available_maximum = sum(
        item["Maximum"]
        for item in available_items
    )

    total_maximum = 45

    coverage = (
        available_maximum / total_maximum
        if total_maximum > 0
        else 0
    )

    # Unter 70 % Datenabdeckung derzeit keine Scoreberechnung.
    if coverage < 0.70:
        return 0

    raw_score = sum(
        item["Punkte"]
        for item in available_items
    )

    # Nur tatsächlich fehlende Daten werden bei ausreichender
    # Abdeckung auf die 45-Punkte-Skala hochgerechnet.
    if available_maximum < total_maximum:
        raw_score = (
            raw_score / available_maximum
        ) * total_maximum

    overheating_points = next(
        (
            item["Punkte"]
            for item in breakdown
            if item["Kriterium"]
            == "Überhitzungsgefahr"
        ),
        0,
    )

    if overheating_points is None:
        overheating_points = 0

    final_score = raw_score + overheating_points

    return round(
        max(0, min(45, final_score))
    )

