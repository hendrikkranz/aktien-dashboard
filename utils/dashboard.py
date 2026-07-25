import streamlit as st

from utils.data_loader import load_portfolio


def render_dashboard(csv_path, title):
    st.title(title)

    df = load_portfolio(csv_path)

    st.success("Daten erfolgreich geladen.")

    st.dataframe(
        df,
        width="stretch",
        hide_index=True,
    )