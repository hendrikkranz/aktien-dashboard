import html

import streamlit as st

from components.opportunity_section import get_opportunity_rating
from components.quality_section import _quality_rating


def _score_ring(
    value,
    maximum,
    color,
    suffix,
):
    if value is None:
        score_text = "–"
        percentage = 0
    else:
        score_text = str(round(value))
        percentage = max(
            0,
            min(100, (float(value) / maximum) * 100),
        )

    return f"""
        <div style="
            width:126px;
            height:126px;
            border-radius:50%;
            background:
                conic-gradient(
                    {color} 0 {percentage}%,
                    rgba(148,163,184,0.13) {percentage}% 100%
                );
            display:flex;
            align-items:center;
            justify-content:center;
            position:relative;
            flex-shrink:0;
            margin:18px auto 16px auto;
            box-shadow:
                0 10px 28px rgba(0,0,0,0.28),
                0 0 24px {color}18;
        ">
            <div style="
                position:absolute;
                inset:8px;
                border-radius:50%;
                background:#151b24;
                border:1px solid rgba(255,255,255,0.05);
            "></div>

            <div style="
                position:relative;
                z-index:1;
                text-align:center;
            ">
                <div style="
                    color:#f8fafc;
                    font-size:2.05rem;
                    line-height:1;
                    font-weight:800;
                    letter-spacing:-0.04em;
                ">
                    {score_text}
                </div>
                <div style="
                    color:#64748b;
                    font-size:0.72rem;
                    font-weight:700;
                    margin-top:5px;
                ">
                    {suffix}
                </div>
            </div>
        </div>
    """


def _overview_card(
    number,
    title,
    score,
    maximum,
    rating,
    summary,
    color,
    footer,
    detail_key,
):
    safe_title = html.escape(str(title))
    safe_rating = html.escape(str(rating))
    safe_summary = html.escape(str(summary))
    safe_footer = html.escape(str(footer))

    ring = _score_ring(
        value=score,
        maximum=maximum,
        color=color,
        suffix=f"/ {maximum}",
    )

    active_detail = st.session_state.get(
        "analysis_overview_detail"
    )
    is_active = active_detail == detail_key

    if is_active:
        card_border = color
        active_shadow = (
            f"0 18px 42px rgba(0,0,0,0.34), "
            f"0 0 28px {color}28"
        )
    else:
        card_border = "rgba(148,163,184,0.17)"
        active_shadow = "0 14px 34px rgba(0,0,0,0.24)"

    st.html(
        f"""
        <div class="inra-overview-card" style="
            --accent:{color};
            min-height:505px;
            height:505px;
            box-sizing:border-box;
            display:flex;
            flex-direction:column;
            background:
                linear-gradient(
                    145deg,
                    rgba(31,41,55,0.96),
                    rgba(15,23,42,0.98)
                );
            border:1px solid {card_border};
            border-top:3px solid {color};
            border-radius:16px;
            padding:24px 26px 22px 26px;
            box-shadow:
                {active_shadow},
                inset 0 1px 0 rgba(255,255,255,0.025);
        ">
            <div style="
                display:flex;
                justify-content:space-between;
                align-items:center;
            ">
                <div style="
                    color:#64748b;
                    font-size:0.72rem;
                    font-weight:800;
                    letter-spacing:0.14em;
                ">
                    {number} / 03
                </div>

                <div style="
                    width:8px;
                    height:8px;
                    border-radius:50%;
                    background:{color};
                    box-shadow:0 0 12px {color};
                "></div>
            </div>

            <div style="
                color:#f8fafc;
                font-size:1.08rem;
                font-weight:800;
                margin-top:14px;
                letter-spacing:-0.015em;
                text-align:center;
            ">
                {safe_title}
            </div>

            {ring}

            <div style="
                color:{color};
                font-size:0.90rem;
                font-weight:750;
                min-height:22px;
                text-align:center;
            ">
                {safe_rating}
            </div>

            <div style="
                color:#a8b2c1;
                font-size:0.86rem;
                line-height:1.55;
                margin:13px auto 0 auto;
                height:96px;
                max-width:330px;
                text-align:center;
                padding-bottom:0;
                box-sizing:border-box;
            ">
                {safe_summary}
            </div>

            <div style="
                border-top:1px solid rgba(148,163,184,0.14);
                margin-top:0;
                padding-top:32px;
                color:#718096;
                font-size:0.72rem;
                line-height:1.45;
            ">
                {safe_footer}
            </div>
        </div>
        """
    )

    if score is None:
        score_label = "–"
    else:
        score_label = str(round(score))

    button_label = (
        f"Warum {score_label} von {maximum} Punkten?"
    )

    if st.button(
        button_label,
        key=f"overview_detail_{detail_key}",
        use_container_width=True,
    ):
        if is_active:
            st.session_state["analysis_overview_detail"] = None
        else:
            st.session_state["analysis_overview_detail"] = detail_key

        st.rerun()

    if is_active:
        st.markdown(
            f"""
            <div style="
                display:flex;
                flex-direction:column;
                align-items:center;
                margin:-4px auto -24px auto;
            ">
                <div style="
                    width:2px;
                    height:22px;
                    background:{color};
                    opacity:0.85;
                    box-shadow:0 0 8px {color}55;
                "></div>
                <div style="
                    width:0;
                    height:0;
                    border-left:12px solid transparent;
                    border-right:12px solid transparent;
                    border-top:12px solid {color};
                    filter:drop-shadow(
                        0 4px 6px rgba(0,0,0,0.25)
                    );
                "></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_analysis_overview(data: dict) -> None:
    quality_score = data.get("Unternehmensqualität")
    buy_score = data.get("Kaufchance")
    dividend_score = data.get("Dividendenstrategie Score")
    dividend_yield = data.get("Dividendenrendite")

    if quality_score is None:
        quality_rating = "Nicht bewertbar"
        quality_color = "#8b949e"
    else:
        (
            quality_rating,
            _quality_icon,
            quality_color,
        ) = _quality_rating(round(quality_score))

    quality_summary = (
        "Quantitative Unternehmensqualität als Basis, "
        "ergänzt um die qualitative Bewertung."
    )

    (
        buy_rating,
        buy_summary,
        _buy_icon,
        buy_color,
    ) = get_opportunity_rating(data)

    dividend_status = data.get("Dividendenstrategie Status")

    if dividend_status == "Keine Dividende":
        dividend_rating = "Keine Dividende"
        dividend_summary = (
            "Das Unternehmen schüttet derzeit keine Dividende aus. "
            "Die Dividendenstrategie ist daher nicht anwendbar."
        )
        dividend_color = "#64748b"
    elif dividend_score is None:
        dividend_rating = "Nicht bewertbar"
        dividend_summary = (
            "Für die Dividendenstrategie liegen derzeit "
            "nicht genügend Daten vor."
        )
        dividend_color = "#64748b"
    elif dividend_score >= 12:
        dividend_rating = "Sehr stark"
        dividend_summary = (
            "Sehr überzeugende Kombination aus Ausschüttung, "
            "Tragfähigkeit, Wachstum und Kapitalallokation."
        )
        dividend_color = "#34d399"
    elif dividend_score >= 10:
        dividend_rating = "Stark"
        dividend_summary = (
            "Überzeugende Dividendenstrategie mit insgesamt "
            "solidem Ausschüttungs- und Kapitalallokationsprofil."
        )
        dividend_color = "#34d399"
    elif dividend_score >= 6:
        dividend_rating = "Solide"
        dividend_summary = (
            "Solide Dividendenstrategie mit einzelnen "
            "Schwächen oder weniger belastbaren Teilbereichen."
        )
        dividend_color = "#fbbf24"
    else:
        dividend_rating = "Schwach"
        dividend_summary = (
            "Die Dividendenstrategie überzeugt derzeit "
            "nur eingeschränkt."
        )
        dividend_color = "#f87171"

    dividend_footer = (
        "Rendite · Tragfähigkeit · Wachstum · "
        "Kontinuität · Kapitalallokation"
    )

    if dividend_yield is not None:
        dividend_footer = (
            f"Aktuelle Rendite {dividend_yield:.1f} % · "
            + dividend_footer
        )

    st.markdown(
        """
        <div class="inra-section-header">
            <div class="inra-section-kicker">
                <span>02</span>
                ANALYSE IM ÜBERBLICK
            </div>
            <div class="inra-section-title">
                Drei strukturelle Säulen
            </div>
            <div class="inra-section-subtitle">
                Die zentralen InRA-Bewertungen auf einen Blick.
                Die vollständige Herleitung bleibt im Detail erhalten.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    columns = st.columns(3, gap="medium")

    with columns[0]:
        _overview_card(
            "01",
            "Unternehmensqualität",
            quality_score,
            100,
            quality_rating,
            quality_summary,
            quality_color,
            "Quantitativ zuerst · Qualitativ ergänzend",
            "quality",
        )

    with columns[1]:
        _overview_card(
            "02",
            "Kaufchance",
            buy_score,
            100,
            buy_rating,
            buy_summary,
            buy_color,
            (
                "Kursbewertung · Technische Verfassung · "
                "Entry Setup · Event Impact"
            ),
            "opportunity",
        )

    with columns[2]:
        _overview_card(
            "03",
            "Dividendenstrategie",
            dividend_score,
            15,
            dividend_rating,
            dividend_summary,
            dividend_color,
            dividend_footer,
            "dividend",
        )
