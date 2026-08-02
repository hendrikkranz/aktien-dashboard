import streamlit as st

from utils.market_data import load_company_snapshot

st.title("Analyse")
st.caption("Investmententscheidung auf einen Blick")

ticker = st.text_input(
    "Ticker",
    value="MSFT",
    placeholder="z. B. MSFT",
).strip().upper()

if ticker:
    data = load_company_snapshot(ticker)

    st.subheader(data["Name"])

    st.metric(
        "Kurs",
        f'{data["Kurs"]:.2f} {data["Währung"]}'
        if data["Kurs"] is not None
        else "Keine Daten",
    )

    st.metric(
        "Dividendenrendite",
        f'{data["Dividendenrendite"]:.2f} %'
        if data["Dividendenrendite"] is not None
        else "Keine Dividende",
    )

    st.metric(
        "KGV",
        f'{data["KGV"]:.1f}'
        if data["KGV"] is not None
        else "Keine Daten",
    )