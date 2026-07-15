import streamlit as st

from utils.data_loader import load_portfolio
from utils.scoring import calculate_score


st.set_page_config(
    page_title="Mein Aktien-Dashboard",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Mein Aktien-Dashboard")
st.caption("Depotübersicht auf Basis meiner CSV-Datei")

df = load_portfolio()

# Einstand inklusive Kaufspesen
df["Spesen EUR"] = df["Spesen EUR"].fillna(0)
df["Einstand EUR"] = df["Kaufwert EUR"] + df["Spesen EUR"]

# Live-Depotwert berechnen
df["Live-Wert EUR"] = df["Stück"] * df["Live-Kurs EUR"]

# Falls kein Live-Kurs verfügbar ist, bisherigen CSV-Wert verwenden
df["Berechneter Wert EUR"] = df["Live-Wert EUR"].fillna(
    df["Aktueller Wert EUR"]
)

# Live-Gewinn und Live-Rendite
df["Live Gewinn Verlust EUR"] = (
    df["Berechneter Wert EUR"] - df["Einstand EUR"]
)

df["Live Gewinn Verlust Prozent"] = (
    df["Live Gewinn Verlust EUR"]
    / df["Einstand EUR"]
    * 100
)

# Gesamtwerte
gesamtwert = df["Berechneter Wert EUR"].sum()
kaufwert = df["Einstand EUR"].sum()
gewinn = df["Live Gewinn Verlust EUR"].sum()
rendite = (gewinn / kaufwert * 100) if kaufwert else 0

# Aktuelle Depotgewichtung
df["Live Gewichtung Prozent"] = (
    df["Berechneter Wert EUR"]
    / gesamtwert
    * 100
)

df["Score"] = df.apply(calculate_score, axis=1)

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
        "Score",
        "Analystenpotenzial Prozent",
        "Analystenziel EUR",
        "Live Gewichtung Prozent",
        "Berechneter Wert EUR",
        "Live Gewinn Verlust Prozent",
        "Live Gewinn Verlust EUR",
        "Name",
        "Dividendenrendite Prozent",
        "KGV",
        "Forward KGV",
        "Umsatzwachstum Prozent",
        "Gewinnwachstum Prozent",
        "Abstand 50-Tage-Linie Prozent",
        "Abstand 200-Tage-Linie Prozent",
        "Momentum 3 Monate Prozent",
        "Momentum 6 Monate Prozent",
    ],
)

aufsteigend = st.checkbox(
    "Aufsteigend sortieren",
    value=False,
)

anzeige_df = df.sort_values(
    by=sortierung,
    ascending=aufsteigend,
    na_position="last",
)

st.dataframe(
    anzeige_df[
        [
            "Name",
            "Score",
            "Ticker",
            "Typ",
            "WKN",
            "Stück",
            "Kaufkurs",
            "Live-Kurs",
            "Analystenziel",
            "Analystenziel EUR",
            "Analystenpotenzial Prozent",
            "Dividendenrendite Prozent",
            "KGV",
            "Forward KGV",
            "Umsatzwachstum Prozent",
            "Gewinnwachstum Prozent",
            "Ausschüttungsquote Prozent",
            "50-Tage-Linie",
            "200-Tage-Linie",
            "Abstand 50-Tage-Linie Prozent",
            "Abstand 200-Tage-Linie Prozent",
            "Momentum 3 Monate Prozent",
            "Momentum 6 Monate Prozent",
            "Live-Währung",
            "Live-Kurs EUR",
            "Berechneter Wert EUR",
            "Live Gewinn Verlust EUR",
            "Live Gewinn Verlust Prozent",
            "Live Gewichtung Prozent",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score",
            min_value=0,
            max_value=100,
            format="%d",
        ),
        "Live-Kurs": st.column_config.NumberColumn(
            "Live-Kurs",
            format="%.2f",
        ),
        "Analystenziel": st.column_config.NumberColumn(
            "Analystenziel",
            help=(
                "Durchschnittliches Analysten-Kursziel "
                "in der Handelswährung"
            ),
            format="%.2f",
        ),
        "Analystenziel EUR": st.column_config.NumberColumn(
            "Analystenziel EUR",
            help=(
                "Durchschnittliches Analysten-Kursziel, "
                "in Euro umgerechnet"
            ),
            format="%.2f €",
        ),
        "Analystenpotenzial Prozent": (
            st.column_config.NumberColumn(
                "Potenzial",
                help=(
                    "Abstand des durchschnittlichen "
                    "Analystenziels zum aktuellen Kurs"
                ),
                format="%.2f %%",
            )
        ),
        "Live-Kurs EUR": st.column_config.NumberColumn(
            "Live-Kurs EUR",
            format="%.2f €",
        ),
        "Berechneter Wert EUR": (
            st.column_config.NumberColumn(
                "Depotwert",
                format="%.2f €",
            )
        ),
        "Live Gewinn Verlust EUR": (
            st.column_config.NumberColumn(
                "Gewinn/Verlust",
                format="%.2f €",
            )
        ),
        "Live Gewinn Verlust Prozent": (
            st.column_config.NumberColumn(
                "Rendite",
                format="%.2f %%",
            )
        ),
        "Dividendenrendite Prozent": st.column_config.NumberColumn(
            "Div.-Rendite",
            format="%.2f %%",
        ),
        "KGV": st.column_config.NumberColumn(
            "KGV",
            format="%.2f",
        ),
        "Forward KGV": st.column_config.NumberColumn(
            "Forward KGV",
            format="%.2f",
        ),
        "50-Tage-Linie": st.column_config.NumberColumn(
            "SMA 50",
            format="%.2f",
        ),
        "200-Tage-Linie": st.column_config.NumberColumn(
            "SMA 200",
            format="%.2f",
        ),
        "Abstand 50-Tage-Linie Prozent": st.column_config.NumberColumn(
            "Abstand SMA 50",
            format="%.1f %%",
        ),
        "Abstand 200-Tage-Linie Prozent": st.column_config.NumberColumn(
            "Abstand SMA 200",
            format="%.1f %%",
        ),
        "Momentum 3 Monate Prozent": st.column_config.NumberColumn(
            "Momentum 3M",
            format="%.1f %%",
        ),
        "Momentum 6 Monate Prozent": st.column_config.NumberColumn(
            "Momentum 6M",
            format="%.1f %%",
        ),
        "Live Gewichtung Prozent": (
            st.column_config.NumberColumn(
                "Gewichtung",
                format="%.2f %%",
            )
        ),
    },
)

st.divider()

linke_spalte, rechte_spalte = st.columns(2)

with linke_spalte:
    st.subheader("Größte Positionen")

    gewichtung = (
        df.sort_values(
            "Live Gewichtung Prozent",
            ascending=False,
        )
        .head(10)
        .set_index("Name")["Live Gewichtung Prozent"]
    )

    st.bar_chart(gewichtung)

with rechte_spalte:
    st.subheader("Beste Wertentwicklungen")

    performance = (
        df.sort_values(
            "Live Gewinn Verlust Prozent",
            ascending=False,
        )
        .head(10)
        .set_index("Name")["Live Gewinn Verlust Prozent"]
    )

    st.bar_chart(performance)

st.divider()

st.subheader("Risikohinweise")

hohe_gewichtung = df[
    df["Live Gewichtung Prozent"] >= 10
]

if hohe_gewichtung.empty:
    st.success(
        "Keine Einzelposition überschreitet 10 % Gewichtung."
    )
else:
    for _, position in hohe_gewichtung.iterrows():
        st.warning(
            f'{position["Name"]}: '
            f'{position["Live Gewichtung Prozent"]:.2f} % '
            f'Depotgewicht'
        )

st.caption(
    "Hinweis: Dieses Dashboard dient nur der Analyse "
    "und ist keine Anlageberatung."
)
