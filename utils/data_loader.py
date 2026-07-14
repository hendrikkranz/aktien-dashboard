import pandas as pd
import streamlit as st
import yfinance as yf

from utils.analyst_data import load_analyst_targets
from utils.fundamentals import load_fundamentals
from utils.indicators import load_technical_indicators

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
        df["Analystenziel"] = pd.NA
        df["Analystenziel EUR"] = pd.NA
        df["Analystenpotenzial Prozent"] = pd.NA

        return df

    df["Ticker"] = (
        df["Ticker"]
        .astype("string")
        .str.strip()
    )

    tickers = (
        df["Ticker"]
        .dropna()
        .loc[lambda values: values.ne("")]
        .tolist()
    )
    technical_indicators = load_technical_indicators(tickers)
    fundamentals = load_fundamentals(tickers)
    live_data = load_live_data(tickers)
    analyst_targets = load_analyst_targets(tickers)
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

    df["Analystenziel"] = df["Ticker"].map(
        lambda ticker: analyst_targets.get(
            ticker,
            {},
        ).get("mean")
    )

    df["Analystenziel EUR"] = df.apply(
        lambda row: (
            row["Analystenziel"]
            * fx_rates.get(row["Live-Währung"])
            if pd.notna(row["Analystenziel"])
            and fx_rates.get(row["Live-Währung"]) is not None
            else pd.NA
        ),
        axis=1,
    )

    df["Analystenpotenzial Prozent"] = df.apply(
        lambda row: (
            (
                row["Analystenziel"]
                / row["Live-Kurs"]
                - 1
            )
            * 100
            if pd.notna(row["Analystenziel"])
            and pd.notna(row["Live-Kurs"])
            and row["Live-Kurs"] > 0
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
    technical_columns = [
        "50-Tage-Linie",
        "200-Tage-Linie",
        "Abstand 50-Tage-Linie Prozent",
        "Abstand 200-Tage-Linie Prozent",
        "Momentum 3 Monate Prozent",
        "Momentum 6 Monate Prozent",
    ]

    for column in technical_columns:
        df[column] = df["Ticker"].map(
            lambda ticker: technical_indicators.get(
                ticker,
                {},
            ).get(column, pd.NA)
        )
    return df
