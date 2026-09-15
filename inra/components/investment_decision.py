import textwrap

import streamlit as st

from modules.chart_score import calculate_chart_breakdown
from modules.opportunity_score import (
    calculate_opportunity_breakdown,
    get_pe_valuation_class,
)

def _is_distressed(data: dict) -> bool:
    distress_values = (
        data.get("Kapitalrendite"),
        data.get("Operative Marge"),
        data.get("Operativer Cashflow"),
        data.get("EBITDA"),
    )

    negative_signals = sum(
        value is not None and value < 0
        for value in distress_values
    )

    return negative_signals >= 3

def render_investment_decision(data: dict) -> None:
    buy_score = data["Kaufchance"]
    quality_score = data["Unternehmensqualität"]

    opportunity_breakdown = calculate_opportunity_breakdown(data)
    chart_breakdown = calculate_chart_breakdown(data)

    available_maximum = (
        sum(
            item["Maximum"]
            for item in opportunity_breakdown
            if item["Punkte"] is not None
        )
        + sum(
            item["Maximum"]
            for item in chart_breakdown
            if item["Punkte"] is not None
        )
    )

    opportunity_data_complete = available_maximum == 100

    investment_score = (
        0.60 * buy_score
        + 0.40 * quality_score
    )

    if _is_distressed(data):
        title = "Kein Investment"
        icon = "🔴"
        background = "#FDEEEE"
        border = "#D9534F"
        text = (
            "Mehrere zentrale operative Kennzahlen sind negativ. "
            "Die fundamentale Belastung ist derzeit zu hoch für "
            "ein Investment."
        )

    elif (
        not opportunity_data_complete
        and get_pe_valuation_class(data) == "SONDERFALL"
    ):
        title = "Sonderfall"
        icon = "⚪"
        background = "#F3F4F6"
        border = "#8b949e"
        text = (
            "Die KGV-basierte Kursbewertung ist für diesen "
            "Unternehmenstyp methodisch nicht anwendbar. "
            "Daher wird derzeit kein reguläres Investment-Urteil "
            "vergeben."
        )

    elif not opportunity_data_complete:
        title = "Eingeschränkt bewertbar"
        icon = "⚪"
        background = "#F3F4F6"
        border = "#8b949e"
        text = (
            "Für ein belastbares Investment-Urteil fehlen derzeit "
            "wesentliche Daten zur Kaufchance."
        )

    elif investment_score >= 80 and buy_score >= 70:
        title = "Klarer Kauf"
        icon = "★"
        background = "#E4F8EE"
        border = "#20C77A"
        text = (
            "Kaufchance und Unternehmensqualität ergeben zusammen "
            "eine besonders überzeugende Investment-Konstellation."
        )

    elif investment_score >= 70 and buy_score >= 60:
        title = "Erste Position aufbauen"
        icon = "🟢"
        background = "#EAF7F2"
        border = "#2EAD7B"
        text = (
            "Die Kombination aus Einstiegschance und "
            "Unternehmensqualität spricht derzeit für den Aufbau "
            "einer ersten Position."
        )

    elif buy_score >= 75 and investment_score < 70:
        title = "Trading-Chance"
        icon = "🔵"
        background = "#EEF5FF"
        border = "#4A90E2"
        text = (
            "Die aktuelle Einstiegssituation ist außergewöhnlich "
            "attraktiv, die Unternehmensqualität reicht jedoch "
            "nicht für eine reguläre Kaufempfehlung."
        )

    elif investment_score >= 55:
        title = "Beobachten"
        icon = "🟡"
        background = "#FFF8E1"
        border = "#D9A514"
        text = (
            "Die Aktie bleibt interessant, die Kombination aus "
            "Einstiegschance und Unternehmensqualität reicht derzeit "
            "aber noch nicht für eine Kaufempfehlung."
        )

    else:
        title = "Abwarten"
        icon = "🟠"
        background = "#FFF3E8"
        border = "#E58A2B"
        text = (
            "Die aktuelle Kombination aus Einstiegschance und "
            "Unternehmensqualität ist für ein Investment derzeit "
            "nicht attraktiv genug."
        )

    if title == "Klarer Kauf":
        icon_html = (
            '<span style="color:#20C77A;">★</span>'
        )
    else:
        icon_html = icon

    html = textwrap.dedent(
    f"""
<div style="
    background:#1b1f27;
    border:3px solid {border};
    border-radius:12px;
    padding:26px 30px;
    margin:8px 0 26px 0;
    box-shadow:0 8px 28px rgba(0,0,0,0.35);
">

<div style="
    color:#8b949e;
    font-size:12px;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:1px;
">
Investment-Urteil
</div>

<div style="
    color:white;
    font-size:34px;
    font-weight:700;
    margin-top:10px;
">
{icon_html} {title}
</div>

<div style="
    color:#c9d1d9;
    font-size:16px;
    margin-top:12px;
    line-height:1.5;
">
{text}
</div>

</div>
"""
).strip()

    st.html(html)