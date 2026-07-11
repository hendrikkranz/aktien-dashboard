import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=21600)
def load_fundamentals(tickers):
    """
    Lädt Fundamentaldaten für die übergebenen Yahoo-Finance-Ticker.

    Cache-Dauer: 6 Stunden, da sich Fundamentaldaten
    nicht laufend während des Tages verändern.
    """
    results = {}

    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).get_info()

            dividend_yield = info.get("dividendYield")
            dividend_rate = info.get("dividendRate")
            current_price = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
            )

            trailing_pe = info.get("trailingPE")
            forward_pe = info.get("forwardPE")
            revenue_growth = info.get("revenueGrowth")
            earnings_growth = info.get("earningsGrowth")
            payout_ratio = info.get("payoutRatio")

            if (
                dividend_rate is not None
                and current_price is not None
                and float(current_price) > 0
            ):
                dividend_yield_percent = (
                    float(dividend_rate)
                    / float(current_price)
                    * 100
                )
            elif dividend_yield is not None:
                raw_yield = float(dividend_yield)

                dividend_yield_percent = (
                    raw_yield / 100
                    if raw_yield > 20
                    else raw_yield
                )
            else:
                dividend_yield_percent = pd.NA

            results[ticker] = {
                "Dividendenrendite Prozent": dividend_yield_percent,
                "KGV": (
                    float(trailing_pe)
                    if trailing_pe is not None
                    else pd.NA
                ),
                "Forward KGV": (
                    float(forward_pe)
                    if forward_pe is not None
                    else pd.NA
                ),
                "Umsatzwachstum Prozent": (
                    float(revenue_growth) * 100
                    if revenue_growth is not None
                    else pd.NA
                ),
                "Gewinnwachstum Prozent": (
                    float(earnings_growth) * 100
                    if earnings_growth is not None
                    else pd.NA
                ),
                "Ausschüttungsquote Prozent": (
                    float(payout_ratio) * 100
                    if payout_ratio is not None
                    else pd.NA
                ),
            }

        except Exception:
            results[ticker] = {
                "Dividendenrendite Prozent": pd.NA,
                "KGV": pd.NA,
                "Forward KGV": pd.NA,
                "Umsatzwachstum Prozent": pd.NA,
                "Gewinnwachstum Prozent": pd.NA,
                "Ausschüttungsquote Prozent": pd.NA,
            }

    return results
