import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Mein Aktien-Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Mein Aktien-Dashboard")
st.caption("Depotübersicht auf Basis meiner CSV-Datei")

@st.cache_data
def load_data():
    return pd.read_csv(
        "depot_watchlist.csv",
        sep=";",
        decimal=",",
        encoding="utf-8-sig",
    )

df = load_data()

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
        df[column] = pd.to_numeric(df[column], errors="coerce")

gesamtwert = df["Aktueller Wert EUR"].sum()
kaufwert = df["Kaufwert EUR"].sum()
gewinn = df["Gewinn Verlust EUR"].sum()
rendite = (gewinn / kaufwert * 100) if kaufwert else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("Depotwert", f"{gesamtwert:,.2f} €")
col2.metric("Investiert", f"{kaufwert:,.2f} €")
col3.metric("Gewinn / Verlust", f"{gewinn:,.2f} €")
col4.metric("Gesamtrendite", f"{rendite:.2f} %")

st.divider()

st.subheader("Depotpositionen")

sortierung = st.selectbox(
    "Sortieren nach",
    [
        "Gewichtung Prozent",
        "Aktueller Wert EUR",
        "Gewinn Verlust Prozent",
        "Gewinn Verlust EUR",
        "Name",
    ],
)

aufsteigend = st.checkbox("Aufsteigend sortieren", value=False)

anzeige_df = df.sort_values(
    by=sortierung,
    ascending=aufsteigend,
)

st.dataframe(
    anzeige_df[
        [
            "Name",
            "Typ",
            "WKN",
            "Stück",
            "Kaufkurs",
            "Aktueller Kurs",
            "Aktueller Wert EUR",
            "Gewinn Verlust EUR",
            "Gewinn Verlust Prozent",
            "Gewichtung Prozent",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

st.divider()

linke_spalte, rechte_spalte = st.columns(2)

with linke_spalte:
    st.subheader("Größte Positionen")

    gewichtung = (
        df.sort_values("Gewichtung Prozent", ascending=False)
        .head(10)
        .set_index("Name")["Gewichtung Prozent"]
    )

    st.bar_chart(gewichtung)

with rechte_spalte:
    st.subheader("Beste Wertentwicklungen")

    performance = (
        df.sort_values("Gewinn Verlust Prozent", ascending=False)
        .head(10)
        .set_index("Name")["Gewinn Verlust Prozent"]
    )

    st.bar_chart(performance)

st.divider()

st.subheader("Risikohinweise")

hohe_gewichtung = df[df["Gewichtung Prozent"] >= 10]

if hohe_gewichtung.empty:
    st.success("Keine Einzelposition überschreitet 10 % Gewichtung.")
else:
    for _, position in hohe_gewichtung.iterrows():
        st.warning(
            f'{position["Name"]}: '
            f'{position["Gewichtung Prozent"]:.2f} % Depotgewicht'
        )

st.caption(
    "Hinweis: Dieses Dashboard dient nur der Analyse und ist keine Anlageberatung."
)
