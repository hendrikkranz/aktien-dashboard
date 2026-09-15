import streamlit as st

def render_dividend_section(data: dict) -> None:

    dividend = data.get("Dividendenrendite")
    points = data.get("Dividendenstrategie Score")
    dividend_status = data.get("Dividendenstrategie Status")
    is_non_dividend_payer = (
        dividend_status == "Keine Dividende"
    )

    if dividend is None:
        value = "Keine Daten"
    else:
        value = f"{dividend:.1f} %"

    high_yield_icon = (
        " 💰"
        if dividend is not None and dividend >= 3.0
        else ""
    )

    display_score = (
        f"{points} / 15"
        if points is not None
        else "Keine Daten"
    )

    if is_non_dividend_payer:
        display_score = "Keine Dividende"
        rating = "Nicht anwendbar"
        icon = "⚪"
        border = "#6e7681"
        summary = (
            "Das Unternehmen schüttet derzeit keine Dividende aus. "
            "Eine Bewertung nach Dividendenrendite, Ausschüttungsquote, "
            "Wachstum und Kontinuität ist daher nicht sinnvoll."
        )

    elif points is None:
        display_score = "Keine Daten"
        rating = "Keine Daten"
        icon = "⚪"
        border = "#6e7681"
        summary = (
            "Zur Dividendenstrategie liegen derzeit "
            "nicht genügend Daten vor."
        )

    elif points >= 12:
        display_score = f"{points} / 15"
        rating = "Sehr stark"
        icon = "🟢"
        border = "#2ea043"
        summary = (
            "Die Dividendenstrategie ist insgesamt sehr überzeugend. "
            "Bewertet werden Rendite, Tragfähigkeit, Wachstum, "
            "Kontinuität und Kapitalallokation."
        )

    elif points >= 10:
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
        {display_score}
    </div>

    <div style="
        color:#d0d7de;
        font-size:15px;
        font-weight:600;
        margin-top:5px;
    ">
        {icon} {rating}{high_yield_icon}
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

    if is_non_dividend_payer:
        with st.expander("Warum keine Bewertung?"):
            st.markdown(
                "**Dividendenrendite:** 0,0 %  \n"
                "**Keine Dividendenzahlung**"
            )

            st.markdown(
                "Das Unternehmen zahlt derzeit keine Dividende. "
                "Deshalb werden Dividendenrendite, Ausschüttungsquote, "
                "Dividendenwachstum und Kontinuität nicht mit Punkten "
                "bewertet."
            )

            st.caption(
                "Eine bewusste Nichtausschüttung wird nicht als schwache "
                "Dividendenstrategie gewertet. Die Kapitalallokation "
                "fließt nicht allein in einen Dividendenscore ein."
            )

    else:
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

            if dividend is not None and dividend < 1.5:
                raw_points = data.get(
                    "Dividendenstrategie Score vor Begrenzung"
                )

                if raw_points is not None and raw_points > 9:
                    reduction = raw_points - points

                    st.info(
                        f"**Finale Anpassung:**  \n"
                        f"Berechneter Score: **{raw_points} / 15**  \n"
                        f"Begrenzung wegen Dividendenrendite "
                        f"unter 1,5 %: **−{reduction} "
                        f"{'Punkt' if reduction == 1 else 'Punkte'}**  \n"
                        f"Finaler Score: **{points} / 15**"
                    )

            st.caption(
                "Fehlende Teilkriterien werden nicht mit 0 Punkten "
                "bewertet. Der verfügbare Score wird in diesem Fall "
                "proportional auf 15 Punkte normiert."
            )
