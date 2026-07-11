import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=1800)
def load_live_prices(tickers):
    prices = {}

    for ticker in tickers:
        try:
            history = yf.Ticker(ticker).history(period="5d")

            if history.empty:
                prices[ticker] = None
            else:
                prices[ticker] = float(
                    history["Close"].dropna().iloc[-1]
                )

        except Exception:
            prices[ticker] = None

    return prices


@st.cache_data
def load_portfolio():
    df = pd.read_csv(
        "depot_watchlist.csv",
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )

    numeric_columns = [
        "Stück",
        "Kaufkurs",
        "Kaufwert EUR",
        "Spesen EUR",
        "Aktueller Kurs",
        "Aktueller Wert EUR",
        "Gewinn Verlust EUR",
        "Gewinn Verlust Prozent",
        "Gewichtung Prozent",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce",
            )

    if "Ticker" not in df.columns:
        df["Live-Kurs"] = pd.NA
        return df

    tickers = (
        df["Ticker"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    live_prices = load_live_prices(tickers)
    df["Live-Kurs"] = df["Ticker"].map(live_prices)

    return df
