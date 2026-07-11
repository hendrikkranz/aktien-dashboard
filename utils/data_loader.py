import pandas as pd
import streamlit as st
import yfinance as yf

from utils.fundamentals import load_fundamentals


@st.cache_data(ttl=1800)
def load_live_data(tickers):
    live_data = {}

    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(period="5d")

            if history.empty:
                live_data[ticker] = {
                    "price": None,
                    "currency": None,
                }
                continue

            metadata = stock.get_history_metadata()

            live_data[ticker] = {
                "price": float(history["Close"].dropna().iloc[-1]),
                "currency": metadata.get("currency"),
            }

        except Exception:
            live_data[ticker] = {
                "price": None,
                "currency": None,
            }

    return live_data


@st.cache_data(ttl=1800)
def load_fx_rates():
    rates = {
        "EUR": 1.0,
        "USD": None,
        "SGD": None,
    }

    try:
        eur_usd = yf.Ticker("EURUSD=X").history(period="5d")

        if not eur_usd.empty:
            rates["USD"] = 1 / float(
                eur_usd["Close"].dropna().iloc[-1]
            )

    except Exception:
        pass

    try:
        eur_sgd = yf.Ticker("EURSGD=X").history(period="5d")

        if not eur_sgd.empty:
            rates["SGD"] = 1 / float(
                eur_sgd["Close"].dropna().iloc[-1]
            )

    except Exception:
        pass

    return rates


@st.cache_data(ttl=1800)
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
        df["Live-Währung"] = pd.NA
        df["Live-Kurs EUR"] = pd.NA

        return df

    tickers = (
        df["Ticker"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    fundamentals = load_fundamentals(tickers)
    live_data = load_live_data(tickers)
    fx_rates = load_fx_rates()

    df["Live-Kurs"] = df["Ticker"].map(
        lambda ticker: live_data.get(
            ticker,
            {},
        ).get("price")
    )

    df["Live-Währung"] = df["Ticker"].map(
        lambda ticker: live_data.get(
            ticker,
            {},
        ).get("currency")
    )

    df["Live-Kurs EUR"] = df.apply(
        lambda row: (
            row["Live-Kurs"]
            * fx_rates.get(row["Live-Währung"])
            if pd.notna(row["Live-Kurs"])
            and fx_rates.get(row["Live-Währung"]) is not None
            else pd.NA
        ),
        axis=1,
    )

    fundamental_columns = [
        "Dividendenrendite Prozent",
        "KGV",
        "Forward KGV",
        "Umsatzwachstum Prozent",
        "Gewinnwachstum Prozent",
        "Ausschüttungsquote Prozent",
    ]

    for column in fundamental_columns:
        df[column] = df["Ticker"].map(
            lambda ticker: fundamentals.get(
                ticker,
                {},
            ).get(column, pd.NA)
        )

    return df
