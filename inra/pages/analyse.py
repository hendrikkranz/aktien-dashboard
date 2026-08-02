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

    st.header(data["Name"])

    header_details = [
        data["Ticker"],
        data["Währung"],
        data.get("Land"),
        data.get("Sektor"),
        data.get("Branche"),
    ]

    st.caption(
        " • ".join(
            str(value)
            for value in header_details
            if value
        )
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Kurs",
            f'{data["Kurs"]:.2f} {data["Währung"]}'
            if data["Kurs"] is not None
            else "Keine Daten",
        )

    with col2:
        st.metric(
            "Dividendenrendite",
            f'{data["Dividendenrendite"]:.2f} %'
            if data["Dividendenrendite"] is not None
            else "Keine Dividende",
        )

    with col3:
        st.metric(
            "Potenzial",
            f'{data["Analystenpotenzial"]:.1f} %'
            if data["Analystenpotenzial"] is not None
            else "Keine Daten",
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "KGV",
            f'{data["KGV"]:.1f}'
            if data["KGV"] is not None
            else "Keine Daten",
        )

    with col5:
        st.metric(
            "Forward KGV",
            f'{data["Forward KGV"]:.1f}'
            if data["Forward KGV"] is not None
            else "Keine Daten",
        )

    with col6:
        st.metric(
            "Analystenziel",
            f'{data["Analystenziel"]:.2f} {data["Währung"]}'
            if data["Analystenziel"] is not None
            else "Keine Daten",
        )

    st.divider()

    st.subheader("Kaufchance")

    buy_score = data["Kaufchance"]

    if buy_score >= 80:
        rating = "🟢 Kaufen"
    elif buy_score >= 50:
        rating = "🟡 Beobachten"
    else:
        rating = "🔴 Abwarten"

    st.metric(rating, f"{buy_score} / 100")

    reasons = []

    if (
        data["Analystenpotenzial"] is not None
        and data["Analystenpotenzial"] >= 20
    ):
        reasons.append("✅ Hohes Analystenpotenzial")

    if (
        data["Forward KGV"] is not None
        and data["Forward KGV"] <= 20
    ):
        reasons.append("✅ Attraktive Bewertung (Forward KGV)")

    if (
        data["Dividendenrendite"] is not None
        and data["Dividendenrendite"] >= 2
    ):
        reasons.append("✅ Solide Dividendenrendite")

    if reasons:
        st.info("\n".join(reasons))
    else:
        st.info("Noch keine besonderen Kaufsignale.")

    st.divider()

    st.subheader("Unternehmensqualität")

    st.metric(
        "Quality Score",
        f'{data["Unternehmensqualität"]} / 100',
    )

    q1, q2, q3 = st.columns(3)

    with q1:
        st.metric(
            "ROE",
            f'{data["Eigenkapitalrendite"]:.1f} %'
            if data["Eigenkapitalrendite"] is not None
            else "–",
        )

    with q2:
        st.metric(
            "Nettomarge",
            f'{data["Nettomarge"]:.1f} %'
            if data["Nettomarge"] is not None
            else "–",
        )

    with q3:
        st.metric(
            "Debt / Equity",
            f'{data["Verschuldungsgrad"]:.1f}'
            if data["Verschuldungsgrad"] is not None
            else "–",
        )