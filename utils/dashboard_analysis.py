from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from utils.data_loader import load_portfolio
from utils.recommendation import get_recommendation
from utils.scoring import (
    calculate_growth_score,
    calculate_momentum_score,
    calculate_quality_score,
    calculate_score,
    calculate_value_score,
)


def render_dashboard(csv_path, title, subtitle):
    dashboard_zeitpunkt = datetime.now(
        ZoneInfo("Europe/Berlin")
    )

    st.title(title)
    st.caption(subtitle)
    st.caption(
        "Dashboard geladen: "
        f"{dashboard_zeitpunkt:%d.%m.%Y · %H:%M Uhr}"
    )

    df = load_portfolio(csv_path)

    

    

    # Teil-Scores
    df["Quality Score"] = df.apply(
        calculate_quality_score,
        axis=1,
    )

    df["Value Score"] = df.apply(
        calculate_value_score,
        axis=1,
    )

    df["Growth Score"] = df.apply(
        calculate_growth_score,
        axis=1,
    )

    df["Momentum Score"] = df.apply(
        calculate_momentum_score,
        axis=1,
    )

    # Gesamtscore
    df["Score"] = df.apply(
        calculate_score,
        axis=1,
    )

    # Empfehlung muss nach den Scores berechnet werden
    df["Empfehlung"] = df.apply(
        get_recommendation,
        axis=1,
    )

    st.divider()

    st.subheader("Aktienanalyse")

    sortierung = st.selectbox(
        "Sortieren nach",
        [
            "Score",
            "Quality Score",
            "Value Score",
            "Growth Score",
            "Momentum Score",
            "Analystenpotenzial Prozent",
            "Analystenziel EUR",
            "Name",
            "Kursdatum",
            "Dividendenrendite Prozent",
            "KGV",
            "Forward KGV",
            "PEG",
            "Umsatzwachstum Prozent",
            "Gewinnwachstum Prozent",
            "Ausschüttungsquote Prozent",
            "50-Tage-Linie",
            "200-Tage-Linie",
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
                "Empfehlung",
                "Name",
                "Score",
                "Quality Score",
                "Value Score",
                "Growth Score",
                "Momentum Score",
                "Ticker",
                "Typ",
                "WKN",
                "Live-Kurs",
                "Live-Währung",
                "Live-Kurs EUR",
                "Kursdatum",
                "Analystenziel",
                "Analystenziel EUR",
                "Analystenpotenzial Prozent",
                "Dividendenrendite Prozent",
                "KGV",
                "Forward KGV",
                "PEG",
                "Umsatzwachstum Prozent",
                "Gewinnwachstum Prozent",
                "Ausschüttungsquote Prozent",
                "50-Tage-Linie",
                "200-Tage-Linie",
                "Abstand 50-Tage-Linie Prozent",
                "Abstand 200-Tage-Linie Prozent",
                "Momentum 3 Monate Prozent",
                "Momentum 6 Monate Prozent",
            ]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "Empfehlung": st.column_config.TextColumn(
                "Empfehlung",
                help=(
                    "Automatische Einordnung anhand von "
                    "Gesamtscore, Analystenpotenzial, "
                    "Momentum und Gewinnwachstum"
                ),
                width="medium",
            ),
            "Score": st.column_config.ProgressColumn(
                "Gesamt",
                help=(
                    "Gewichteter Gesamtscore aus Quality, "
                    "Value, Growth und Momentum"
                ),
                min_value=0,
                max_value=100,
                format="%d",
            ),
            "Quality Score": st.column_config.ProgressColumn(
                "Quality",
                help="Qualitätsscore des Unternehmens",
                min_value=0,
                max_value=100,
                format="%d",
            ),
            "Value Score": st.column_config.ProgressColumn(
                "Value",
                help=(
                    "Bewertung anhand von PEG, Forward KGV "
                    "und Analystenpotenzial"
                ),
                min_value=0,
                max_value=100,
                format="%d",
            ),
            "Growth Score": st.column_config.ProgressColumn(
                "Growth",
                help="Bewertung des Umsatz- und Gewinnwachstums",
                min_value=0,
                max_value=100,
                format="%d",
            ),
            "Momentum Score": st.column_config.ProgressColumn(
                "Momentum",
                help=(
                    "Technischer Score aus SMA-Abständen "
                    "und Kursmomentum"
                ),
                min_value=0,
                max_value=100,
                format="%d",
            ),
            "Live-Kurs": st.column_config.NumberColumn(
                "Live-Kurs",
                format="%.2f",
            ),
            "Kursdatum": st.column_config.TextColumn(
                "Kursdatum",
                help="Datum des letzten verfügbaren Yahoo-Kurses",
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
            "Dividendenrendite Prozent": (
                st.column_config.NumberColumn(
                    "Div.-Rendite",
                    format="%.2f %%",
                )
            ),
            "KGV": st.column_config.NumberColumn(
                "KGV",
                format="%.2f",
            ),
            "Forward KGV": st.column_config.NumberColumn(
                "Forward KGV",
                format="%.2f",
            ),
            "PEG": st.column_config.NumberColumn(
                "PEG",
                format="%.2f",
            ),
            "Umsatzwachstum Prozent": (
                st.column_config.NumberColumn(
                    "Umsatzwachstum",
                    format="%.2f %%",
                )
            ),
            "Gewinnwachstum Prozent": (
                st.column_config.NumberColumn(
                    "Gewinnwachstum",
                    format="%.2f %%",
                )
            ),
            "Ausschüttungsquote Prozent": (
                st.column_config.NumberColumn(
                    "Ausschüttungsquote",
                    format="%.2f %%",
                )
            ),
            "50-Tage-Linie": st.column_config.NumberColumn(
                "SMA 50",
                format="%.2f",
            ),
            "200-Tage-Linie": st.column_config.NumberColumn(
                "SMA 200",
                format="%.2f",
            ),
            "Abstand 50-Tage-Linie Prozent": (
                st.column_config.NumberColumn(
                    "Abstand SMA 50",
                    format="%.2f %%",
                )
            ),
            "Abstand 200-Tage-Linie Prozent": (
                st.column_config.NumberColumn(
                    "Abstand SMA 200",
                    format="%.2f %%",
                )
            ),
            "Momentum 3 Monate Prozent": (
                st.column_config.NumberColumn(
                    "Momentum 3M",
                    format="%.2f %%",
                )
            ),
            "Momentum 6 Monate Prozent": (
                st.column_config.NumberColumn(
                    "Momentum 6M",
                    format="%.2f %%",
                )
            ),
            "Live-Kurs EUR": st.column_config.NumberColumn(
                "Live-Kurs EUR",
                format="%.2f €",
            ),
                    },
    )

    st.caption(
        "Hinweis: Dieses Dashboard dient ausschließlich der Analyse von Aktien "
        "und stellt keine Anlageberatung dar."
    )