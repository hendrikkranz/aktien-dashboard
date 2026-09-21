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
from utils.data_loader import update_stock_in_benchmark_cache

from utils.fundamental_interpreter import (
    interpret_momentum,
    interpret_rsi,
)

from modules.opportunity_score import (
    calculate_opportunity_breakdown,
    get_pe_valuation_class,
)

from modules.chart_score import (
    calculate_chart_breakdown,
    calculate_chart_available_maximum,
    calculate_chart_score,
)
from utils.current_intelligence import (
    get_current_intelligence,
    research_current_intelligence_with_gemini,
    save_current_intelligence,
)

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
        "KGV vs. Branche": "siehe Branchenvergleich",
        "Branchenbewertung historisch": "siehe Branchenvergleich",
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
            "Bewertet den Abstand zum durchschnittlichen Analystenziel: "
            "unter 0 % = 0, ab 0 % = 3, ab 5 % = 7, "
            "ab 10 % = 12, ab 15 % = 17, ab 20 % = 21 "
            "und ab 30 % = 25 Punkte."
        ),
        "Forward KGV": (
            "Bewertet die KGVs der beiden nächsten verfügbaren "
            "Geschäftsjahre anhand der Bewertungsgruppe "
            "(NIEDRIG, STANDARD oder WACHSTUM). "
            "Das nähere Geschäftsjahr wird mit 60 %, das folgende "
            "mit 40 % gewichtet. Maximal 24 Punkte."
        ),
        "KGV vs. Branche": (
            "Vergleicht das für die KGV-Bewertung verwendete "
            "Aktien-KGV mit dem aktuellen Forward KGV der "
            "zugeordneten Damodaran-Branche. Sind beide "
            "Geschäftsjahre verfügbar, wird das Aktien-KGV "
            "zu 60 % aus dem näheren und zu 40 % aus dem "
            "folgenden Geschäftsjahr gebildet. Maximal 3 Punkte."
        ),
        "Branchenbewertung historisch": (
            "Vergleicht das aktuelle Branchen-KGV mit dem "
            "historischen Median der Jahre 2015 bis 2025. "
            "Maximal 3 Punkte."
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
        + calculate_chart_available_maximum(data)
    )
    base_buy_score = data.get(
        "Kaufchance Basis",
        data.get("Kaufchance"),
    )
    display_base_score = round(base_buy_score)
    display_buy_score = round(data["Kaufchance"])
    event_impact = data.get("Event Impact", 0)

    chart_available_maximum = (
        calculate_chart_available_maximum(data)
    )
    fundamental_available_maximum = sum(
        item["Maximum"]
        for item in breakdown
        if item["Punkte"] is not None
    )
    chart_only_missing = (
        chart_available_maximum == 0
        and fundamental_available_maximum == 55
    )

    if available_maximum == 100 or chart_only_missing:
        expander_title = (
            f"Warum {display_base_score} von "
            f"100 Basispunkten?"
        )
    else:
        expander_title = (
            f"Warum {display_base_score} von "
            f"{available_maximum} verfügbaren Basispunkten?"
        )

    with st.expander(expander_title):

        if chart_only_missing:
            fundamental_score = sum(
                item["Punkte"]
                for item in breakdown
                if item["Punkte"] is not None
            )
            st.markdown(
                f"**Basisbewertung:** "
                f"{round(fundamental_score)} / 55 Fundamentpunkte "
                f"+ 22 / 45 neutraler Chart-Ersatzwert "
                f"= **{display_base_score} / 100**"
            )
            st.caption(
                "Die 22 Chartpunkte sind kein gemessener Chartscore. "
                "Sie werden neutral angesetzt, solange die "
                "Kurshistorie für eine belastbare Chartbewertung "
                "nicht ausreicht."
            )

        if event_impact:
            impact_display = (
                f"+{event_impact}"
                if event_impact > 0
                else str(event_impact)
            )
            st.markdown(
                f"**Aktuelle Kaufchance:** "
                f"{display_base_score} Basis "
                f"{impact_display} Event Impact "
                f"→ **{display_buy_score}**"
            )
            st.caption(
                "Der Event Impact ergänzt die "
                "nachfolgende Basisbewertung."
            )

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

        course_available_maximum = sum(
            item["Maximum"]
            for item in course_breakdown
            if item["Punkte"] is not None
        )

        if course_available_maximum == 0:
            course_score_display = "Nicht bewertbar"
        elif course_available_maximum < course_maximum:
            course_score_display = (
                f"{round(course_total)} / "
                f"{course_available_maximum} verfügbare Punkte"
            )
        else:
            course_score_display = (
                f"{round(course_total)} / {course_maximum}"
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

            display_criterion = (
                "KGV Geschäftsjahre"
                if criterion == "Forward KGV"
                else criterion
            )

            st.markdown(
                f"###### {display_criterion}"
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
                display_points = round(points)
                st.markdown(
                    f"{icon} **{display_points} von {maximum} Punkten**"
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

            if criterion == "Forward KGV":
                valuation_class = item.get(
                    "Bewertungsklasse"
                )

                class_labels = {
                    "NIEDRIG": "Niedrig",
                    "STANDARD": "Standard",
                    "WACHSTUM": "Wachstum",
                    "SONDERFALL": "Sonderfall",
                }

                year_0 = item.get("Geschäftsjahr +0")
                pe_0 = item.get("KGV GJ +0")
                eps_0 = item.get("EPS GJ +0")
                analysts_0 = item.get("Analysten GJ +0")
                points_0 = item.get("Punkte GJ +0")

                year_1 = item.get("Geschäftsjahr +1")
                pe_1 = item.get("KGV GJ +1")
                eps_1 = item.get("EPS GJ +1")
                analysts_1 = item.get("Analysten GJ +1")
                points_1 = item.get("Punkte GJ +1")

                if (
                    valuation_class == "SONDERFALL"
                    and pe_0 is not None
                    and pe_1 is not None
                ):
                    current_value = (
                        f"GJ {year_0}: {_format_value(pe_0)} · "
                        f"GJ {year_1}: {_format_value(pe_1)}"
                    )
                elif pe_0 is not None and pe_1 is not None:
                    current_value = (
                        f"GJ {year_0}: {_format_value(pe_0)} "
                        f"({points_0}/24 · 60 %) · "
                        f"GJ {year_1}: {_format_value(pe_1)} "
                        f"({points_1}/24 · 40 %)"
                    )
                elif pe_0 is not None:
                    current_value = (
                        f"GJ {year_0}: {_format_value(pe_0)} "
                        f"({points_0}/24)"
                    )
                elif pe_1 is not None:
                    current_value = (
                        f"GJ {year_1}: {_format_value(pe_1)} "
                        f"({points_1}/24)"
                    )
                else:
                    current_value = _format_value(
                        data.get("Forward KGV")
                    )

                if valuation_class:
                    current_value += (
                        " · Bewertungsgruppe "
                        f"{class_labels.get(valuation_class, valuation_class)}"
                    )

            elif criterion == "KGV vs. Branche":
                if item.get("Punkte") is None:
                    if valuation_class == "SONDERFALL":
                        current_value = (
                            "Nicht anwendbar bei diesem Sonderfall"
                        )
                    else:
                        current_value = "Nicht bewertbar"
                else:
                    stock_pe = item.get(
                        "Aktien KGV gewichtet"
                    )
                    industry_pe = item.get("Branchen KGV")
                    damodaran_industry = item.get(
                        "Damodaran Branche"
                    )

                    if (
                        stock_pe is not None
                        and industry_pe is not None
                    ):
                        current_value = (
                            f"{_format_value(stock_pe)} "
                            f"vs. {_format_value(industry_pe)}"
                        )

                        if damodaran_industry:
                            current_value += (
                                f" · {damodaran_industry}"
                            )
                    else:
                        current_value = "Keine Daten"

            elif criterion == "Branchenbewertung historisch":
                if item.get("Punkte") is None:
                    current_value = (
                        "Nicht anwendbar bei diesem Sonderfall"
                    )
                else:
                    industry_pe = item.get("Branchen KGV")
                    historical_median = item.get(
                        "Historischer Median"
                    )
                    historical_years = item.get(
                        "Historische Jahre"
                    )

                    if (
                        industry_pe is not None
                        and historical_median is not None
                    ):
                        current_value = (
                            f"{_format_value(industry_pe)} aktuell "
                            f"vs. {_format_value(historical_median)} "
                            f"historischer Median"
                        )

                        if historical_years:
                            current_value += (
                                f" · {historical_years} Jahre"
                            )
                    else:
                        current_value = "Keine Daten"

            else:
                current_value = values.get(
                    criterion,
                    "Keine Daten",
                )

            value_label = (
                "KGV-Bewertung"
                if criterion == "Forward KGV"
                else "Aktueller Wert"
            )

            st.caption(
                f"{value_label}: {current_value}"
            )

            if (
                criterion == "Forward KGV"
                and eps_0 is not None
                and eps_1 is not None
            ):
                analysts_0_text = (
                    f"{int(analysts_0)} Analysten"
                    if analysts_0 is not None
                    and analysts_0 == analysts_0
                    else "Analystenzahl nicht verfügbar"
                )
                analysts_1_text = (
                    f"{int(analysts_1)} Analysten"
                    if analysts_1 is not None
                    and analysts_1 == analysts_1
                    else "Analystenzahl nicht verfügbar"
                )

                st.caption(
                    f"EPS-Konsens: GJ {year_0} "
                    f"{_format_value(eps_0)} "
                    f"({analysts_0_text}) · "
                    f"GJ {year_1} {_format_value(eps_1)} "
                    f"({analysts_1_text})"
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

            if (
                criterion == "Forward KGV"
                and valuation_class == "SONDERFALL"
            ):
                explanation = (
                    "Die KGVs der verfügbaren Geschäftsjahre "
                    "werden zur Information angezeigt. Für diesen "
                    "Sonderfall erfolgt jedoch keine KGV-Bewertung "
                    "und keine 60/40-Gewichtung."
                )
            else:
                explanation = explanations.get(
                    criterion,
                    "",
                )

            st.caption(explanation)

            st.divider()

        chart_score = calculate_chart_score(data)
        chart_raw_maximum = sum(
            item["Maximum"]
            for item in chart_breakdown
            if item["Kriterium"] != "Überhitzungsgefahr"
            and item["Punkte"] is not None
        )

        if chart_score is None:
            chart_header_value = "⚪ Nicht ausreichend bewertbar"
        else:
            chart_header_value = f"{chart_score} / 45"

        st.markdown(
            f"##### 📊 Charttechnik"
            f"<span style='float:right'>"
            f"{chart_header_value}"
            f"</span>",
            unsafe_allow_html=True,
        )

        if chart_score is None:
            st.caption(
                f"Nur {chart_raw_maximum} von 45 technischen "
                "Rohpunkten sind derzeit verfügbar. "
                "Die Charttechnik ist deshalb noch nicht belastbar "
                "bewertbar. In der Basis-Kaufchance wird der "
                "Chartblock neutral mit 22 von 45 Punkten angesetzt."
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
                if points is None:
                    st.markdown(
                        "⚪ **Nicht bewertbar**"
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

            elif criterion == "Pressure Balance":
                pressure_balance = data.get("Pressure Balance")

                if pressure_balance is not None:
                    if pressure_balance >= 0.40:
                        label = "Sehr starker Kaufdruck"
                    elif pressure_balance >= 0.20:
                        label = "Starker Kaufdruck"
                    elif pressure_balance >= 0.05:
                        label = "Leichter Kaufdruck"
                    elif pressure_balance >= -0.10:
                        label = "Ausgeglichen"
                    elif pressure_balance >= -0.30:
                        label = "Leichter Verkaufsdruck"
                    elif pressure_balance >= -0.50:
                        label = "Starker Verkaufsdruck"
                    else:
                        label = "Sehr starker Verkaufsdruck"

                    st.caption(
                        "Kurs-/Volumendruck der letzten "
                        "20 Handelstage"
                    )
                    st.markdown(
                        f"**Pressure Balance: "
                        f"{pressure_balance:+.2f} · {label}**"
                    )
                    st.caption(
                        "Positive Werte zeigen überwiegenden "
                        "Kaufdruck, negative Werte überwiegenden "
                        "Verkaufsdruck. Kursbewegungen mit höherem "
                        "Handelsvolumen erhalten mehr Gewicht."
                    )
            st.divider()        

        fundamental_total = sum(
            item["Punkte"]
            for item in breakdown
            if item["Punkte"] is not None
        )

        chart_score = calculate_chart_score(data)

        total = fundamental_total
        if chart_score is not None:
            total += chart_score

        available_maximum = sum(
            item["Maximum"]
            for item in breakdown
            if item["Punkte"] is not None
        ) + calculate_chart_available_maximum(data)

        coverage = round(
            available_maximum / 100 * 100
        )

        st.divider()

        if chart_only_missing:
            st.markdown(
                f"**Tatsächlich bewertet: "
                f"{round(fundamental_total)} / 55 Fundamentpunkte**"
            )
            st.caption(
                "Charttechnik: noch nicht belastbar bewertbar · "
                "neutraler Ersatzwert 22 / 45 · "
                f"Basis-Kaufchance {display_base_score} / 100"
            )
        else:
            st.markdown(
                f"**Aktuell bewertet: {round(total)} von "
                f"{available_maximum} verfügbaren Punkten**"
            )
            st.caption(
                f"Datenabdeckung: {coverage} %"
            )

def _render_current_intelligence(data: dict) -> None:
    ticker = data.get("Ticker")
    company_name = (
        data.get("Name")
        or data.get("Unternehmen")
        or ticker
        or "Unbekannt"
    )

    preview_key = f"current_intelligence_preview_{ticker}"

    st.markdown("### ⚡ Aktuelle Entwicklungen")

    st.caption(
        "Aktuelle Nachrichten und strategische Entwicklungen ergänzen "
        "die bestehende Kaufchance. Der validierte Event Impact fließt "
        "als begrenzter Zu- oder Abschlag ein."
    )

    if st.button(
        "🔄 Aktuelle Entwicklungen analysieren "
        "(API-Kosten: ca. 1–2 Ct.)",
        key=f"current_intelligence_update_{ticker}",
    ):
        try:
            with st.spinner(
                "Aktuelle Entwicklungen werden recherchiert und bewertet …"
            ):
                opportunity_breakdown = (
                    calculate_opportunity_breakdown(data)
                )
                chart_breakdown = calculate_chart_breakdown(data)

                chart_points = sum(
                    item["Punkte"]
                    for item in chart_breakdown
                    if item.get("Punkte") is not None
                )

                chart_maximum = sum(
                    item["Maximum"]
                    for item in chart_breakdown
                    if item.get("Maximum") is not None
                )

                inra_context = {
                    "Unternehmensqualität": data.get(
                        "Unternehmensqualität"
                    ),
                    "Qualitative Quality": data.get(
                        "Qualitative Quality"
                    ),
                    "Kaufchance Basis": data.get(
                        "Kaufchance Basis",
                        data.get("Kaufchance"),
                    ),
                    "Analystenpotenzial Prozent": data.get(
                        "Analystenpotenzial"
                    ),
                    "Forward KGV": data.get("Forward KGV"),
                    "Charttechnik Punkte": chart_points,
                    "Charttechnik Maximum": chart_maximum,
                    "Momentum 3M Prozent": data.get("Momentum 3M"),
                    "Momentum 6M Prozent": data.get("Momentum 6M"),
                    "Momentum 12M Prozent": data.get("Momentum 12M"),
                    "RSI 14": data.get("RSI 14"),
                    "Abstand 52W Hoch Prozent": data.get(
                        "Abstand 52W Hoch"
                    ),
                    "Pressure Balance": data.get(
                        "Pressure Balance"
                    ),
                    "Kaufchance Breakdown": opportunity_breakdown,
                    "Charttechnik Breakdown": chart_breakdown,
                }

                result = research_current_intelligence_with_gemini(
                    api_key=st.secrets["GEMINI_API_KEY"],
                    tavily_api_key=st.secrets["TAVILY_API_KEY"],
                    ticker=ticker,
                    company_name=company_name,
                    sector=data.get("Sektor"),
                    industry=data.get("Branche"),
                    momentum_3m=data.get("Momentum 3M"),
                    momentum_6m=data.get("Momentum 6M"),
                    inra_context=inra_context,
                )

            st.session_state[preview_key] = result

        except Exception as exc:
            st.error(
                "Die aktuellen Entwicklungen konnten nicht "
                f"analysiert werden: {exc}"
            )
            return

    saved_result = get_current_intelligence(ticker)
    preview_result = st.session_state.get(preview_key)

    if (
        preview_result is not None
        and str(
            preview_result.get("Ticker") or ""
        ).strip().upper()
        == str(ticker or "").strip().upper()
    ):
        result = preview_result
        is_preview = True
    else:
        result = saved_result
        is_preview = False

    if not result:
        st.caption(
            "Noch keine aktuelle Nachrichtenanalyse gespeichert."
        )
        return

    if is_preview:
        st.info(
            "Neue Current-Intelligence-Recherche – "
            "noch nicht gespeichert"
        )

    analysis_date = result.get("Analyse_Datum")

    if analysis_date:
        st.caption(
            f"Stand: {_format_date_de(analysis_date)}"
        )

    movement = result.get("Kursbewegung") or {}

    st.markdown("#### 📈 Was bewegt die Aktie?")

    if movement.get("Beschreibung"):
        st.write(movement["Beschreibung"])

    causes = movement.get("Ursachen") or []

    if causes:
        for index, cause in enumerate(causes[:2], start=1):
            st.markdown(f"**{index}.** {cause}")

    movement_meta = []

    if movement.get("Zeitraum"):
        movement_meta.append(movement["Zeitraum"])

    if movement.get("Sicherheit"):
        movement_meta.append(
            f"Einordnung: {movement['Sicherheit']}"
        )

    if movement_meta:
        st.caption(" · ".join(movement_meta))

    positive = result.get("Positive_Entwicklungen") or []
    negative = result.get("Negative_Entwicklungen") or []

    col_positive, col_negative = st.columns(2)

    with col_positive:
        st.markdown("#### 🟢 Rückenwind")

        if not positive:
            st.caption(
                "Aktuell kein wesentlicher neuer Rückenwind."
            )

        for index, item in enumerate(positive, start=1):
            st.markdown(
                f"**{index}. {item.get('Titel', 'Entwicklung')}**"
            )

            if item.get("Beschreibung"):
                st.write(item["Beschreibung"])

    with col_negative:
        st.markdown("#### 🔴 Gegenwind")

        if not negative:
            st.caption(
                "Aktuell kein wesentlicher neuer Gegenwind."
            )

        for index, item in enumerate(negative, start=1):
            st.markdown(
                f"**{index}. {item.get('Titel', 'Entwicklung')}**"
            )

            if item.get("Beschreibung"):
                st.write(item["Beschreibung"])

    open_factors = result.get("Offene_Faktoren") or []

    if open_factors:
        st.markdown("#### 👀 Darauf kommt es jetzt an")

        for index, item in enumerate(open_factors, start=1):
            title = item.get(
                "Titel",
                "Offener Faktor",
            )
            description = item.get("Beschreibung")

            st.markdown(f"**{index}. {title}**")

            if description:
                st.write(description)

    impact = result.get("Event_Impact_Vorschlag", 0)

    if impact > 0:
        impact_label = f"+{impact}"
        impact_icon = "🟢"
    elif impact < 0:
        impact_label = str(impact)
        impact_icon = "🔴"
    else:
        impact_label = "0"
        impact_icon = "⚪"

    if impact == 0:
        st.markdown("#### ⚪ Event Impact = 0")
        st.caption(
            "Nachrichtenlage verändert die Kaufchance nicht."
        )
    else:
        st.markdown(
            f"#### {impact_icon} Event Impact: "
            f"{impact_label} Punkte"
        )

        if result.get("Event_Impact_Begruendung"):
            st.write(result["Event_Impact_Begruendung"])

    source_count = result.get("Verwendbare_Quellen")
    strong_count = result.get("Starke_Quellen")
    source_status = result.get("Event_Impact_Status")

    source_parts = []

    if source_status:
        source_parts.append(source_status)

    if source_count is not None:
        source_parts.append(
            f"{source_count} verwendbare Quellen"
        )

    if strong_count is not None:
        source_parts.append(
            f"{strong_count} starke Quellen"
        )

    if source_parts:
        st.caption(" · ".join(source_parts))

    if is_preview:
        if st.button(
            "Neue Analyse übernehmen",
            key=f"save_current_intelligence_{ticker}",
            type="primary",
        ):
            save_current_intelligence(result)
            update_stock_in_benchmark_cache(ticker)
            del st.session_state[preview_key]
            st.rerun()


def render_opportunity_section(
    data: dict,
) -> None:

    buy_score = data["Kaufchance"]
    opportunity_breakdown = calculate_opportunity_breakdown(data)

    chart_breakdown = calculate_chart_breakdown(data)

    available_maximum = sum(
        item["Maximum"]
        for item in opportunity_breakdown
        if item["Punkte"] is not None
    ) + calculate_chart_available_maximum(data)

    coverage = round(
        available_maximum / 100 * 100
    )

    chart_available = (
        calculate_chart_available_maximum(data) > 0
    )
    fundamental_available_maximum = sum(
        item["Maximum"]
        for item in opportunity_breakdown
        if item["Punkte"] is not None
    )
    chart_only_missing = (
        not chart_available
        and fundamental_available_maximum == 55
    )

    if (
        coverage < 100
        and get_pe_valuation_class(data) == "SONDERFALL"
    ):
        rating = "Bewertung als Sonderfall"
        icon = "⚪"
        border = "#8b949e"
        explanation = (
            "Die KGV-basierte Kursbewertung ist für diesen "
            "Unternehmenstyp methodisch nicht anwendbar. "
            f"Die Kaufchance basiert daher auf "
            f"{available_maximum} statt 100 möglichen Punkten."
        )

    elif coverage < 100 and not chart_only_missing:
        rating = "Eingeschränkt bewertbar"
        icon = "⚪"
        border = "#8b949e"
        explanation = (
            f"Für die Kaufchance sind derzeit nur "
            f"{coverage} % der vorgesehenen Daten verfügbar."
        )

    elif buy_score >= 68:
        rating = "Attraktiv"
        icon = "🟢"
        border = "#2EAD7B"
        if chart_only_missing:
            explanation = (
                "Die bewertbaren Faktoren ergeben eine attraktive "
                "Einstiegssituation. Die Charttechnik ist wegen "
                "unzureichender Kurshistorie noch nicht belastbar "
                "bewertbar."
            )
        else:
            explanation = (
                "Die aktuelle Einstiegssituation erscheint attraktiv. "
                "Die Kaufchance berücksichtigt Bewertung, "
                "Analystenpotenzial und Charttechnik."
            )

    elif buy_score >= 51:
        rating = "Neutral"
        icon = "🟡"
        border = "#D9A514"
        explanation = (
            "Die aktuelle Einstiegssituation ist gemischt. "
            "Positive und negative Signale halten sich "
            "noch weitgehend die Waage."
        )

    else:
        rating = "Unattraktiv"
        icon = "🔴"
        border = "#D9534F"
        explanation = (
            "Die aktuelle Einstiegssituation erscheint "
            "derzeit nicht attraktiv."
        )

    base_buy_score = data.get(
        "Kaufchance Basis",
        buy_score,
    )
    event_impact = data.get("Event Impact")
    chart_available = (
        calculate_chart_available_maximum(data) > 0
    )

    display_score = f"{round(buy_score)} / 100"

    if (
        base_buy_score is not None
        and event_impact is not None
    ):
        impact_text = (
            f"+{event_impact}"
            if event_impact > 0
            else (
                "±0"
                if event_impact == 0
                else str(event_impact)
            )
        )

        overlay_html = f"""
    <div style="
        color:#8b949e;
        font-size:13px;
        margin-top:12px;
    ">
        Basis {round(base_buy_score)}
        · Event Impact {impact_text}
        → {round(buy_score)}
    </div>
"""
    else:
        overlay_html = ""

    if not chart_available:
        overlay_html += """
    <div style="
        color:#8b949e;
        font-size:13px;
        margin-top:6px;
    ">
        Charttechnik noch nicht belastbar bewertbar.
        Der fehlende 45-Punkte-Block wird für die Kaufchance
        neutral mit 22 Punkten angesetzt.
    </div>
"""

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
        {display_score}
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

    {overlay_html}
</div>
"""

    st.html(card)

    _render_opportunity_breakdown(
        data,
        rating,
    )

    _render_current_intelligence(data)
