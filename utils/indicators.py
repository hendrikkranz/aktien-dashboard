import pandas as pd
import streamlit as st
import yfinance as yf


@st.cache_data(ttl=21600)
def load_technical_indicators(tickers):
    """
    Lädt historische Kurse und berechnet einfache Technik-Kennzahlen.

    Berechnet:
    - 50-Tage-Linie
    - 200-Tage-Linie
    - Abstand zur 50-Tage-Linie in Prozent
    - Abstand zur 200-Tage-Linie in Prozent
    - Momentum über 3 Monate
    - Momentum über 6 Monate

    Cache-Dauer: 6 Stunden.
    """
    results = {}

    for ticker in sorted(set(tickers)):
        if not ticker or pd.isna(ticker):
            continue

        try:
            history = yf.Ticker(ticker).history(
                period="1y",
                auto_adjust=True,
            )

            close = history["Close"].dropna()

            if close.empty:
                raise ValueError("Keine Kursdaten vorhanden")

            current_price = float(close.iloc[-1])

            high_52w = float(close.max())

            distance_52w_high = (
                (current_price / high_52w - 1) * 100
                if high_52w > 0
                else pd.NA
            )

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

            distance_sma_50 = (
                (current_price / sma_50 - 1) * 100
                if pd.notna(sma_50) and sma_50 > 0
                else pd.NA
            )

            distance_sma_200 = (
                (current_price / sma_200 - 1) * 100
                if pd.notna(sma_200) and sma_200 > 0
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
                "Abstand 52-Wochen-Hoch Prozent": distance_52w_high,
                "Abstand 50-Tage-Linie Prozent": distance_sma_50,
                "Abstand 200-Tage-Linie Prozent": distance_sma_200,
                "Momentum 3 Monate Prozent": momentum_3m,
                "Momentum 6 Monate Prozent": momentum_6m,
            }

        except Exception as error:
            print(
                f"Technische Kennzahlen konnten für "
                f"{ticker} nicht geladen werden: {error}"
            )

            results[ticker] = {
                "50-Tage-Linie": pd.NA,
                "200-Tage-Linie": pd.NA,
                "Abstand 52-Wochen-Hoch Prozent": pd.NA,
                "Abstand 50-Tage-Linie Prozent": pd.NA,
                "Abstand 200-Tage-Linie Prozent": pd.NA,
                "Momentum 3 Monate Prozent": pd.NA,
                "Momentum 6 Monate Prozent": pd.NA,
            }

    return results