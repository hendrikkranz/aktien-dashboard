from typing import Optional

import numpy as np
import pandas as pd


def _prepare_prices(history: pd.DataFrame) -> Optional[pd.Series]:
    if history is None or history.empty:
        return None

    if "Close" not in history.columns:
        return None

    prices = history["Close"].dropna()

    if len(prices) < 30:
        return None

    return prices


def _calculate_regression(prices: pd.Series) -> dict:
    y = np.log(prices.to_numpy(dtype=float))
    x = np.arange(len(y), dtype=float)

    slope, intercept = np.polyfit(x, y, 1)

    fitted = intercept + slope * x
    residuals = y - fitted

    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    r_squared = (
        1 - ss_res / ss_tot
        if ss_tot > 0
        else 0.0
    )

    residual_std = float(np.std(residuals))

    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(max(0.0, min(r_squared, 1.0))),
        "residual_std": residual_std,
        "fitted": fitted,
        "residuals": residuals,
    }


def _classify_direction(
    slope: float,
    periods_per_year: int,
) -> str:
    annualized_return = np.exp(
        slope * periods_per_year
    ) - 1

    if annualized_return >= 0.04:
        return "Aufwärtstrend"

    if annualized_return <= -0.04:
        return "Abwärtstrend"

    return "Seitwärts"


def _calculate_channel_position(
    regression: dict,
) -> dict:
    residual_std = regression["residual_std"]

    if residual_std <= 0:
        return {
            "position": "Nicht bestimmbar",
            "normalized_position": None,
        }

    latest_residual = regression["residuals"][-1]

    # -2 = untere Kanalgrenze
    #  0 = Regressionsmittellinie
    # +2 = obere Kanalgrenze
    normalized = latest_residual / residual_std

    if normalized <= -1.6:
        position = "Untere Unterstützungszone"
    elif normalized <= -0.5:
        position = "Untere Kanalhälfte"
    elif normalized < 0.5:
        position = "Mittellinie"
    elif normalized < 1.6:
        position = "Obere Kanalhälfte"
    else:
        position = "Obere Widerstandszone"

    return {
        "position": position,
        "normalized_position": float(normalized),
    }


def _calculate_channel_position_history(
    regression: dict,
    lookback_periods: int = 20,
) -> list[float]:
    """Historie der normalisierten Position im aktuellen Trendkanal.

    0 = Regressionsmittellinie
    -2 = untere Kanalgrenze
    +2 = obere Kanalgrenze
    """
    residual_std = regression["residual_std"]

    if residual_std <= 0:
        return []

    residuals = regression["residuals"]

    normalized = (
        residuals / residual_std
    )

    recent = normalized[
        -min(lookback_periods, len(normalized)):
    ]

    return [
        float(value)
        for value in recent
    ]

def _calculate_market_respect(
    regression: dict,
) -> dict:
    residuals = regression["residuals"]
    residual_std = regression["residual_std"]

    if residual_std <= 0:
        return {
            "lower_tests": 0,
            "upper_tests": 0,
            "midline_tests": 0,
        }

    normalized = residuals / residual_std

    def count_episodes(mask: np.ndarray) -> int:
        count = 0
        in_episode = False

        for active in mask:
            if active and not in_episode:
                count += 1
                in_episode = True
            elif not active:
                in_episode = False

        return count

    lower_mask = (
        (normalized >= -2.2)
        & (normalized <= -1.3)
    )

    upper_mask = (
        (normalized >= 1.3)
        & (normalized <= 2.2)
    )

    midline_mask = (
        np.abs(normalized) <= 0.25
    )

    return {
        "lower_tests": count_episodes(lower_mask),
        "upper_tests": count_episodes(upper_mask),
        "midline_tests": count_episodes(midline_mask),
    }


def _confidence_label(score: float) -> str:
    if score >= 0.80:
        return "Sehr hoch"

    if score >= 0.65:
        return "Hoch"

    if score >= 0.50:
        return "Mittel"

    return "Niedrig"


def analyze_trend_structure(
    history: pd.DataFrame,
    periods_per_year: int = 52,
) -> dict:
    prices = _prepare_prices(history)

    if prices is None:
        return {
            "status": "Nicht bewertbar",
            "direction": None,
            "position": None,
            "normalized_position": None,
            "confidence": "Niedrig",
            "confidence_raw": None,
            "r_squared": None,
            "lower_tests": None,
            "upper_tests": None,
            "midline_tests": None,
        }

    regression = _calculate_regression(prices)

    direction = _classify_direction(
        regression["slope"],
        periods_per_year,
    )

    position_result = _calculate_channel_position(
        regression
    )

    respect = _calculate_market_respect(
        regression
    )

    channel_position_history = (
        _calculate_channel_position_history(
            regression,
            lookback_periods=20,
        )
    )

    touch_score = min(
        (
            respect["lower_tests"]
            + respect["upper_tests"]
        ) / 10,
        1.0,
    )

    confidence_score = (
        regression["r_squared"] * 0.50
        + touch_score * 0.30
        + 0.20
    )

    confidence_score = max(
        0.0,
        min(confidence_score, 1.0),
    )

    confidence = _confidence_label(
        confidence_score
    )

    if confidence == "Niedrig":
        status = "Nicht belastbar"
    else:
        status = "Belastbar"

    return {
        "status": status,
        "direction": direction,
        "position": position_result["position"],
        "normalized_position": position_result["normalized_position"],
        "confidence": confidence,
        "confidence_raw": confidence_score,
        "r_squared": regression["r_squared"],
        "lower_tests": respect["lower_tests"],
        "upper_tests": respect["upper_tests"],
        "midline_tests": respect["midline_tests"],
        "channel_position_history": channel_position_history,
    }

def analyze_entry_confirmation(
    pressure_balance=None,
    cm_macd_weekly=None,
    cm_signal_weekly=None,
    cm_histogram_weekly=None,
) -> dict:
    """Diagnostiziert die kurzfristige Bestätigung eines Entry-Setups.

    Reine Diagnose: kein Einfluss auf Score oder Setup-Klassifikation.
    """
    signals = {
        "pressure": None,
        "macd_direction": None,
        "histogram_direction": None,
        "macd_above_signal": None,
    }

    # Kurzfristiger Kauf-/Verkaufsdruck.
    if pressure_balance is not None:
        if pressure_balance > 0.05:
            signals["pressure"] = "positiv"
        elif pressure_balance < -0.10:
            signals["pressure"] = "negativ"
        else:
            signals["pressure"] = "neutral"

    # MACD-Dynamik: steigt oder fällt der MACD aktuell?
    if (
        cm_macd_weekly is not None
        and len(cm_macd_weekly) >= 2
    ):
        if cm_macd_weekly[-1] > cm_macd_weekly[-2]:
            signals["macd_direction"] = "positiv"
        elif cm_macd_weekly[-1] < cm_macd_weekly[-2]:
            signals["macd_direction"] = "negativ"
        else:
            signals["macd_direction"] = "neutral"

    # Histogramm-Dynamik: verbessert oder verschlechtert
    # sich der Abstand zwischen MACD und Signallinie?
    if (
        cm_histogram_weekly is not None
        and len(cm_histogram_weekly) >= 2
    ):
        if (
            cm_histogram_weekly[-1]
            > cm_histogram_weekly[-2]
        ):
            signals["histogram_direction"] = "positiv"
        elif (
            cm_histogram_weekly[-1]
            < cm_histogram_weekly[-2]
        ):
            signals["histogram_direction"] = "negativ"
        else:
            signals["histogram_direction"] = "neutral"

    # MACD relativ zur Signallinie ist ein Zustand,
    # keine eigenständige Trendwende-Bestätigung.
    if (
        cm_macd_weekly is not None
        and cm_signal_weekly is not None
        and len(cm_macd_weekly) >= 1
        and len(cm_signal_weekly) >= 1
    ):
        signals["macd_above_signal"] = (
            cm_macd_weekly[-1]
            > cm_signal_weekly[-1]
        )

    directional = [
        signals["pressure"],
        signals["macd_direction"],
        signals["histogram_direction"],
    ]

    available = [
        value
        for value in directional
        if value is not None
    ]

    positive = available.count("positiv")
    negative = available.count("negativ")

    if len(available) < 2:
        confirmation = "Nicht bewertbar"
    elif positive >= 2 and negative == 0:
        confirmation = "Positiv"
    elif negative >= 2 and positive == 0:
        confirmation = "Negativ"
    else:
        confirmation = "Gemischt"

    return {
        "confirmation": confirmation,
        "positive_signals": positive,
        "negative_signals": negative,
        **signals,
    }



def analyze_30w_support_reclaim(
    weekly_close_prices,
) -> dict:
    """Diagnostiziert einen Test der 30-Wochen-Linie.

    Reine Diagnose: kein Einfluss auf Score oder Entry Setup.
    Ein positives Signal setzt voraus, dass die 30W-Linie bereits
    beim Test gestiegen ist.
    """
    import pandas as pd

    result = {
        "signal": "Nicht bewertbar",
        "test_weeks_ago": None,
        "test_distance_pct": None,
        "sma30_slope_at_test_pct": None,
        "current_distance_pct": None,
        "move_since_test_pct": None,
    }

    if weekly_close_prices is None:
        return result

    close = pd.Series(weekly_close_prices).copy()
    close = pd.to_numeric(close, errors="coerce").dropna()

    if len(close) < 40:
        return result

    sma30 = close.rolling(30).mean()

    df = pd.DataFrame({
        "close": close,
        "sma30": sma30,
    }).dropna()

    if len(df) < 11:
        return result

    df["distance"] = (
        df["close"] / df["sma30"] - 1
    ) * 100

    df["slope5"] = (
        df["sma30"] / df["sma30"].shift(5) - 1
    ) * 100

    # Nur jüngere Tests sind für das heutige Entry Setup relevant.
    recent = df.tail(13)

    candidates = []

    for pos in range(1, len(recent)):
        current = recent.iloc[pos]
        previous = recent.iloc[pos - 1]

        # Die Linie muss bereits beim Test steigen.
        if (
            pd.isna(current["slope5"])
            or current["slope5"] <= 0
        ):
            continue

        # Tatsächliche Annäherung von oben:
        # vorher oberhalb, danach nahe an/leicht unter der 30W-Linie.
        approached_from_above = (
            previous["distance"] > 3
            and -5 <= current["distance"] <= 3
        )

        if approached_from_above:
            candidates.append(recent.index[pos])

    if not candidates:
        result["signal"] = "Kein positives 30W-Signal"
        result["current_distance_pct"] = round(
            float(df["distance"].iloc[-1]),
            2,
        )
        return result

    test_idx = candidates[-1]
    test_pos = df.index.get_loc(test_idx)
    test = df.loc[test_idx]
    current = df.iloc[-1]

    weeks_ago = len(df) - 1 - test_pos

    move_since = (
        current["close"] / test["close"] - 1
    ) * 100

    current_distance = current["distance"]

    # Test in der laufenden Woche: noch keine Bestätigung möglich.
    if weeks_ago == 0:
        signal = "30W Test läuft"

    # Unterhalb getestet und anschließend zurück über die Linie.
    elif (
        test["distance"] < 0
        and current_distance > 3
        and move_since > 0
    ):
        signal = "30W Reclaim"

    # Linie beim Test gehalten und anschließend klar wegbewegt.
    elif (
        test["distance"] >= 0
        and current_distance > 3
        and move_since > 0
    ):
        signal = "30W Support Bounce"

    # Noch in unmittelbarer Nähe der steigenden Linie.
    elif -3 <= current_distance <= 3:
        signal = "30W Test läuft"

    else:
        signal = "Kein positives 30W-Signal"

    return {
        "signal": signal,
        "test_weeks_ago": weeks_ago,
        "test_distance_pct": round(
            float(test["distance"]),
            2,
        ),
        "sma30_slope_at_test_pct": round(
            float(test["slope5"]),
            2,
        ),
        "current_distance_pct": round(
            float(current_distance),
            2,
        ),
        "move_since_test_pct": round(
            float(move_since),
            2,
        ),
    }


def classify_entry_setup(
    trend: dict,
    confirmation=None,
    positive_signals=0,
    negative_signals=0,
    pullback_pct=None,
    recovery_pct=None,
    distance_to_previous_52w_high_pct=None,
    support_30w_signal=None,
) -> dict:
    """Klassifiziert das aktuelle technische Entry-Setup.

    V1 kombiniert:
    - belastbare langfristige Trendstruktur,
    - Position und Reaktion im Trendkanal,
    - laufenden Pullback und dessen Recovery,
    - kurzfristige technische Bestätigung,
    - Lage zum vorherigen 52W-Hoch.

    Reine Diagnose: noch kein Einfluss auf einen Score.
    """
    result = {
        "setup": "Nicht bewertbar",
        "detail": None,
    }

    trend_status = trend.get("status")
    trend_direction = trend.get("direction")

    # Echter Datenmangel: keine Trendstruktur berechenbar.
    # Dieser Fall darf später neutral behandelt werden.
    if (
        trend_status == "Nicht bewertbar"
        or trend_direction is None
    ):
        result["detail"] = (
            "Zu wenig Daten für eine belastbare "
            "Entry-Klassifikation"
        )
        return result

    # Eine Trendrichtung ist berechenbar, die Struktur erfüllt
    # aber nicht die Mindestanforderungen an die Belastbarkeit.
    # Das ist kein Datenmangel und daher kein neutraler Entry-Fall.
    if trend_status != "Belastbar":
        return {
            "setup": "Kein belastbares Entry Setup",
            "detail": (
                "Trendrichtung ist berechenbar, die langfristige "
                "Trendstruktur ist jedoch nicht belastbar"
            ),
        }

    # Belastbarer Seitwärts- oder Abwärtstrend:
    # kein klassisches Pullback-/Support-Entry im Aufwärtstrend.
    if trend_direction == "Seitwärtstrend":
        return {
            "setup": "Seitwärtstrend – kein Entry Setup",
            "detail": (
                "Belastbarer Seitwärtstrend ohne strukturellen "
                "Aufwärtstrend für ein bevorzugtes Entry Setup"
            ),
        }

    if trend_direction == "Abwärtstrend":
        return {
            "setup": "Abwärtstrend – kein Entry Setup",
            "detail": (
                "Belastbarer Abwärtstrend; ein günstiger "
                "Kanalstand allein ist kein Kaufsignal"
            ),
        }

    if trend_direction != "Aufwärtstrend":
        return result

    history = trend.get(
        "channel_position_history"
    ) or []

    if len(history) < 6:
        result["detail"] = (
            "Zu wenig Kanalhistorie für Entry-Klassifikation"
        )
        return result

    recent = history[-8:]
    current = recent[-1]
    previous = recent[:-1]

    recent_min = min(previous)
    recent_max = max(previous)

    # Sehr tiefe laufende Pullbacks sind kein klassisches
    # Pullback-Entry-Setup. Sie verlangen zunächst Stabilisierung.
    deep_pullback = (
        pullback_pct is not None
        and pullback_pct <= -30.0
    )

    healthy_pullback = (
        pullback_pct is not None
        and -25.0 <= pullback_pct <= -5.0
    )

    recovery_established = (
        recovery_pct is not None
        and recovery_pct >= 40.0
    )

    # Eine gemischte Gesamtbestätigung kann trotzdem
    # konstruktiv sein, wenn mindestens zwei der drei
    # Richtungssignale positiv und höchstens eines negativ ist.
    constructive_confirmation = (
        confirmation == "Positiv"
        or (
            confirmation == "Gemischt"
            and positive_signals >= 2
            and negative_signals <= 1
        )
    )

    # 1. Bruch der unteren Trendkanal-Unterstützung.
    # Hat Vorrang vor kurzfristig positiven Einzelsignalen.
    if (
        current <= -2.20
        and min(recent[-3:]) <= -2.20
    ):
        return {
            "setup": "Support Breakdown",
            "detail": (
                "Kurs liegt deutlich unter der unteren "
                "Trendkanalgrenze; kurzfristige Signale "
                "heben den strukturellen Bruch nicht auf"
            ),
        }

    # 2. Untere Kanalzone mit erkennbarer Aufwärtsreaktion.
    lower_channel_bounce = (
        recent_min <= -1.60
        and current >= recent_min + 0.50
        and current > -1.60
    )

    if lower_channel_bounce:
        if (
            healthy_pullback
            and recovery_established
            and constructive_confirmation
        ):
            return {
                "setup": "Lower Channel Bounce – bestätigt",
                "detail": (
                    "Erholung aus der unteren Kanalzone nach "
                    "gesundem Pullback mit positiver "
                    "kurzfristiger Bestätigung"
                ),
            }

        if deep_pullback:
            return {
                "setup": "Lower Channel Recovery – vorsichtig",
                "detail": (
                    "Erholung aus der unteren Kanalzone, "
                    "aber nach sehr tiefem Pullback"
                ),
            }

        return {
            "setup": "Lower Channel Bounce",
            "detail": (
                "Erholung aus der unteren "
                "Trendkanal-Unterstützungszone; "
                "Bestätigung noch nicht vollständig"
            ),
        }

    # 3. Rückeroberung der Medianlinie.
    median_reclaim = (
        recent_min <= -0.40
        and max(recent[-5:]) >= 0.0
        and current >= -0.20
    )

    if median_reclaim:
        if constructive_confirmation:
            if deep_pullback:
                return {
                    "setup": "Median Reclaim – vorsichtig",
                    "detail": (
                        "Mittellinie positiv zurückerobert, "
                        "aber nach sehr tiefem Pullback"
                    ),
                }

            return {
                "setup": "Median Reclaim – bestätigt",
                "detail": (
                    "Mittellinie nach vorheriger Schwäche "
                    "mit positiver kurzfristiger "
                    "Bestätigung zurückerobert"
                ),
            }

        if confirmation == "Negativ":
            return {
                "setup": "Median Reclaim – schwach",
                "detail": (
                    "Mittellinie zurückerobert, aber "
                    "kurzfristige Signale bestätigen "
                    "die Bewegung derzeit nicht"
                ),
            }

        return {
            "setup": "Median Reclaim",
            "detail": (
                "Mittellinie nach vorheriger Schwäche "
                "zurückerobert; Bestätigung ist gemischt"
            ),
        }

    # 4. Test der Medianlinie von oben.
    median_test = (
        recent_max >= 0.35
        and -0.15 <= current <= 0.25
        and min(recent[-3:]) >= -0.15
    )

    if median_test:
        if confirmation == "Positiv":
            return {
                "setup": "Median Support – bestätigt",
                "detail": (
                    "Mittellinie wird von oben getestet "
                    "und die kurzfristigen Signale "
                    "bestätigen eine positive Reaktion"
                ),
            }

        if confirmation == "Negativ":
            return {
                "setup": "Median Test – schwach",
                "detail": (
                    "Kurs testet die Mittellinie von oben, "
                    "aber die kurzfristigen Signale sind "
                    "derzeit negativ"
                ),
            }

        return {
            "setup": "Median Test – unbestätigt",
            "detail": (
                "Kurs testet die Mittellinie aus einem "
                "bestehenden Aufwärtstrend; eine positive "
                "Reaktion ist noch nicht bestätigt"
            ),
        }

    # 5. Untere Kanalhälfte ohne strukturell erkannten Bounce.
    if -1.60 < current <= -0.50:
        if (
            healthy_pullback
            and recovery_established
            and constructive_confirmation
        ):
            return {
                "setup": "Pullback Recovery – bestätigt",
                "detail": (
                    "Gesunder Pullback in der unteren "
                    "Kanalhälfte mit deutlicher Erholung "
                    "und positiver Bestätigung"
                ),
            }

        if deep_pullback:
            return {
                "setup": "Tiefe Korrektur – Stabilisierung abwarten",
                "detail": (
                    "Kurs liegt günstig im Trendkanal, "
                    "der laufende Pullback ist jedoch "
                    "außergewöhnlich tief"
                ),
            }

        if confirmation == "Negativ":
            return {
                "setup": "Untere Kanalhälfte – schwach",
                "detail": (
                    "Günstigere Kanalposition, aber "
                    "negative kurzfristige Bestätigung"
                ),
            }

        if (
            constructive_confirmation
            and support_30w_signal in {
                "30W Reclaim",
                "30W Support Bounce",
            }
        ):
            return {
                "setup": "30W Support/Reclaim – bestätigt",
                "detail": (
                    "Günstigere Position im langfristigen "
                    "Aufwärtstrend mit bestätigter Reaktion "
                    "an der bereits steigenden 30-Wochen-Linie"
                ),
            }

        return {
            "setup": "Untere Kanalhälfte – unbestätigt",
            "detail": (
                "Günstigere Kanalposition, aber noch "
                "kein ausreichend bestätigter Einstieg"
            ),
        }

    # 6. Obere Kanalzone.
    # Sie ist nicht automatisch negativ: zunächst unterscheiden,
    # ob gleichzeitig das vorherige 52W-Hoch angegriffen oder
    # bereits überschritten wird.
    if current >= 1.60:
        near_previous_high = (
            distance_to_previous_52w_high_pct is not None
            and -5.0
            <= distance_to_previous_52w_high_pct
            <= 0.0
        )

        breakout = (
            distance_to_previous_52w_high_pct is not None
            and distance_to_previous_52w_high_pct > 0.0
        )

        if breakout:
            if confirmation == "Positiv":
                return {
                    "setup": "Breakout – bestätigt",
                    "detail": (
                        "Kurs liegt über dem vorherigen "
                        "52W-Hoch und der Ausbruch wird "
                        "kurzfristig positiv bestätigt"
                    ),
                }

            if confirmation == "Negativ":
                return {
                    "setup": "Breakout – fragil",
                    "detail": (
                        "Kurs liegt über dem vorherigen "
                        "52W-Hoch, die kurzfristige "
                        "Bestätigung ist jedoch negativ"
                    ),
                }

            return {
                "setup": "Breakout – unbestätigt",
                "detail": (
                    "Kurs liegt über dem vorherigen "
                    "52W-Hoch; die kurzfristige "
                    "Bestätigung ist noch gemischt"
                ),
            }

        if near_previous_high:
            if confirmation == "Positiv":
                return {
                    "setup": "Widerstands-Anlauf – positiv",
                    "detail": (
                        "Kurs nähert sich in der oberen "
                        "Kanalzone dem vorherigen 52W-Hoch "
                        "mit positiver Dynamik"
                    ),
                }

            if confirmation == "Negativ":
                return {
                    "setup": "Widerstands-Anlauf – schwach",
                    "detail": (
                        "Kurs nähert sich in der oberen "
                        "Kanalzone dem vorherigen 52W-Hoch, "
                        "aber die kurzfristigen Signale "
                        "sind negativ"
                    ),
                }

            return {
                "setup": "Widerstands-Anlauf – unbestätigt",
                "detail": (
                    "Kurs nähert sich in der oberen "
                    "Kanalzone dem vorherigen 52W-Hoch"
                ),
            }

        return {
            "setup": "Obere Kanalzone",
            "detail": (
                "Kurs liegt relativ zum langfristigen "
                "Trend weit oben, ohne unmittelbaren "
                "52W-Breakout"
            ),
        }

    return {
        "setup": "Neutral",
        "detail": (
            "Kein ausgeprägtes Entry-Signal im Trendkanal"
        ),
    }

def calculate_long_term_trend_score(
    trend: dict,
) -> tuple[int, str]:

    if trend["status"] != "Belastbar":
        return (
            0,
            "Trendstruktur derzeit nicht belastbar",
        )

    if trend["direction"] == "Aufwärtstrend":
        return (
            3,
            "Belastbarer langfristiger Aufwärtstrend",
        )

    if trend["direction"] == "Abwärtstrend":
        return (
            -3,
            "Belastbarer langfristiger Abwärtstrend",
        )

    return (
        1,
        "Belastbare Seitwärtsstruktur",
    )