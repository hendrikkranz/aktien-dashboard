import streamlit as st

from utils.data_loader import load_portfolio


st.title("💼 Depot")

df = load_portfolio("data/depot.csv")

st.success("Depotdaten erfolgreich geladen.")

st.dataframe(
    df,
    width="stretch",
    hide_index=True,
)