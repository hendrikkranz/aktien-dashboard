import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=21600)
def load_technical_indicators(tickers):
    """
    Lädt historische Kurse und berechnet einfache Technik-Kennzahlen.

    Cache-Dauer: 6 Stunden.
    """
    results = {}

    for ticker in tickers:
        try:
            history = yf.Ticker(ticker).history(
                period="1y",
                auto_adjust=True,
            )

            close = history["Close"].dropna()

            if close.empty:
                raise ValueError("Keine Kursdaten vorhanden")

            current_price = float(close.iloc[-1])

            sma_50 = (
                float(close.tail(50).mean())
                if len(close) >= 50
                else pd.NA
            )

            sma_200 = (
                float(close.tail(200).mean())
                if len(close) >= 200
                else pd.NA
            )

            momentum_3m = (
                (current_price / float(close.iloc[-64]) - 1) * 100
                if len(close) >= 64
                else pd.NA
            )

            momentum_6m = (
                (current_price / float(close.iloc[-127]) - 1) * 100
                if len(close) >= 127
                else pd.NA
            )

            results[ticker] = {
                "50-Tage-Linie": sma_50,
                "200-Tage-Linie": sma_200,
                "Abstand 50-Tage-Linie Prozent": (
                    (current_price / sma_50 - 1) * 100
                    if pd.notna(sma_50)
                    else pd.NA
                ),
                "Abstand 200-Tage-Linie Prozent": (
                    (current_price / sma_200 - 1) * 100
                    if pd.notna(sma_200)
                    else pd.NA
                ),
                "Momentum 3 Monate Prozent": momentum_3m,
                "Momentum 6 Monate Prozent": momentum_6m,
            }

        except Exception:
            results[ticker] = {
                "50-Tage-Linie": pd.NA,
                "200-Tage-Linie": pd.NA,
                "Abstand 50-Tage-Linie Prozent": pd.NA,
                "Abstand 200-Tage-Linie Prozent": pd.NA,
                "Momentum 3 Monate Prozent": pd.NA,
                "Momentum 6 Monate Prozent": pd.NA,
            }

    return results
