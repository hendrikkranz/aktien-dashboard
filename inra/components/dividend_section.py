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

        return

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

    if payout_ratio is not None:
        payout_value = f"{payout_ratio * 100:.1f} %"
    else:
        payout_value = "Keine Daten"

    if dividend_growth is not None:
        growth_value = f"{dividend_growth:.1f} % p. a."
    else:
        growth_value = "Noch nicht belastbar"

    if continuity_points is not None:
        continuity_years = data.get(
            "Dividendenkontinuität Jahre"
        )
        continuity_value = (
            f"{continuity_years} Jahre ohne Kürzung"
        )
    else:
        continuity_value = "Noch nicht belastbar"

    def score_icon(score, maximum):
        if score is None:
            return "⚪"

        ratio = score / maximum if maximum else 0

        if ratio >= 0.8:
            return "🟢"
        if ratio >= 0.5:
            return "🟡"
        return "🔴"

    def render_section(title, score, maximum):
        icon_local = score_icon(score, maximum)
        score_text = (
            f"{score} / {maximum}"
            if score is not None
            else "Nicht bewertbar"
        )

        st.markdown(
            f"##### {icon_local} {title}"
        )

    def render_row(label, row_value, score, maximum):
        if score is None:
            row_icon = "⚪"
            score_text = "Nicht bewertbar"
        else:
            row_icon = score_icon(score, maximum)
            score_text = f"{score} / {maximum}"

        st.html(
            f"""
            <div style="
                display:grid;
                grid-template-columns:minmax(150px, 1fr) 180px 150px;
                gap:16px;
                align-items:center;
                padding:10px 0;
                border-bottom:1px solid #30363d;
            ">
                <div style="
                    color:#c9d1d9;
                    font-size:14px;
                    font-weight:600;
                ">
                    {label}
                </div>

                <div style="
                    color:white;
                    font-size:17px;
                    font-weight:700;
                    text-align:right;
                ">
                    {row_value}
                </div>

                <div style="
                    color:#d0d7de;
                    font-size:14px;
                    font-weight:600;
                    white-space:nowrap;
                    text-align:right;
                ">
                    {row_icon} {score_text}
                </div>
            </div>
            """
        )

    render_section(
        "Dividendenrendite",
        dividend_yield_points,
        5,
    )
    render_row(
        "Dividendenrendite",
        value,
        dividend_yield_points,
        5,
    )

    st.divider()

    render_section(
        "Tragfähigkeit",
        payout_points,
        3,
    )
    render_row(
        "Ausschüttungsquote",
        payout_value,
        payout_points,
        3,
    )

    st.divider()

    render_section(
        "Dividendenwachstum",
        growth_points,
        2,
    )
    render_row(
        "Dividendenwachstum (3J)",
        growth_value,
        growth_points,
        2,
    )

    st.divider()

    render_section(
        "Kontinuität",
        continuity_points,
        2,
    )
    render_row(
        "Jahre ohne Kürzung",
        continuity_value,
        continuity_points,
        2,
    )

    st.divider()

    render_section(
        "Kapitalallokation",
        allocation_points,
        3,
    )
    render_row(
        "Kapitalallokation",
        "Strategische Bewertung",
        allocation_points,
        3,
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
