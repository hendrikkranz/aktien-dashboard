from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

from modules.opportunity_score import (
    calculate_opportunity_breakdown,
    calculate_opportunity_score,
)
from modules.quality_score import (
    calculate_quality_breakdown,
    calculate_quality_score,
)
from modules.trend_structure import (
    analyze_trend_structure,
    calculate_long_term_trend_score,
)

MANUAL_OVERRIDES_PATH = Path(__file__).resolve().parents[1] / "data" / "manual_overrides.csv"

def _load_manual_overrides() -> pd.DataFrame:
    if not MANUAL_OVERRIDES_PATH.exists():
        return pd.DataFrame(
            columns=["Ticker", "Feld", "Wert", "Stand", "Quelle"]
        )

    return pd.read_csv(MANUAL_OVERRIDES_PATH)

def _get_manual_override(
    ticker: str,
    field: str,
) -> Optional[float]:
    overrides = _load_manual_overrides()

    match = overrides[
        (overrides["Ticker"] == ticker)
        & (overrides["Feld"] == field)
    ]

    if match.empty:
        return None

    value = match.iloc[0]["Wert"]

    if pd.isna(value):
        return None

    return float(value)

def _get_manual_override_metadata(
    ticker: str,
    field: str,
) -> dict:
    overrides = _load_manual_overrides()

    match = overrides[
        (overrides["Ticker"] == ticker)
        & (overrides["Feld"] == field)
    ]

    if match.empty:
        return {}

    row = match.iloc[0]

    return {
        "Stand": row.get("Stand"),
        "Quelle": row.get("Quelle"),
    }

def save_manual_override(
    ticker: str,
    field: str,
    value: float,
    date: str,
    source: str,
) -> None:
    overrides = _load_manual_overrides()

    new_row = pd.DataFrame(
        [
            {
                "Ticker": ticker,
                "Feld": field,
                "Wert": value,
                "Stand": date,
                "Quelle": source,
            }
        ]
    )

    overrides = overrides[
        ~(
            (overrides["Ticker"] == ticker)
            & (overrides["Feld"] == field)
        )
    ]

    overrides = pd.concat(
        [overrides, new_row],
        ignore_index=True,
    )

    overrides.to_csv(
        MANUAL_OVERRIDES_PATH,
        index=False,
    )

def _calculate_period_return(
    close_prices: pd.Series,
    trading_days: int,
) -> Optional[float]:
    clean_prices = close_prices.dropna()

    if len(clean_prices) <= trading_days:
        return None

    start_price = clean_prices.iloc[-trading_days - 1]
    end_price = clean_prices.iloc[-1]

    if start_price is None or start_price == 0:
        return None

    return ((end_price / start_price) - 1) * 100


def load_momentum_metrics(ticker: str) -> dict:
    empty_result = {
        "Momentum 3M": None,
        "Momentum 6M": None,
        "Momentum 12M": None,
        "RSI 14": None,
        "CM MACD": None,
        "CM Signal": None,
        "CM Histogram": None,
        "CM MACD Weekly": None,
        "CM Signal Weekly": None,
        "CM Histogram Weekly": None,
    }

    try:
        history = yf.Ticker(ticker).history(
            period="5y",
            auto_adjust=True,
        )
    except Exception:
        return empty_result

    if history.empty or "Close" not in history.columns:
        return empty_result

    close_prices = history["Close"].dropna()
    weekly_close_prices = (
        close_prices
        .resample("W-FRI")
        .last()
        .dropna()
    )    

    if close_prices.empty:
        return empty_result

    rsi_14 = None
    cm_macd = None
    cm_signal = None
    cm_histogram = None
    cm_macd_weekly = None
    cm_signal_weekly = None
    cm_histogram_weekly = None    

    if len(close_prices) >= 15:
        price_changes = close_prices.diff()

        gains = price_changes.clip(lower=0)
        losses = -price_changes.clip(upper=0)

        average_gain = gains.ewm(
            alpha=1 / 14,
            adjust=False,
            min_periods=14,
        ).mean()

        average_loss = losses.ewm(
            alpha=1 / 14,
            adjust=False,
            min_periods=14,
        ).mean()

        current_gain = average_gain.iloc[-1]
        current_loss = average_loss.iloc[-1]

        if current_loss == 0:
            rsi_14 = 100.0
        elif current_gain == 0:
            rsi_14 = 0.0
        else:
            relative_strength = (
                current_gain / current_loss
            )

            rsi_14 = 100 - (
                100 / (1 + relative_strength)
            )

    if len(close_prices) >= 35:
        ema_12 = close_prices.ewm(
            span=12,
            adjust=False,
        ).mean()

        ema_26 = close_prices.ewm(
            span=26,
            adjust=False,
        ).mean()

        macd_line = ema_12 - ema_26

        signal_line = macd_line.ewm(
            span=9,
            adjust=False,
        ).mean()

        histogram = macd_line - signal_line

        cm_macd = macd_line.iloc[-1]
        cm_signal = signal_line.iloc[-1]
        cm_histogram = histogram.iloc[-1]

    if len(weekly_close_prices) >= 35:
        weekly_ema_12 = weekly_close_prices.ewm(
            span=12,
            adjust=False,
        ).mean()

        weekly_ema_26 = weekly_close_prices.ewm(
            span=26,
            adjust=False,
        ).mean()

        weekly_macd_line = (
            weekly_ema_12 - weekly_ema_26
        )

        weekly_signal_line = weekly_macd_line.ewm(
            span=9,
            adjust=False,
        ).mean()

        weekly_histogram = (
            weekly_macd_line - weekly_signal_line
        )

        cm_macd_weekly = weekly_macd_line
        cm_signal_weekly = weekly_signal_line
        cm_histogram_weekly = weekly_histogram        

    return {
        "Momentum 3M": _calculate_period_return(
            close_prices,
            63,
        ),
        "Momentum 6M": _calculate_period_return(
            close_prices,
            126,
        ),
        "Momentum 12M": _calculate_period_return(
            close_prices,
            251,
        ),
        "RSI 14": rsi_14,
        "CM MACD": cm_macd,
        "CM Signal": cm_signal,
        "CM Histogram": cm_histogram,
        "CM MACD Weekly": (
            cm_macd_weekly.tolist()
            if cm_macd_weekly is not None
            else None
        ),
        "CM Signal Weekly": (
            cm_signal_weekly.tolist()
            if cm_signal_weekly is not None
            else None
        ),
        "CM Histogram Weekly": (
            cm_histogram_weekly.tolist()
            if cm_histogram_weekly is not None
            else None
        ),        
    }


def load_company_snapshot(ticker: str) -> dict:
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.get_info()
    dividend_history = ticker_obj.dividends
    annual_dividends = {}

    if not dividend_history.empty:
        annual_dividends = (
            dividend_history
            .groupby(dividend_history.index.year)
            .sum()
            .to_dict()
        )

    dividend_growth_3y = None

    completed_years = sorted(
        year
        for year in annual_dividends
        if year < pd.Timestamp.now().year
    )

    if len(completed_years) >= 3:
        last_three_years = completed_years[-3:]

        start_dividend = annual_dividends[
            last_three_years[0]
        ]
        end_dividend = annual_dividends[
            last_three_years[-1]
        ]

        if start_dividend > 0:
            dividend_growth_3y = (
                (
                    end_dividend / start_dividend
                ) ** (1 / 2)
                - 1
            ) * 100

    dividend_growth_points = None

    if dividend_growth_3y is not None:
        if dividend_growth_3y >= 5:
            dividend_growth_points = 2
        elif dividend_growth_3y >= 0:
            dividend_growth_points = 1
        else:
            dividend_growth_points = 0

    dividend_continuity_years = None
    dividend_cut_last_3y = None

    if len(completed_years) >= 3:
        recent_years = completed_years[-5:]

        cuts = []

        for previous_year, current_year in zip(
            recent_years,
            recent_years[1:],
        ):
            previous_dividend = annual_dividends[
                previous_year
            ]
            current_dividend = annual_dividends[
                current_year
            ]

            if current_dividend < previous_dividend:
                cuts.append(current_year)

        dividend_cut_last_3y = any(
            year in completed_years[-3:]
            for year in cuts
        )

        if not cuts:
            dividend_continuity_years = len(
                recent_years
            )
        else:
            last_cut_year = max(cuts)

            dividend_continuity_years = len(
                [
                    year
                    for year in recent_years
                    if year > last_cut_year
                ]
            )

    dividend_continuity_points = None

    if dividend_continuity_years is not None:
        if dividend_cut_last_3y:
            dividend_continuity_points = 0
        elif dividend_continuity_years >= 5:
            dividend_continuity_points = 2
        elif dividend_continuity_years >= 3:
            dividend_continuity_points = 1

    dividend_yield = info.get("dividendYield")
    payout_ratio = info.get("payoutRatio")

    payout_ratio_points = None

    if payout_ratio is not None:
        payout_percent = payout_ratio * 100

        if payout_percent > 110:
            payout_ratio_points = 0
        elif payout_percent > 90:
            payout_ratio_points = 1
        elif payout_percent > 70:
            payout_ratio_points = 2
        elif payout_percent > 20:
            payout_ratio_points = 3
        elif payout_percent > 0:
            payout_ratio_points = 2
        else:
            payout_ratio_points = 0
    five_year_avg_dividend_yield = info.get("fiveYearAvgDividendYield")
    dividend_rate = info.get("dividendRate")
    dividend_yield_points = None

    if (
        dividend_yield is None
        and info.get("trailingAnnualDividendRate") == 0
    ):
        dividend_yield = 0.0
        dividend_yield_points = None

    if dividend_yield is not None:
        if dividend_yield >= 5:
            dividend_yield_points = 5
        elif dividend_yield >= 4:
            dividend_yield_points = 4
        elif dividend_yield >= 3:
            dividend_yield_points = 3
        elif dividend_yield >= 2:
            dividend_yield_points = 2
        elif dividend_yield > 0:
            dividend_yield_points = 1
        else:
            dividend_yield_points = 0

    current_price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        )
    analyst_target = info.get("targetMeanPrice")

    analyst_target_manual = False
    analyst_target_metadata = {}

    if analyst_target is None or pd.isna(analyst_target):
        analyst_target = _get_manual_override(
            ticker,
            "Analystenziel",
        )

        if analyst_target is not None:
            analyst_target_manual = True
            analyst_target_metadata = _get_manual_override_metadata(
                ticker,
                "Analystenziel",
            )

    forward_pe = info.get("forwardPE")
    forward_pe_manual = False
    forward_pe_metadata = {}

    if forward_pe is None or pd.isna(forward_pe):
        forward_pe = _get_manual_override(
            ticker,
            "Forward KGV",
        )

        if forward_pe is not None:
            forward_pe_manual = True

        forward_pe_metadata = _get_manual_override_metadata(
            ticker,
            "Forward KGV",
        )

    analyst_upside = None

    if current_price and analyst_target:
        analyst_upside = (
            (analyst_target / current_price) - 1
        ) * 100

    return_on_equity = info.get("returnOnEquity")
    profit_margin = info.get("profitMargins")
    debt_to_equity = info.get("debtToEquity")
    revenue_growth = info.get("revenueGrowth")
    earnings_growth = info.get("earningsGrowth")
    capital_allocation_points = None

    if (
        payout_ratio is not None
        and revenue_growth is not None
        and earnings_growth is not None
    ):
        payout_percent = payout_ratio * 100
        revenue_growth_percent = revenue_growth * 100
        earnings_growth_percent = earnings_growth * 100

        if (
            payout_percent <= 25
            and (
                revenue_growth_percent >= 10
                or earnings_growth_percent >= 10
            )
        ):
            capital_allocation_points = 3

        elif (
            25 < payout_percent <= 70
            and (
                revenue_growth_percent > 0
                or earnings_growth_percent > 0
            )
        ):
            capital_allocation_points = 3

        elif (
            payout_percent > 70
            and revenue_growth_percent < 5
            and earnings_growth_percent < 5
        ):
            capital_allocation_points = 3

        else:
            capital_allocation_points = 2

    dividend_components = [
        (dividend_yield_points, 5),
        (payout_ratio_points, 3),
        (dividend_growth_points, 2),
        (dividend_continuity_points, 2),
        (capital_allocation_points, 3),
    ]

    dividend_available_points = sum(
        points
        for points, maximum in dividend_components
        if points is not None
    )

    dividend_available_maximum = sum(
        maximum
        for points, maximum in dividend_components
        if points is not None
    )

    dividend_strategy_score = None

    if dividend_available_maximum > 0:
        dividend_strategy_score = round(
            dividend_available_points
            / dividend_available_maximum
            * 15
        )

    dividend_strategy_score_raw = dividend_strategy_score

    if (
        dividend_strategy_score is not None
        and dividend_yield is not None
        and dividend_yield < 1.5
    ):
        dividend_strategy_score = min(
            dividend_strategy_score,
            9,
        )

    market_cap = info.get("marketCap")

    week_52_high = info.get("fiftyTwoWeekHigh")

    distance_to_52w_high = None

    if (
        current_price is not None
        and week_52_high is not None
        and week_52_high > 0
    ):
        distance_to_52w_high = (
            (current_price / week_52_high) - 1
        ) * 100

    if return_on_equity is not None:
        return_on_equity *= 100

    if profit_margin is not None:
        profit_margin *= 100

    if revenue_growth is not None:
        revenue_growth *= 100

    if earnings_growth is not None:
        earnings_growth *= 100

    momentum = load_momentum_metrics(ticker)

    history_5y = yf.Ticker(ticker).history(
        period="5y",
        interval="1wk",
        auto_adjust=True,
    )

    long_term_trend = analyze_trend_structure(
        history_5y,
        periods_per_year=52,
    )

    long_term_trend_score, long_term_trend_explanation = (
        calculate_long_term_trend_score(
            long_term_trend
        )
    )

    snapshot = {
        "Ticker": ticker,
        "Name": (
            info.get("longName")
            or info.get("shortName")
            or ticker
        ),
        "Land": info.get("country"),
        "Sektor": info.get("sector"),
        "Branche": info.get("industry"),
        "Kurs": current_price,
        "Währung": info.get("currency"),
        "Dividendenrendite": dividend_yield,
        "Dividendenrendite Punkte": dividend_yield_points,
        "Ausschüttungsquote": payout_ratio,
        "Ausschüttungsquote Punkte": payout_ratio_points,
        "Dividendenrendite 5J Ø": five_year_avg_dividend_yield,
        "Dividendenrate": dividend_rate,
        "Dividendenwachstum 3J": dividend_growth_3y,
        "Dividendenwachstum Punkte": dividend_growth_points,
        "Dividendenkontinuität Jahre": dividend_continuity_years,
        "Dividendenkürzung letzte 3J": dividend_cut_last_3y,
        "Dividendenkontinuität Punkte": dividend_continuity_points,
        "Dividenden jährlich": annual_dividends,
        "KGV": info.get("trailingPE"),
        "Forward KGV": forward_pe,
        "Forward KGV manuell": forward_pe_manual,
        "Forward KGV Metadaten": forward_pe_metadata,
        "Analystenziel": analyst_target,
        "Analystenziel manuell": analyst_target_manual,
        "Analystenziel Metadaten": analyst_target_metadata,
        "Analystenpotenzial": analyst_upside,
        "52W Hoch": week_52_high,
        "Abstand 52W Hoch": distance_to_52w_high,
        "Eigenkapitalrendite": return_on_equity,
        "Nettomarge": profit_margin,
        "Verschuldungsgrad": debt_to_equity,
        "Umsatzwachstum": revenue_growth,
        "Gewinnwachstum": earnings_growth,
        "Kapitalallokation Punkte": capital_allocation_points,
        "Dividendenstrategie Score vor Begrenzung": dividend_strategy_score_raw,
        "Dividendenstrategie Score": dividend_strategy_score,
        "Marktkapitalisierung": market_cap,
        "Momentum 3M": momentum["Momentum 3M"],
        "Momentum 6M": momentum["Momentum 6M"],
        "Momentum 12M": momentum["Momentum 12M"],
        "RSI 14": momentum["RSI 14"],
        "CM MACD": momentum["CM MACD"],
        "CM Signal": momentum["CM Signal"],
        "CM Histogram": momentum["CM Histogram"],
        "Langfristiger Trend": long_term_trend["direction"],
        "Trendkanal Position": long_term_trend["position"],
        "Trendkanal Position Normalisiert": long_term_trend["normalized_position"],
        "Langfristiger Trend Status": long_term_trend["status"],
        "Langfristiger Trend Confidence": long_term_trend["confidence"],
        "Langfristiger Trend Score": long_term_trend_score,
        "Langfristiger Trend Erklärung": long_term_trend_explanation,
        "CM MACD Weekly": momentum["CM MACD Weekly"],
        "CM Signal Weekly": momentum["CM Signal Weekly"],
        "CM Histogram Weekly": momentum["CM Histogram Weekly"],        
    }

    snapshot["Kaufchance"] = calculate_opportunity_score(
        snapshot
    )
    snapshot["Opportunity Breakdown"] = (
        calculate_opportunity_breakdown(snapshot)
    )
    snapshot["Unternehmensqualität"] = (
        calculate_quality_score(snapshot)
    )
    snapshot["Quality Breakdown"] = (
        calculate_quality_breakdown(snapshot)
    )

    return snapshot


def load_price_history(
    ticker: str,
    period: str = "6mo",
) -> pd.DataFrame:
    try:
        history = yf.Ticker(ticker).history(
            period=period,
            auto_adjust=True,
        )
    except Exception:
        return pd.DataFrame(
            columns=["Datum", "Schlusskurs"]
        )

    if history.empty or "Close" not in history.columns:
        return pd.DataFrame(
            columns=["Datum", "Schlusskurs"]
        )

    price_history = history.reset_index()

    date_column = price_history.columns[0]

    price_history = price_history[
        [date_column, "Close"]
    ].copy()

    price_history.columns = [
        "Datum",
        "Schlusskurs",
    ]

    price_history["Datum"] = pd.to_datetime(
        price_history["Datum"]
    )

    price_history["Schlusskurs"] = pd.to_numeric(
        price_history["Schlusskurs"],
        errors="coerce",
    )

    return price_history.dropna(
        subset=["Datum", "Schlusskurs"]
    )