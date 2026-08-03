import html

import streamlit as st

from utils.investment_summary import create_investment_summary


def _score_icon(score: int, maximum: int) -> str:
    ratio = score / maximum if maximum else 0

    if ratio >= 0.8:
        return "🟢"
    if ratio >= 0.5:
        return "🟡"

    return "🔴"


def _render_subscore(
    column,
    label: str,
    score: int,
    maximum: int,
    explanation: str,
) -> None:
    safe_explanation = html.escape(
        explanation,
        quote=True,
    )

    icon = _score_icon(score, maximum)

    with column:
        st.markdown(
            f"""
            <div title="{safe_explanation}">
                <div style="
                    font-size:0.82rem;
                    font-weight:600;
                    white-space:nowrap;
                ">
                    {icon} {label} ⓘ
                </div>
                <div style="
                    font-size:1.45rem;
                    margin-top:0.25rem;
                    white-space:nowrap;
                ">
                    {score} / {maximum}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _plus(column) -> None:
    with column:
        st.markdown(
            """
            <div style="
                color:#666;
                font-size:0.95rem;
                text-align:center;
                padding-top:1.05rem;
                font-weight:300;
            ">
                +
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_quality_section(data: dict) -> None:
    st.subheader("Unternehmensqualität")

    st.metric(
        "Quality Score",
        f'{data["Unternehmensqualität"]} / 100',
        help=(
            "Gesamtbewertung der Unternehmensqualität. "
            "Der Score setzt sich aus Profitabilität, "
            "Wachstum, Bilanz und Dividende zusammen."
        ),
    )

    st.info(create_investment_summary(data))

    breakdown = data["Quality Breakdown"]

    s1, p1, s2, p2, s3, p3, s4 = st.columns(
        [1, 0.12, 1, 0.12, 1, 0.12, 1]
    )

    _render_subscore(
        s1,
        "Profitabilität",
        breakdown["Profitabilität"],
        35,
        "Bewertet aktuell Eigenkapitalrendite und Nettomarge.",
    )

    _plus(p1)

    _render_subscore(
        s2,
        "Wachstum",
        breakdown["Wachstum"],
        30,
        "Bewertet aktuell vor allem das Umsatzwachstum.",
    )

    _plus(p2)

    _render_subscore(
        s3,
        "Bilanz",
        breakdown["Bilanz"],
        20,
        "Bewertet aktuell hauptsächlich den Verschuldungsgrad.",
    )

    _plus(p3)

    _render_subscore(
        s4,
        "Dividende",
        breakdown["Dividende"],
        15,
        "Bewertet aktuell die Dividendenrendite.",
    )