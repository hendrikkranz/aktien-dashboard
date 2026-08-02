import streamlit as st

from utils.data_loader import load_universe

st.title("Scout")
st.caption("Welche Aktien verdienen heute meine Aufmerksamkeit?")

df = load_universe()

search = st.text_input("Aktie suchen", key="scout_search")

if search:
    df = df[
        df["Name"].str.contains(search, case=False, na=False)
        | df["Ticker"].str.contains(search, case=False, na=False)
    ]

st.metric("Aktien im Universum", len(df))

st.dataframe(df, width="stretch")