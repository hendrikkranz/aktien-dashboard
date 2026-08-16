import streamlit as st

def render_dividend_section(data: dict) -> None:

    dividend = data.get("Dividendenrendite")
    points = data.get("Dividendenstrategie Score")

    if dividend is None:
        value = "Keine Daten"
    else:
        value = f"{dividend:.1f} %"

    if points is None:
        points = 0
        rating = "Keine Daten"
        icon = "⚪"
        border = "#6e7681"
        summary = (
            "Zur Dividendenstrategie liegen derzeit "
            "nicht genügend Daten vor."
        )

    elif points >= 12:
        rating = "Sehr stark"
        icon = "🟢"
        border = "#2ea043"
        summary = (
            "Die Dividendenstrategie ist insgesamt sehr überzeugend. "
            "Bewertet werden Rendite, Tragfähigkeit, Wachstum, "
            "Kontinuität und Kapitalallokation."
        )

    elif points >= 9:
        rating = "Stark"
        icon = "🟢"
        border = "#2ea043"

        if dividend is not None and dividend >= 5:
            summary = (
                "Die Dividendenstrategie ist insgesamt überzeugend. "
                "Die hohe Dividendenrendite ist eine besondere Stärke, "
                "während Tragfähigkeit und Kapitalallokation "
                "differenziert betrachtet werden sollten."
            )
        elif dividend is not None and dividend < 2:
            summary = (
                "Die Dividendenstrategie ist insgesamt überzeugend. "
                "Die niedrige Rendite wird durch andere Stärken "
                "der Ausschüttungs- und Reinvestitionsstrategie ausgeglichen."
            )
        else:
            summary = (
                "Die Dividendenstrategie ist insgesamt überzeugend "
                "und verbindet Ausschüttung, Wachstum und "
                "Kapitalallokation in einem soliden Verhältnis."
            )
    elif points >= 6:
        rating = "Solide"
        icon = "🟡"
        border = "#d29922"
        summary = (
            "Die Dividendenstrategie ist insgesamt solide, "
            "weist aber noch Schwächen oder nicht belastbare Teilbereiche auf."
        )

    else:
        rating = "Schwach"
        icon = "🔴"
        border = "#da3633"
        summary = (
            "Die Dividendenstrategie überzeugt derzeit nur eingeschränkt."
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

        dividend_yield_points = data.get(
            "Dividendenrendite Punkte"
        )
        payout_points = data.get(
            "Ausschüttungsquote Punkte"
        )
        growth_points = data.get(
            "Dividendenwachstum Punkte"
        )
        continuity_points = data.get(
            "Dividendenkontinuität Punkte"
        )
        allocation_points = data.get(
            "Kapitalallokation Punkte"
        )

        payout_ratio = data.get("Ausschüttungsquote")
        dividend_growth = data.get(
            "Dividendenwachstum 3J"
        )

        st.markdown(
            f"**Dividendenrendite:** {value}  \n"
            f"**{dividend_yield_points} von 5 Punkten**"
        )

        if payout_ratio is not None:
            payout_value = f"{payout_ratio * 100:.1f} %"
        else:
            payout_value = "Keine Daten"

        st.markdown(
            f"**Ausschüttungsquote:** {payout_value}  \n"
            f"**{payout_points} von 3 Punkten**"
        )

        if dividend_growth is not None:
            growth_value = f"{dividend_growth:.1f} % p. a."
            growth_score = f"{growth_points} von 2 Punkten"
        else:
            growth_value = "Noch nicht belastbar"
            growth_score = "Noch nicht bewertet"

        st.markdown(
            f"**Dividendenwachstum (3J):** {growth_value}  \n"
            f"**{growth_score}**"
        )

        if continuity_points is not None:
            continuity_years = data.get(
                "Dividendenkontinuität Jahre"
            )
            continuity_value = (
                f"{continuity_years} Jahre ohne Kürzung"
            )
            continuity_score = (
                f"{continuity_points} von 2 Punkten"
            )
        else:
            continuity_value = "Noch nicht belastbar"
            continuity_score = "Noch nicht bewertet"

        st.markdown(
            f"**Kontinuität:** {continuity_value}  \n"
            f"**{continuity_score}**"
        )

        if allocation_points is not None:
            allocation_score = (
                f"{allocation_points} von 3 Punkten"
            )
        else:
            allocation_score = "Noch nicht bewertet"

        st.markdown(
            f"**Kapitalallokation:** "
            f"{allocation_score}"
        )

        st.caption(
            "Fehlende Teilkriterien werden nicht mit 0 Punkten "
            "bewertet. Der verfügbare Score wird in diesem Fall "
            "proportional auf 15 Punkte normiert."
        )