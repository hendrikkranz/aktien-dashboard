import streamlit as st
import yfinance as yf


@st.cache_data(ttl=1800)
def load_analyst_targets(tickers):
    analyst_targets = {}

    for ticker in sorted(set(tickers)):
        try:
            stock = yf.Ticker(ticker)
            targets = stock.get_analyst_price_targets() or {}

            mean_target = targets.get("mean")

            analyst_targets[ticker] = {
                "mean": (
                    float(mean_target)
                    if mean_target is not None
                    else None
                )
            }

        except Exception:
            analyst_targets[ticker] = {
                "mean": None
            }

    return analyst_targets