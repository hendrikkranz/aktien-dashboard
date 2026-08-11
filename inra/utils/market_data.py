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
    info = yf.Ticker(ticker).get_info()

    dividend_yield = info.get("dividendYield")

    if (
        dividend_yield is None
        and info.get("trailingAnnualDividendRate") == 0
    ):
        dividend_yield = 0.0
    current_price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
    )
    analyst_target = info.get("targetMeanPrice")

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
        "KGV": info.get("trailingPE"),
        "Forward KGV": info.get("forwardPE"),
        "Analystenziel": analyst_target,
        "Analystenpotenzial": analyst_upside,
        "52W Hoch": week_52_high,
        "Abstand 52W Hoch": distance_to_52w_high,
        "Eigenkapitalrendite": return_on_equity,
        "Nettomarge": profit_margin,
        "Verschuldungsgrad": debt_to_equity,
        "Umsatzwachstum": revenue_growth,
        "Gewinnwachstum": earnings_growth,
        "Marktkapitalisierung": market_cap,
        "Momentum 3M": momentum["Momentum 3M"],
        "Momentum 6M": momentum["Momentum 6M"],
        "Momentum 12M": momentum["Momentum 12M"],
        "RSI 14": momentum["RSI 14"],
        "CM MACD": momentum["CM MACD"],
        "CM Signal": momentum["CM Signal"],
        "CM Histogram": momentum["CM Histogram"],
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