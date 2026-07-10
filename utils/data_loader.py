import pandas as pd
import streamlit as st


@st.cache_data
def load_portfolio():

    df = pd.read_csv(
        "depot_watchlist.csv",
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )

    numeric = [
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

    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
