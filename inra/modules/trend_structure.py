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