from datetime import datetime

def _format_date_de(value: str) -> str:
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).strftime("%d.%m.%Y")
    except (TypeError, ValueError):
        return value or "unbekannt"

from typing import Optional

def _is_manual_data_stale(
    value: str,
    max_age_days: int = 90,
) -> bool:
    try:
        data_date = datetime.strptime(
            value,
            "%Y-%m-%d",
        )
    except (TypeError, ValueError):
        return False

    age_days = (datetime.now() - data_date).days
    return age_days > max_age_days

import streamlit as st

from utils.market_data import save_manual_override

from utils.fundamental_interpreter import (
    interpret_momentum,
    interpret_rsi,
)

from modules.opportunity_score import calculate_opportunity_breakdown

from modules.chart_score import calculate_chart_breakdown

def _format_value(
    value: Optional[float],
    suffix: str = "",
) -> str:
    if value is None:
        return "Keine Daten"

    return f"{value:.1f}{suffix}"


def _format_momentum(
    value: Optional[float],
) -> str:
    if value is None:
        return "–"

    return f"{value:+.1f} %"


def _momentum_icon(
    result: Optional[dict],
) -> str:
    if result is None:
        return "⚪"

    level = result.get("level")

    if level in ("excellent", "good"):
        return "🟢"

    if level == "solid":
        return "🟡"

    return "🔴"


def _momentum_label(
    result: Optional[dict],
) -> str:
    if result is None:
        return "Keine Einordnung"

    mapping = {
        "excellent": "Sehr stark",
        "good": "Stark",
        "solid": "Positiv",
        "weak": "Schwach",
        "poor": "Sehr schwach",
    }

    return mapping.get(
        result.get("level"),
        "Keine Einordnung",
    )


def _render_opportunity_breakdown(
    data: dict,
    rating: str,
) -> None:

    breakdown = data.get(
        "Opportunity Breakdown",
        [],
    )

    chart_breakdown = calculate_chart_breakdown(data)

    analyst_target_missing = (
        data.get("Analystenziel") is None
    )

    forward_pe_missing = (
        data.get("Forward KGV") is None
    )

    values = {
        "Analystenpotenzial": _format_value(
            data.get("Analystenpotenzial"),
            " %",
        ),
        "Forward KGV": _format_value(
            data.get("Forward KGV"),
        ),
        "Dividendenstrategie": (
            "Keine Daten"
            if data.get("Dividendenrendite") is None
            else (
                "0,0 % (keine Dividende)"
                if data.get("Dividendenrendite") == 0
                else _format_value(
                    data.get("Dividendenrendite"),
                    " %",
                )
            )
        ),
        "Abstand 52W-Hoch": _format_value(
            data.get("Abstand 52W Hoch"),
            " %",
        ),
    }

    explanations = {
        "Analystenpotenzial": (
            "Ab 20 % wird die volle Punktzahl vergeben, "
            "ab 10 % eine reduzierte Punktzahl."
        ),
        "Forward KGV": (
            "Bis 20 werden 30 Punkte vergeben. "
            "Bis 22 gibt es 17 Punkte, "
            "bis 25 noch 14 Punkte, "
            "bis 30 noch 8 Punkte "
            "und über 30 keine Punkte."
        ),
        "Abstand 52W-Hoch": (
            "Je näher der Kurs am 52-Wochen-Hoch liegt, "
            "desto mehr Punkte werden vergeben."
        ),
    }

    available_maximum = (
        sum(
            item["Maximum"]
            for item in breakdown
            if item["Punkte"] is not None
        )
        + sum(
            item["Maximum"]
            for item in chart_breakdown
        )
    )

    if available_maximum == 100:
        expander_title = (
            f"Warum {data['Kaufchance']} von 100 Punkten?"
        )
    else:
        expander_title = (
            f"Warum {data['Kaufchance']} von "
            f"{available_maximum} verfügbaren Punkten?"
        )

    with st.expander(expander_title):

        course_breakdown = breakdown

        course_total = sum(
            item["Punkte"]
            for item in course_breakdown
            if item["Punkte"] is not None
        )

        course_maximum = sum(
            item["Maximum"]
            for item in course_breakdown
        )

        course_score_display = (
            "Nicht bewertbar"
            if all(
                item["Punkte"] is None
                for item in course_breakdown
            )
            else f"{course_total} / {course_maximum}"
        )

        st.markdown(
            f"##### 💰 Kursbewertung"
            f"<span style='float:right'>"
            f"{course_score_display}"
            f"</span>",
            unsafe_allow_html=True,
        )

        for item in course_breakdown:

            criterion = item["Kriterium"]
            points = item["Punkte"]
            maximum = item["Maximum"]

            if points is None:
                icon = "⚪"
            elif points >= maximum:
                icon = "🟢"
            elif points > 0:
                icon = "🟡"
            else:
                icon = "🔴"

            st.markdown(
                f"###### {criterion}"
            )

            if points is None:
                st.markdown(
                    f"{icon} **Nicht bewertbar**"
                )
            elif points < 0:
                st.markdown(
                    f"{icon} **{points} Punkte**"
                )
            else:
                st.markdown(
                    f"{icon} **{points} von {maximum} Punkten**"
            )

            if criterion == "Langfristiger Trend":
                st.caption("Trendanalyse")

                st.markdown(
                    f"**Trend: "
                    f"{data.get('Langfristiger Trend', 'Keine Daten')}**"
                )

                st.markdown(
                    f"**Validität: "
                    f"{data.get('Langfristiger Trend Confidence', 'Keine Daten')}**"
                )

                st.caption(
                    data.get(
                        "Langfristiger Trend Erklärung",
                        "",
                    )
                )

            st.caption(
                f"Aktueller Wert: "
                f"{values.get(criterion, 'Keine Daten')}"
            )

            if (
                criterion == "Analystenpotenzial"
                and data.get("Analystenziel manuell")
            ):
                metadata = data.get(
                    "Analystenziel Metadaten",
                    {},
                )

                st.caption(
                    f"Manuelle Ergänzung des Analystenziels · "
                    f"{metadata.get('Quelle', 'Quelle unbekannt')} · "
                    f"Stand {_format_date_de(metadata.get('Stand'))}"
                )

                if _is_manual_data_stale(
                    metadata.get("Stand")
                ):
                    st.warning(
                        "⚠️ Datenstand älter als 90 Tage."
                    )

            elif (
                criterion == "Forward KGV"
                and data.get("Forward KGV manuell")
            ):
                metadata = data.get(
                    "Forward KGV Metadaten",
                    {},
                )

                st.caption(
                    f"Manuelle Ergänzung · "
                    f"{metadata.get('Quelle', 'Quelle unbekannt')} · "
                    f"Stand {_format_date_de(metadata.get('Stand'))}"
                )

                if _is_manual_data_stale(
                    metadata.get("Stand")
                ):
                    st.warning(
                        "⚠️ Datenstand älter als 90 Tage."
                    )

            if (
                criterion == "Analystenpotenzial"
                and analyst_target_missing
            ):
                with st.expander(
                    "Analystenziel manuell ergänzen"
                ):
                    manual_analyst_target = st.number_input(
                        "Analystenziel",
                        min_value=0.0,
                        step=0.1,
                        key="manual_analyst_target",
                    )

                    manual_analyst_currency = st.text_input(
                        "Währung des Analystenziels",
                        value=data.get("Währung") or "",
                        key="manual_analyst_currency",
                    )

                    manual_analyst_source = st.text_input(
                        "Quelle",
                        key="manual_analyst_source",
                    )

                    manual_analyst_date = st.date_input(
                        "Stand",
                        key="manual_analyst_date",
                    )

                    if st.button(
                        "Analystenziel speichern",
                        key="save_manual_analyst_target",
                    ):
                        if (
                            manual_analyst_target <= 0
                            or not manual_analyst_source.strip()
                            or (
                                manual_analyst_currency.strip().upper()
                                != str(
                                    data.get("Währung") or ""
                                ).upper()
                            )
                        ):
                            if (
                                manual_analyst_currency.strip().upper()
                                != str(
                                    data.get("Währung") or ""
                                ).upper()
                            ):
                                st.error(
                                    "Die Währung des Analystenziels muss "
                                    "mit der InRA-Währung übereinstimmen."
                                )
                            else:
                                st.error(
                                    "Bitte Wert und Quelle "
                                    "vollständig angeben."
                                )
                        else:
                            save_manual_override(
                                ticker=data["Ticker"],
                                field="Analystenziel",
                                value=manual_analyst_target,
                                date=manual_analyst_date.isoformat(),
                                source=manual_analyst_source.strip(),
                            )

                            st.rerun()

            if (
                criterion == "Forward KGV"
                and forward_pe_missing
            ):
                with st.expander(
                    "Forward KGV manuell ergänzen"
                ):
                    manual_forward_pe = st.number_input(
                        "Forward KGV",
                        min_value=0.0,
                        step=0.1,
                        key="manual_forward_pe",
                    )

                    manual_forward_pe_source = st.text_input(
                        "Quelle",
                        key="manual_forward_pe_source",
                    )

                    manual_forward_pe_date = st.date_input(
                        "Stand",
                        key="manual_forward_pe_date",
                    )

                    if st.button(
                        "Forward KGV speichern",
                        key="save_manual_forward_pe",
                    ):
                        if (
                            manual_forward_pe <= 0
                            or not manual_forward_pe_source.strip()
                        ):
                            st.error(
                                "Bitte Wert und Quelle "
                                "vollständig angeben."
                            )
                        else:
                            save_manual_override(
                                ticker=data["Ticker"],
                                field="Forward KGV",
                                value=manual_forward_pe,
                                date=manual_forward_pe_date.isoformat(),
                                source=manual_forward_pe_source.strip(),
                            )

                            st.rerun()

            st.caption(
                explanations.get(criterion, "")
            )

            st.divider()

        chart_total = sum(
            item["Punkte"]
            for item in chart_breakdown
        )

        chart_maximum = sum(
            item["Maximum"]
            for item in chart_breakdown
        )

        st.markdown(
            f"##### 📊 Charttechnik"
            f"<span style='float:right'>"
            f"{chart_total} / {chart_maximum}"
            f"</span>",
            unsafe_allow_html=True,
        )

        for item in chart_breakdown:

            criterion = item["Kriterium"]
            points = item["Punkte"]
            maximum = item["Maximum"]

            placeholder_criteria = set()

            st.markdown(
                f"###### {criterion}"
            )

            if criterion in placeholder_criteria:
                st.markdown(
                    "⚪ **Noch nicht bewertet**"
                )
                st.caption(
                    "Dieser Baustein wird in V2 ergänzt."
                )

            elif criterion == "Überhitzungsgefahr":
                if points == 0:
                    icon = "🟢"
                    label = "Keine Überhitzungsgefahr"
                elif points == -2:
                    icon = "🟡"
                    label = "Leicht erhöht"
                elif points == -4:
                    icon = "🟠"
                    label = "Erhöht"
                else:
                    icon = "🔴"
                    label = "Sehr hoch"

                if points == 0:
                    st.markdown(
                        f"{icon} **{label} · kein Punktabzug**"
                    )
                else:
                    st.markdown(
                        f"{icon} **{label} · {points} Punkte**"
                    )
                st.caption(
                    "Bewertung aus RSI, Abstand zum 52W-Hoch "
                    "und Momentum 3M / 6M / 12M."
                )
            else:
                if points >= maximum:
                    icon = "🟢"
                elif points > 0:
                    icon = "🟡"
                else:
                    icon = "🔴"

                if points < 0:
                    st.markdown(
                        f"{icon} **{points} Punkte**"
                    )
                else:
                    st.markdown(
                        f"{icon} **{points} von "
                        f"{maximum} Punkten**"
                    )

            if criterion == "Langfristiger Trend":
                st.caption("Trendanalyse")

                st.markdown(
                    f"**Trend: "
                    f"{data.get('Langfristiger Trend', 'Keine Daten')}**"
                )

                st.markdown(
                    f"**Validität: "
                    f"{data.get('Langfristiger Trend Confidence', 'Keine Daten')}**"
                )

                st.caption(
                    data.get(
                        "Langfristiger Trend Erklärung",
                        "",
                    )
                )

                st.caption(
                    f"Kanalposition: "
                    f"{data.get('Trendkanal Position', 'Keine Daten')} · "
                    f"{data.get('Trendkanal Position Normalisiert', 'Keine Daten')}"
                )

            if criterion == "Momentum":
                momentum_3m = data.get("Momentum 3M")
                momentum_6m = data.get("Momentum 6M")
                momentum_12m = data.get("Momentum 12M")

                m1, m2, m3 = st.columns(3)

                with m1:
                    st.caption("3 Monate")
                    st.markdown(
                        f"**{_format_momentum(momentum_3m)}**"
                    )

                with m2:
                    st.caption("6 Monate")
                    st.markdown(
                        f"**{_format_momentum(momentum_6m)}**"
                    )

                with m3:
                    st.caption("12 Monate")
                    st.markdown(
                        f"**{_format_momentum(momentum_12m)}**"
                    )

            elif criterion == "RSI":
                rsi = data.get("RSI 14")

                if rsi is not None:
                    if rsi >= 70:
                        label = "Überkauft"
                    elif rsi >= 60:
                        label = "Heiß gelaufen"
                    elif rsi >= 40:
                        label = "Neutral"
                    elif rsi >= 30:
                        label = "Schwach"
                    else:
                        label = "Überverkauft"

                    st.caption("Grunddaten Relative Stärke")
                    st.markdown(
                        f"**RSI (14): {rsi:.1f} · {label}**"
                    )

            elif criterion == "Abstand 52W-Hoch":
                high_52w = data.get("52W Hoch")
                distance_52w = data.get("Abstand 52W Hoch")
                currency = data.get("Währung", "")

                c1, c2 = st.columns(2)

                with c1:
                    st.caption("52W-Hoch")
                    st.markdown(
                        (
                            f"**{high_52w:.2f} {currency}**"
                            if high_52w is not None
                            else "**Keine Daten**"
                        )
                    )

                with c2:
                    st.caption("Abstand")
                    st.markdown(
                        (
                            f"**{distance_52w:+.1f} %**"
                            if distance_52w is not None
                            else "**Keine Daten**"
                        )
                    )

            st.divider()        

        fundamental_total = sum(
            item["Punkte"]
            for item in breakdown
            if item["Punkte"] is not None
        )

        chart_total = sum(
            item["Punkte"]
            for item in chart_breakdown
        )

        total = fundamental_total + chart_total

        available_maximum = sum(
            item["Maximum"]
            for item in breakdown
            if item["Punkte"] is not None
        ) + sum(
            item["Maximum"]
            for item in chart_breakdown
        )

        coverage = round(
            available_maximum / 100 * 100
        )

        st.divider()

        st.markdown(
            f"**Aktuell bewertet: {total} von {available_maximum} verfügbaren Punkten**"
        )

        st.caption(
            f"Datenabdeckung: {coverage} %"
        )

def render_opportunity_section(
    data: dict,
) -> None:

    buy_score = data["Kaufchance"]
    opportunity_breakdown = calculate_opportunity_breakdown(data)

    available_maximum = sum(
        item["Maximum"]
        for item in opportunity_breakdown
        if item["Punkte"] is not None
    ) + 45

    coverage = round(
        available_maximum / 100 * 100
    )

    if coverage < 100:
        rating = "Eingeschränkt bewertbar"
        icon = "⚪"
        border = "#8b949e"
        explanation = (
            f"Für die Kaufchance sind derzeit nur "
            f"{coverage} % der vorgesehenen Daten verfügbar."
        )

    elif buy_score >= 68:
        rating = "Kaufen"
        icon = "🟢"
        border = "#2EAD7B"
        explanation = (
            "Der aktuelle Einstieg erscheint attraktiv. "
            "Risiken und die eigene Anlagestrategie "
            "sollten dennoch geprüft werden."
        )

    elif buy_score >= 51:
        rating = "Beobachten"
        icon = "🟡"
        border = "#D9A514"
        explanation = (
            "Die Aktie ist interessant, "
            "erfüllt derzeit aber noch nicht "
            "alle Voraussetzungen für "
            "eine klare Kaufempfehlung."
        )

    else:
        rating = "Abwarten"
        icon = "🔴"
        border = "#D9534F"
        explanation = (
            "Der aktuelle Einstieg erscheint "
            "momentan nicht attraktiv genug."
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
        Kaufchance
    </div>

    <div style="
        color:white;
        font-size:32px;
        font-weight:700;
        margin-top:10px;
    ">
        {buy_score} / {available_maximum}
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
    ">
        {explanation}
    </div>
</div>
"""

    st.html(card)

    _render_opportunity_breakdown(
        data,
        rating,
    )