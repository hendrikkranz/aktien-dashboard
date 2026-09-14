import textwrap

import streamlit as st

from modules.chart_score import calculate_chart_breakdown
from modules.opportunity_score import calculate_opportunity_breakdown


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

    if not opportunity_data_complete:
        title = "Eingeschränkt bewertbar"
        icon = "⚪"
        background = "#F3F4F6"
        border = "#8b949e"
        text = (
            "Für ein belastbares Investment-Urteil fehlen derzeit "
            "wesentliche Daten zur Kaufchance."
        )

    elif buy_score >= 68 and quality_score >= 70:
        title = "Kaufen"
        icon = "🟢"
        background = "#EAF7F2"
        border = "#2EAD7B"
        text = (
            "Die Aktie bietet derzeit einen attraktiven Einstieg. "
            "Auch die Unternehmensqualität unterstützt ein "
            "langfristiges Investment."
        )
    elif buy_score >=51:
        title = "Beobachten"
        icon = "🟡"
        background = "#FFF8E1"
        border = "#D9A514"
        text = (
            "Die Aktie ist interessant, erfüllt derzeit aber noch "
            "nicht alle Voraussetzungen für eine klare Kaufempfehlung."
        )
    else:
        title = "Abwarten"
        icon = "🔴"
        background = "#FDEEEE"
        border = "#D9534F"
        text = (
            "Der aktuelle Einstieg erscheint momentan "
            "nicht attraktiv genug."
        )

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
{icon} {title}
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