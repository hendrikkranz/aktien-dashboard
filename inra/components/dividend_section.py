import streamlit as st

def render_dividend_section(data: dict) -> None:

    dividend = data.get("Dividendenrendite")

    if dividend is None:
        points = 0
        value = "Keine Daten"
        rating = "Keine Daten"
        icon = "⚪"
        border = "#6e7681"
        summary = (
            "Zur Dividendenstrategie liegen derzeit "
            "keine Daten vor."
        )

    else:

        value = f"{dividend:.1f} %"

        if dividend >= 5:
            points = 15
            rating = "Sehr attraktiv"
            icon = "🟢"
            border = "#2ea043"

        elif dividend >= 4:
            points = 12
            rating = "Attraktiv"
            icon = "🟢"
            border = "#2ea043"

        elif dividend >= 3:
            points = 9
            rating = "Gut"
            icon = "🟢"
            border = "#2ea043"

        elif dividend >= 2:
            points = 6
            rating = "Solide"
            icon = "🟡"
            border = "#d29922"

        elif dividend >= 1:
            points = 4
            rating = "Niedrig"
            icon = "🟡"
            border = "#d29922"

        elif dividend > 0:
            points = 2
            rating = "Re-Investor"
            icon = "🔵"
            border = "#1f6feb"

        else:
            points = 0
            rating = "Keine Dividende"
            icon = "⚪"
            border = "#6e7681"

        summary = (
            "Die Bewertung basiert aktuell ausschließlich "
            "auf der Dividendenrendite. "
            "In V2 fließen zusätzlich Ausschüttungsquote, "
            "Dividendenwachstum, Kontinuität, "
            "Kapitalallokation und Branchenvergleich ein."
        )

    card = f"""
<div style="
    background:#1b1f27;
    border-left:6px solid {border};
    border-radius:12px;
    padding:22px 24px;
    margin:10px 0 22px 0;
">
    <div style="
        color:#8b949e;
        font-size:12px;
        font-weight:700;
        text-transform:uppercase;
        letter-spacing:1px;
    ">
        Dividendenstrategie
    </div>

    <div style="
        color:white;
        font-size:32px;
        font-weight:700;
        margin-top:10px;
    ">
        {points} / 15
    </div>

    <div style="
        color:#d0d7de;
        font-size:15px;
        font-weight:600;
        margin-top:5px;
    ">
        {icon} {rating}
    </div>

    <div style="
        color:#c9d1d9;
        font-size:15px;
        line-height:1.55;
        margin-top:14px;
        max-width:1000px;
    ">
        {summary}
    </div>
</div>
"""

    st.html(card)

    with st.expander(
        f"Warum {points} von 15 Punkten?"
    ):

        st.markdown(
            f"**Dividendenrendite:** {value}"
        )

        st.info(
            "V1 bewertet ausschließlich die Dividendenrendite.\n\n"
            "V2 ergänzt:\n"
            "• Ausschüttungsquote\n"
            "• Dividendenwachstum\n"
            "• Kontinuität\n"
            "• Kapitalallokation\n"
            "• Branchenvergleich"
        )