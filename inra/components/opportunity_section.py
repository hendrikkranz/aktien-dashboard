from datetime import datetime
import textwrap

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

from utils.market_data import (
    load_price_history,
    save_manual_override,
)
from utils.data_loader import update_stock_in_benchmark_cache

from utils.fundamental_interpreter import (
    interpret_momentum,
    interpret_rsi,
)

from modules.opportunity_score import (
    calculate_opportunity_breakdown,
    calculate_opportunity_v3_blocks,
    get_pe_valuation_class,
)

from modules.chart_score import (
    calculate_technical_condition_v3_breakdown,
)
from utils.current_intelligence import (
    detect_significant_price_moves,
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

    if level == "neutral":
        return "⚪"

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
        "neutral": "Neutral",
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
            "Bewertet den Abstand zum durchschnittlichen Analystenziel. "
            "In Kaufchance V3 wird die Analystenlogik proportional auf "
            "maximal 15 Punkte skaliert: unter 0 % = 0, "
            "ab 0 % = 1,8, ab 5 % = 4,2, ab 10 % = 7,2, "
            "ab 15 % = 10,2, ab 20 % = 12,6 und "
            "ab 30 % = 15 Punkte."
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

    v3_blocks = calculate_opportunity_v3_blocks(data)
    available_maximum = v3_blocks["available_maximum"]

    base_buy_score = data.get(
        "Kaufchance Basis",
        data.get("Kaufchance"),
    )
    display_base_score = round(base_buy_score)
    display_buy_score = round(data["Kaufchance"])
    event_impact = data.get("Event Impact", 0)

    fundamental_available_maximum = (
        v3_blocks["fundamental_available"]
    )
    technical_missing = (
        v3_blocks["technical_available"] == 0
    )
    entry_missing = (
        v3_blocks["entry_available"] == 0
    )
    technical_only_missing = (
        technical_missing
        and not entry_missing
        and fundamental_available_maximum == 45
    )

    if (
        available_maximum == 100
        or technical_only_missing
        or v3_blocks["technical_neutral"]
        or v3_blocks["entry_neutral"]
    ):
        expander_title = (
            f"Warum {display_base_score} von "
            f"100 Basispunkten?"
        )
    else:
        expander_title = (
            f"Warum {display_base_score} von "
            f"{available_maximum} verfügbaren Basispunkten?"
        )

    # Die äußere Overview-Karte ist bereits die "Warum?"-Ebene.
    # Die Basispunkt-Herleitung folgt deshalb direkt offen.
    if available_maximum < 100:
        neutral_parts = []

        if v3_blocks["technical_neutral"]:
            neutral_parts.append(
                "Technische Verfassung 12,5 / 25 neutral"
            )

        if v3_blocks["entry_neutral"]:
            neutral_parts.append(
                "Entry Setup 15 / 30 neutral"
            )

        if neutral_parts:
            st.markdown(
                f"**Basis-Kaufchance: "
                f"{display_base_score} / 100**"
            )
            st.caption(
                "Neutral angesetzte, nicht ausreichend "
                "bewertbare Blöcke: "
                + " · ".join(neutral_parts)
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
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:16px 16px;
            margin:2px 0 14px 0;
            background:linear-gradient(
                180deg,
                #363b44 0%,
                #292d34 100%
            );
            border:1px solid #5a616c;
            border-radius:8px;
            box-shadow:0 5px 16px rgba(0,0,0,0.38);
            color:#f0f2f5;
            font-size:1.12rem;
            font-weight:700;
        ">
            <span>💰 Kursbewertung</span>
            <span>{course_score_display}</span>
        </div>
        """,
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

        valuation_class = item.get("Bewertungsklasse")

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

        score_col, method_col = st.columns(
            [1, 1.45],
            vertical_alignment="center",
        )

        with score_col:
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

        if explanation:
            method_key = (
                "valuation_method_"
                + criterion.lower()
                .replace(" ", "_")
                .replace(".", "")
            )
            with method_col:
                with st.container(key=method_key):
                    st.markdown(
                        """
                        <style>
                        div[class*="st-key-valuation_method_"] details summary {
                            padding-top: 0.2rem;
                            padding-bottom: 0.2rem;
                            font-size: 0.78rem;
                            color: rgba(250, 250, 250, 0.58);
                        }
                        div[class*="st-key-valuation_method_"] details summary * {
                            font-size: 0.78rem;
                            color: rgba(250, 250, 250, 0.58);
                        }
                        div[class*="st-key-valuation_method_"] details {
                            border: 0;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                    with st.expander("›  ⓘ Berechnung anzeigen"):
                        st.caption(explanation)

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

        elif criterion == "NTA/NAV-Bewertung":
            price = data.get("Kurs")
            nav_value = item.get("NTA/NAV je Aktie")
            nav_metric = item.get("NTA/NAV-Kennzahl")
            price_to_nav = item.get("Kurs/NTA-NAV")

            if (
                price is not None
                and nav_value is not None
                and price_to_nav is not None
            ):
                current_value = (
                    f"Kurs {_format_value(price)} · "
                    f"{nav_metric or 'NTA/NAV'} je Aktie "
                    f"{_format_value(nav_value)} · "
                    f"Kurs/{nav_metric or 'NTA/NAV'} "
                    f"{price_to_nav:.2f}"
                )
            else:
                current_value = "Nicht bewertbar"

        elif criterion == "FFO/AFFO-Bewertung":
            price = data.get("Kurs")
            earnings_metric = item.get("Ertragskennzahl")
            earnings_per_share = item.get("Ertrag je Aktie")
            earnings_period = item.get("Zeitraum")
            earnings_multiple = item.get("Kurs/FFO-AFFO")

            if (
                price is not None
                and earnings_per_share is not None
                and earnings_multiple is not None
            ):
                current_value = (
                    f"Kurs {_format_value(price)} · "
                    f"{earnings_period or 'FY Guidance'} "
                    f"{earnings_metric or 'FFO/AFFO'} je Aktie "
                    f"{_format_value(earnings_per_share)} · "
                    f"Kurs/{earnings_metric or 'FFO/AFFO'} "
                    f"{earnings_multiple:.1f}x"
                )
            else:
                current_value = "Nicht bewertbar"

        else:
            current_value = values.get(
                criterion,
                "Keine Daten",
            )

        value_label = (
            "KGV-Bewertung"
            if criterion == "Forward KGV"
            else (
                "Immobilienbewertung"
                if criterion in {
                    "NTA/NAV-Bewertung",
                    "FFO/AFFO-Bewertung",
                }
                else "Aktueller Wert"
            )
        )

        st.caption(
            f"{value_label}: {current_value}"
        )

        if criterion == "Forward KGV":
            quality_checked = item.get(
                "Ergebnisqualität geprüft",
                False,
            )
            quality_rating = item.get(
                "Ergebnisqualität"
            )
            adjustment_ratio = item.get(
                "Bereinigungsquote"
            )
            quality_penalty = item.get(
                "Ergebnisqualitäts-Abschlag",
                0,
            )

            if not quality_checked:
                st.caption(
                    "Ergebnisqualität: noch nicht auf "
                    "GAAP-/Adjusted-EPS-Differenz geprüft"
                )
            else:
                quality_parts = []

                if quality_rating is not None:
                    quality_parts.append(
                        f"{_format_value(quality_rating)}/5"
                    )

                if adjustment_ratio is not None:
                    quality_parts.append(
                        "Bereinigungsquote "
                        f"{_format_value(adjustment_ratio)} %"
                    )

                if quality_penalty > 0:
                    quality_parts.append(
                        f"Abschlag −{_format_value(quality_penalty)} "
                        f"→ {_format_value(item.get('Punkte'))}/24 Punkte"
                    )
                else:
                    quality_parts.append("kein Abschlag")

                st.caption(
                    "Ergebnisqualität: "
                    + " · ".join(quality_parts)
                )

        if (
            criterion == "NTA/NAV-Bewertung"
            and price_to_nav is not None
        ):
            difference_pct = (price_to_nav - 1) * 100

            if difference_pct < -0.5:
                st.caption(
                    f"Der Aktienkurs liegt rund "
                    f"{abs(difference_pct):.0f} % unter dem "
                    f"{nav_metric or 'NTA/NAV'} je Aktie. "
                    "Die Aktie wird damit mit einem deutlichen "
                    "Abschlag auf den ausgewiesenen Netto-Substanzwert "
                    "gehandelt."
                )
            elif difference_pct > 0.5:
                st.caption(
                    f"Der Aktienkurs liegt rund "
                    f"{difference_pct:.0f} % über dem "
                    f"{nav_metric or 'NTA/NAV'} je Aktie. "
                    "Der Markt bewertet das Unternehmen damit mit "
                    "einem Aufschlag auf den bilanziell abgeleiteten "
                    "Nettoimmobilienwert."
                )
            else:
                st.caption(
                    f"Der Aktienkurs liegt ungefähr auf Höhe des "
                    f"{nav_metric or 'NTA/NAV'} je Aktie."
                )

        if (
            criterion == "FFO/AFFO-Bewertung"
            and earnings_multiple is not None
        ):
            st.caption(
                "Bewertungsbasis: offizielle "
                "FY-2026-Unternehmensguidance."
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

        st.divider()

    # -----------------------------------------------------
    # Technische Verfassung V3 – 25 Punkte
    # -----------------------------------------------------
    technical_breakdown = (
        calculate_technical_condition_v3_breakdown(data)
    )
    technical_points = v3_blocks["technical_points"]

    if v3_blocks["technical_neutral"]:
        technical_header = "⚪ Nicht ausreichend bewertbar"
    else:
        technical_header = f"{technical_points:.1f} / 25"

    st.markdown(
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:16px 16px;
            margin:2px 0 14px 0;
            background:linear-gradient(
                180deg,
                #363b44 0%,
                #292d34 100%
            );
            border:1px solid #5a616c;
            border-radius:8px;
            box-shadow:0 5px 16px rgba(0,0,0,0.38);
            color:#f0f2f5;
            font-size:1.12rem;
            font-weight:700;
        ">
            <span>📈 Technische Verfassung</span>
            <span>{technical_header}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not v3_blocks["technical_neutral"]:
        technical_raw_points = sum(
            item["Punkte"]
            for item in technical_breakdown
            if item["Punkte"] is not None
        )
        technical_raw_maximum = sum(
            item["Maximum"]
            for item in technical_breakdown
            if item["Punkte"] is not None
        )

    technical_method_spacer, technical_method_col = st.columns(
        [1, 1.45],
        vertical_alignment="center",
    )

    with technical_method_col:
        with st.container(key="technical_method"):
            st.markdown(
                """
                <style>
                div.st-key-technical_method details summary,
                div.st-key-technical_method details summary * {
                    font-size: 0.78rem;
                    color: rgba(250, 250, 250, 0.58);
                }
                div.st-key-technical_method details {
                    border: 0;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("›  ⓘ Berechnung anzeigen"):
                st.caption(
                    "Bewertet den übergeordneten technischen Zustand "
                    "der Aktie anhand von langfristigem Trend, Momentum, "
                    "RSI, 52W-Kontext, CM MACD und Pressure Balance. "
                    "Das konkrete Einstiegstiming wird separat im "
                    "Entry Setup beurteilt."
                )
                if not v3_blocks["technical_neutral"]:
                    st.caption(
                        f"Komponentenscore: "
                        f"{technical_raw_points:.1f} / "
                        f"{technical_raw_maximum} → "
                        f"{technical_points:.1f} / 25 Kaufchance-Punkte"
                    )

    if v3_blocks["technical_neutral"]:
        st.caption(
            "Die technischen Daten reichen derzeit nicht "
            "für eine belastbare Bewertung. In der "
            "Basis-Kaufchance wird dieser Block neutral "
            "mit 12,5 von 25 Punkten angesetzt."
        )

    for item in technical_breakdown:
        criterion = item["Kriterium"]
        points = item["Punkte"]
        maximum = item["Maximum"]

        st.markdown(f"###### {criterion}")

        if points is None:
            st.markdown("⚪ **Nicht bewertbar**")
        else:
            ratio = points / maximum if maximum > 0 else 0

            if ratio >= 0.8:
                icon = "🟢"
            elif ratio >= 0.5:
                icon = "🟡"
            else:
                icon = "🔴"

            st.markdown(
                f"{icon} **{points} von "
                f"{maximum} Punkten**"
            )

        if criterion == "Langfristiger Trend":
            trend = data.get(
                "Langfristiger Trend",
                "Keine Daten",
            )
            trend_status = data.get(
                "Langfristiger Trend Status",
                "Keine Daten",
            )

            if trend_status != "Keine Daten":
                trend_status = str(
                    trend_status
                ).lower()

            trend_visual = {
                "Aufwärtstrend": {
                    "symbol": "↗",
                    "color": "#2EAD7B",
                    "label": "Aufwärtstrend",
                },
                "Seitwärtstrend": {
                    "symbol": "→",
                    "color": "#D9A514",
                    "label": "Seitwärtstrend",
                },
                "Seitwärts": {
                    "symbol": "→",
                    "color": "#D9A514",
                    "label": "Seitwärtstrend",
                },
                "Abwärtstrend": {
                    "symbol": "↘",
                    "color": "#D9534F",
                    "label": "Abwärtstrend",
                },
            }.get(
                trend,
                {
                    "symbol": "–",
                    "color": "#8b949e",
                    "label": str(trend),
                },
            )

            trend_html = (
                f'<div style="display:flex;align-items:center;'
                f'gap:10px;margin-top:4px;margin-bottom:4px;">'
                f'<div style="width:38px;height:38px;'
                f'border-radius:10px;'
                f'background:{trend_visual["color"]}18;'
                f'color:{trend_visual["color"]};'
                f'display:flex;align-items:center;'
                f'justify-content:center;font-size:1.65rem;'
                f'font-weight:700;">'
                f'{trend_visual["symbol"]}'
                f'</div>'
                f'<div>'
                f'<div style="font-size:0.88rem;'
                f'font-weight:700;color:#e6edf3;">'
                f'{trend_visual["label"]}'
                f'</div>'
                f'<div style="font-size:0.72rem;'
                f'color:#9ca3af;margin-top:1px;">'
                f'Trendstruktur · {trend_status}'
                f'</div>'
                f'</div>'
                f'</div>'
            )

            st.markdown(
                f"""
                <div style="
                    display:flex;
                    justify-content:flex-end;
                    margin-top:-38px;
                    margin-bottom:8px;
                ">
                    <div style="
                        display:flex;
                        align-items:center;
                        gap:8px;
                    ">
                        <div style="
                            width:30px;
                            height:30px;
                            border-radius:8px;
                            background:{trend_visual['color']}18;
                            color:{trend_visual['color']};
                            display:flex;
                            align-items:center;
                            justify-content:center;
                            font-size:1.35rem;
                            font-weight:700;
                        ">{trend_visual['symbol']}</div>
                        <div>
                            <div style="
                                font-size:0.86rem;
                                font-weight:700;
                                color:#e6edf3;
                                line-height:1.05;
                            ">{trend_visual['label']}</div>
                            <div style="
                                font-size:0.68rem;
                                color:#9ca3af;
                                margin-top:3px;
                            ">{trend_status} · bis zu 5 Jahre</div>
                        </div>
                    </div>
                </div>
                """.replace("\n", "").strip(),
                unsafe_allow_html=True,
            )

        elif criterion == "Momentum":
            momentum_3m = data.get("Momentum 3M")
            momentum_6m = data.get("Momentum 6M")
            momentum_12m = data.get("Momentum 12M")

            momentum_values = [
                momentum_12m,
                momentum_6m,
                momentum_3m,
            ]

            if all(
                value is not None
                for value in momentum_values
            ):
                values = [
                    float(value)
                    for value in momentum_values
                ]

                chart_min = min(
                    min(values),
                    0.0,
                )
                chart_max = max(
                    max(values),
                    0.0,
                )

                chart_range = chart_max - chart_min

                if chart_range == 0:
                    chart_range = 1.0

                padding = max(
                    chart_range * 0.18,
                    2.0,
                )

                chart_min -= padding
                chart_max += padding
                chart_range = chart_max - chart_min

                import math

                momentum_scale = max(
                    5.0,
                    min(
                        20.0,
                        max(abs(value) for value in values)
                        * 0.15,
                    ),
                )

                transformed_values = [
                    math.asinh(value / momentum_scale)
                    for value in values
                ]
                transformed_zero = 0.0

                transformed_min = min(
                    min(transformed_values),
                    transformed_zero,
                )
                transformed_max = max(
                    max(transformed_values),
                    transformed_zero,
                )

                transformed_range = (
                    transformed_max - transformed_min
                )

                if transformed_range == 0:
                    transformed_range = 1.0

                transformed_padding = max(
                    transformed_range * 0.18,
                    0.15,
                )

                transformed_min -= transformed_padding
                transformed_max += transformed_padding
                transformed_range = (
                    transformed_max - transformed_min
                )

                def momentum_y(value):
                    transformed = math.asinh(
                        value / momentum_scale
                    )
                    return (
                        8
                        + (
                            transformed_max - transformed
                        )
                        / transformed_range
                        * 54
                    )

                x_positions = [20, 150, 280]
                y_positions = [
                    momentum_y(value)
                    for value in values
                ]
                zero_y = momentum_y(0.0)

                points = " ".join(
                    f"{x},{y:.1f}"
                    for x, y in zip(
                        x_positions,
                        y_positions,
                    )
                )

                circles = "".join(
                    (
                        f'<circle cx="{x}" cy="{y:.1f}" '
                        f'r="4.5" fill="#0e1117" '
                        f'stroke="#e6edf3" '
                        f'stroke-width="2"/>'
                    )
                    for x, y in zip(
                        x_positions,
                        y_positions,
                    )
                )

                momentum_html = (
                    '<div style="margin-top:-38px;'
                    'width:55%;min-width:360px;'
                    'margin-left:auto;">'
                    '<svg viewBox="0 0 300 78" '
                    'width="100%" height="78" '
                    'preserveAspectRatio="none">'
                    f'<line x1="8" y1="{zero_y:.1f}" '
                    f'x2="292" y2="{zero_y:.1f}" '
                    'stroke="#6e7681" stroke-width="1" '
                    'stroke-dasharray="4 4"/>'
                    f'<polyline points="{points}" '
                    'fill="none" stroke="#7457C8" '
                    'stroke-width="2" '
                    'stroke-linecap="round" '
                    'stroke-linejoin="round"/>'
                    f'{circles}'
                    '</svg>'
                    '<div style="display:flex;'
                    'justify-content:space-between;'
                    'margin-top:-2px;">'
                    '<div style="text-align:left;">'
                    '<div style="font-size:0.68rem;'
                    'color:#9ca3af;">12 Monate</div>'
                    f'<div style="font-size:0.84rem;'
                    f'font-weight:700;color:#e6edf3;">'
                    f'{_format_momentum(momentum_12m)}</div>'
                    '</div>'
                    '<div style="text-align:center;">'
                    '<div style="font-size:0.68rem;'
                    'color:#9ca3af;">6 Monate</div>'
                    f'<div style="font-size:0.84rem;'
                    f'font-weight:700;color:#e6edf3;">'
                    f'{_format_momentum(momentum_6m)}</div>'
                    '</div>'
                    '<div style="text-align:right;">'
                    '<div style="font-size:0.68rem;'
                    'color:#9ca3af;">3 Monate</div>'
                    f'<div style="font-size:0.84rem;'
                    f'font-weight:700;color:#e6edf3;">'
                    f'{_format_momentum(momentum_3m)}</div>'
                    '</div>'
                    '</div>'
                    '</div>'
                )

                st.markdown(
                    momentum_html,
                    unsafe_allow_html=True,
                )
            else:
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

                st.caption("Relative Stärke")
                st.markdown(
                    f"**RSI (14): {rsi:.1f} · {label}**"
                )

                rsi_position = max(
                    0.0,
                    min(100.0, float(rsi)),
                )

                rsi_html = (
                    f'<div style="position:relative;'
                    f'margin-top:10px;margin-bottom:4px;'
                    f'height:8px;border-radius:999px;'
                    f'background:linear-gradient(to right,'
                    f'#2EAD7B 0%,'
                    f'#2EAD7B 30%,'
                    f'#8b949e 30%,'
                    f'#8b949e 60%,'
                    f'#E58A2B 60%,'
                    f'#E58A2B 70%,'
                    f'#D9534F 70%,'
                    f'#D9534F 100%);">'
                    f'<div style="position:absolute;'
                    f'left:{rsi_position}%;top:50%;'
                    f'width:16px;height:16px;border-radius:50%;'
                    f'background:#20242B;'
                    f'border:3px solid #ffffff;'
                    f'transform:translate(-50%,-50%);'
                    f'box-shadow:0 0 0 1px rgba(0,0,0,0.35);">'
                    f'</div>'
                    f'</div>'
                    f'<div style="position:relative;'
                    f'height:17px;color:#9ca3af;'
                    f'font-size:0.68rem;">'
                    f'<span style="position:absolute;left:0;">0</span>'
                    f'<span style="position:absolute;left:30%;'
                    f'transform:translateX(-50%);">30</span>'
                    f'<span style="position:absolute;left:60%;'
                    f'transform:translateX(-50%);">60</span>'
                    f'<span style="position:absolute;left:70%;'
                    f'transform:translateX(-50%);">70</span>'
                    f'<span style="position:absolute;right:0;">100</span>'
                    f'</div>'
                )

                st.markdown(
                    rsi_html,
                    unsafe_allow_html=True,
                )

        elif criterion == "52W-Kontext":
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

            if distance_52w is not None:
                distance_position = max(
                    0.0,
                    min(
                        100.0,
                        (float(distance_52w) + 50.0) / 50.0 * 100.0,
                    ),
                )

                st.markdown(
                    f"""
                    <div style="
                        position:relative;
                        margin-top:8px;
                        margin-bottom:4px;
                        height:7px;
                        border-radius:999px;
                        background:linear-gradient(
                            to right,
                            #3f454d 0%,
                            #4d5560 20%,
                            #596572 40%,
                            #66788a 60%,
                            #5b8f82 80%,
                            #2EAD7B 100%
                        );
                    ">
                        <div style="
                            position:absolute;
                            left:{distance_position}%;
                            top:50%;
                            width:16px;
                            height:16px;
                            border-radius:50%;
                            background:#20242B;
                            border:3px solid #ffffff;
                            transform:translate(-50%, -50%);
                            box-shadow:0 0 0 1px rgba(0,0,0,0.35);
                        "></div>
                    </div>

                    <div style="
                        position:relative;
                        height:17px;
                        color:#9ca3af;
                        font-size:0.68rem;
                    ">
                        <span style="position:absolute;left:0;">≤ −50</span>
                        <span style="
                            position:absolute;
                            left:20%;
                            transform:translateX(-50%);
                        ">−40</span>
                        <span style="
                            position:absolute;
                            left:40%;
                            transform:translateX(-50%);
                        ">−30</span>
                        <span style="
                            position:absolute;
                            left:60%;
                            transform:translateX(-50%);
                        ">−20</span>
                        <span style="
                            position:absolute;
                            left:80%;
                            transform:translateX(-50%);
                        ">−10</span>
                        <span style="position:absolute;right:0;">0 %</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
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

                # Relevanter Bewertungsbereich:
                # <= -0.50 bis >= +0.40.
                pressure_min = -0.50
                pressure_max = 0.40

                pressure_position = (
                    (
                        max(
                            pressure_min,
                            min(
                                pressure_max,
                                float(pressure_balance),
                            ),
                        )
                        - pressure_min
                    )
                    / (pressure_max - pressure_min)
                    * 100.0
                )

                # Positionen der Bewertungsgrenzen auf der
                # nicht symmetrischen Skala -0.50 bis +0.40.
                pos_minus_030 = (
                    (-0.30 - pressure_min)
                    / (pressure_max - pressure_min)
                    * 100.0
                )
                pos_minus_010 = (
                    (-0.10 - pressure_min)
                    / (pressure_max - pressure_min)
                    * 100.0
                )
                pos_plus_005 = (
                    (0.05 - pressure_min)
                    / (pressure_max - pressure_min)
                    * 100.0
                )
                pos_plus_020 = (
                    (0.20 - pressure_min)
                    / (pressure_max - pressure_min)
                    * 100.0
                )

                pressure_html = (
                    f'<div style="position:relative;'
                    f'margin-top:10px;margin-bottom:4px;'
                    f'height:8px;border-radius:999px;'
                    f'background:linear-gradient(to right,'
                    f'#D9534F 0%,'
                    f'#D9534F {pos_minus_030:.1f}%,'
                    f'#B96B50 {pos_minus_030:.1f}%,'
                    f'#B96B50 {pos_minus_010:.1f}%,'
                    f'#8b949e {pos_minus_010:.1f}%,'
                    f'#8b949e {pos_plus_005:.1f}%,'
                    f'#5b8f82 {pos_plus_005:.1f}%,'
                    f'#5b8f82 {pos_plus_020:.1f}%,'
                    f'#2EAD7B {pos_plus_020:.1f}%,'
                    f'#2EAD7B 100%);">'
                    f'<div style="position:absolute;'
                    f'left:{pressure_position:.1f}%;top:50%;'
                    f'width:16px;height:16px;'
                    f'border-radius:50%;'
                    f'background:#20242B;'
                    f'border:3px solid #ffffff;'
                    f'transform:translate(-50%,-50%);'
                    f'box-shadow:0 0 0 1px rgba(0,0,0,0.35);">'
                    f'</div>'
                    f'</div>'
                    f'<div style="position:relative;'
                    f'height:17px;color:#9ca3af;'
                    f'font-size:0.68rem;">'
                    f'<span style="position:absolute;left:0;">'
                    f'≤ −0,50</span>'
                    f'<span style="position:absolute;'
                    f'left:{pos_minus_030:.1f}%;'
                    f'transform:translateX(-50%);">−0,30</span>'
                    f'<span style="position:absolute;'
                    f'left:{pos_minus_010:.1f}%;'
                    f'transform:translateX(-50%);">−0,10</span>'
                    f'<span style="position:absolute;'
                    f'left:{pos_plus_005:.1f}%;'
                    f'transform:translateX(-50%);">+0,05</span>'
                    f'<span style="position:absolute;'
                    f'left:{pos_plus_020:.1f}%;'
                    f'transform:translateX(-50%);">+0,20</span>'
                    f'<span style="position:absolute;right:0;">'
                    f'≥ +0,40</span>'
                    f'</div>'
                )

                st.markdown(
                    pressure_html,
                    unsafe_allow_html=True,
                )

        if criterion == "CM MACD":
            macd_weekly = data.get("CM MACD Weekly")
            signal_weekly = data.get("CM Signal Weekly")
            histogram_weekly = data.get("CM Histogram Weekly")

            if (
                macd_weekly is not None
                and signal_weekly is not None
                and histogram_weekly is not None
                and len(macd_weekly) >= 2
                and len(signal_weekly) >= 2
                and len(histogram_weekly) >= 2
            ):
                positive_weeks = 0
                for value in reversed(histogram_weekly):
                    if value > 0:
                        positive_weeks += 1
                    else:
                        break

                crossover_weeks = 0
                for macd_value, signal_value in reversed(
                    list(zip(macd_weekly, signal_weekly))
                ):
                    if macd_value > signal_value:
                        crossover_weeks += 1
                    else:
                        break

                histogram_rising = (
                    len(histogram_weekly) >= 2
                    and histogram_weekly[-1]
                    > histogram_weekly[-2]
                )
                histogram_rising_3w = (
                    len(histogram_weekly) >= 3
                    and histogram_weekly[-1]
                    > histogram_weekly[-2]
                    > histogram_weekly[-3]
                )
                macd_rising_3w = (
                    len(macd_weekly) >= 3
                    and macd_weekly[-1]
                    > macd_weekly[-2]
                    > macd_weekly[-3]
                )
                fresh_positive_histogram = (
                    1 <= positive_weeks <= 3
                )
                fresh_bullish_crossover = (
                    1 <= crossover_weeks <= 3
                )

                positive_macd_signals = sum(
                    (
                        histogram_rising,
                        histogram_rising_3w,
                        macd_rising_3w,
                        fresh_positive_histogram,
                        fresh_bullish_crossover,
                    )
                )

                if positive_macd_signals == 0:
                    macd_explanation = (
                        "Kein positives MACD-Signal: Histogramm und "
                        "MACD<br>zeigen aktuell keine frische "
                        "Aufwärtsdynamik."
                    )
                elif positive_macd_signals <= 2:
                    macd_explanation = (
                        "Erste positive MACD-Signale sind erkennbar,<br>"
                        "aber noch nicht ausreichend bestätigt."
                    )
                elif positive_macd_signals <= 4:
                    macd_explanation = (
                        "Der MACD zeigt positive Aufwärtsdynamik,<br>"
                        "die Bestätigung ist jedoch noch nicht "
                        "vollständig."
                    )
                else:
                    macd_explanation = (
                        "Der MACD bestätigt eine klare positive<br>"
                        "Aufwärtsdynamik."
                    )

                st.markdown(
                    (
                        '<div style="color:#9ca3af;'
                        'font-size:0.875rem;'
                        'margin-top:0.25rem;">'
                        f'{macd_explanation}'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                macd_values = [
                    float(value)
                    for value in macd_weekly[-12:]
                ]
                signal_values = [
                    float(value)
                    for value in signal_weekly[-12:]
                ]
                histogram_values = [
                    float(value)
                    for value in histogram_weekly[-12:]
                ]

                count = min(
                    len(macd_values),
                    len(signal_values),
                    len(histogram_values),
                )

                macd_values = macd_values[-count:]
                signal_values = signal_values[-count:]
                histogram_values = histogram_values[-count:]

                all_values = (
                    macd_values
                    + signal_values
                    + histogram_values
                    + [0.0]
                )

                chart_min = min(all_values)
                chart_max = max(all_values)
                chart_range = chart_max - chart_min

                if chart_range == 0:
                    chart_range = 1.0

                padding = chart_range * 0.12
                chart_min -= padding
                chart_max += padding
                chart_range = chart_max - chart_min

                def macd_y(value):
                    return (
                        6
                        + (chart_max - value)
                        / chart_range
                        * 78
                    )

                x_positions = [
                    10 + index * 280 / (count - 1)
                    for index in range(count)
                ]

                macd_points_svg = " ".join(
                    f"{x:.1f},{macd_y(value):.1f}"
                    for x, value in zip(
                        x_positions,
                        macd_values,
                    )
                )

                signal_points_svg = " ".join(
                    f"{x:.1f},{macd_y(value):.1f}"
                    for x, value in zip(
                        x_positions,
                        signal_values,
                    )
                )

                zero_y = macd_y(0.0)

                bar_width = max(
                    3.0,
                    min(12.0, 180.0 / count),
                )

                histogram_bars = "".join(
                    (
                        f'<rect '
                        f'x="{x - bar_width / 2:.1f}" '
                        f'y="{min(macd_y(value), zero_y):.1f}" '
                        f'width="{bar_width:.1f}" '
                        f'height="{max(abs(macd_y(value) - zero_y), 1.0):.1f}" '
                        f'rx="1" '
                        f'fill="{"#2EAD7B" if value >= 0 else "#D9534F"}" '
                        f'opacity="0.55"/>'
                    )
                    for x, value in zip(
                        x_positions,
                        histogram_values,
                    )
                )

                macd_html = (
                    '<div style="margin-top:-38px;'
                    'width:55%;min-width:360px;'
                    'margin-left:auto;">'
                    '<svg viewBox="0 0 300 92" '
                    'width="100%" height="92" '
                    'preserveAspectRatio="none">'
                    f'<line x1="6" y1="{zero_y:.1f}" '
                    f'x2="294" y2="{zero_y:.1f}" '
                    'stroke="#6e7681" stroke-width="1" '
                    'stroke-dasharray="4 4"/>'
                    f'{histogram_bars}'
                    f'<polyline points="{signal_points_svg}" '
                    'fill="none" stroke="#8b949e" '
                    'stroke-width="1.5" '
                    'stroke-linecap="round" '
                    'stroke-linejoin="round"/>'
                    f'<polyline points="{macd_points_svg}" '
                    'fill="none" stroke="#7457C8" '
                    'stroke-width="2" '
                    'stroke-linecap="round" '
                    'stroke-linejoin="round"/>'
                    '</svg>'
                    '<div style="display:flex;'
                    'justify-content:flex-end;gap:14px;'
                    'margin-top:-2px;font-size:0.68rem;'
                    'color:#9ca3af;">'
                    '<span style="color:#7457C8;">━ MACD</span>'
                    '<span>━ Signal</span>'
                    '<span>▮ Histogramm</span>'
                    '</div>'
                    '<div style="text-align:right;'
                    'margin-top:3px;font-size:0.68rem;'
                    'color:#9ca3af;">'
                    'Darstellung: letzte 12 Wochen'
                    '</div>'
                    '</div>'
                )

                st.markdown(
                    macd_html,
                    unsafe_allow_html=True,
                )

        st.divider()

    # -----------------------------------------------------
    # Entry Setup heute – 30 Punkte
    # -----------------------------------------------------
    entry_points = v3_blocks["entry_points"]
    entry_setup = (
        v3_blocks["entry_setup"]
        or "Nicht bewertbar"
    )

    if entry_points is None:
        entry_header = "⚪ Nicht bewertbar"
    else:
        entry_header = f"{entry_points:.1f} / 30"

    st.markdown(
        f"""
        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding:16px 16px;
            margin:2px 0 14px 0;
            background:linear-gradient(
                180deg,
                #363b44 0%,
                #292d34 100%
            );
            border:1px solid #5a616c;
            border-radius:8px;
            box-shadow:0 5px 16px rgba(0,0,0,0.38);
            color:#f0f2f5;
            font-size:1.12rem;
            font-weight:700;
        ">
            <span>🎯 Entry Setup heute</span>
            <span>{entry_header}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    entry_setup_col, entry_method_col = st.columns(
        [1, 1.45],
        vertical_alignment="center",
    )

    with entry_setup_col:
        st.markdown(f"**{entry_setup}**")

    with entry_method_col:
        with st.container(key="entry_method"):
            st.markdown(
                """
                <style>
                div.st-key-entry_method details summary,
                div.st-key-entry_method details summary * {
                    font-size: 0.78rem;
                    color: rgba(250, 250, 250, 0.58);
                }
                div.st-key-entry_method details {
                    border: 0;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("›  ⓘ Berechnung anzeigen"):
                st.caption(
                    "Bewertet, ob die heutige technische Situation "
                    "einen günstigen Einstieg unterstützt. "
                    "Berücksichtigt werden insbesondere Trendkanal, "
                    "Pullback/Erholung, Medianlinie, die 30-Wochen-Linie, "
                    "kurzfristige Bestätigung und die Lage zum vorherigen "
                    "52W-Hoch."
                )

    entry_detail = data.get("Entry Setup Erklärung")
    if entry_detail:
        st.caption(entry_detail)

    if entry_points is not None:
        entry_position = max(
            0.0,
            min(
                100.0,
                float(entry_points) / 30.0 * 100.0,
            ),
        )

        entry_scale_html = (
            f'<div style="margin-top:10px;">'
            f'<div style="position:relative;'
            f'height:8px;border-radius:999px;'
            f'background:linear-gradient(to right,'
            f'#D9534F 0%,'
            f'#B96B50 25%,'
            f'#8b949e 50%,'
            f'#5b8f82 75%,'
            f'#2EAD7B 100%);">'
            f'<div style="position:absolute;'
            f'left:{entry_position:.1f}%;top:50%;'
            f'width:16px;height:16px;'
            f'border-radius:50%;'
            f'background:#20242B;'
            f'border:3px solid #ffffff;'
            f'transform:translate(-50%,-50%);'
            f'box-shadow:0 0 0 1px rgba(0,0,0,0.35);">'
            f'</div>'
            f'</div>'
            f'<div style="display:flex;'
            f'justify-content:space-between;'
            f'margin-top:5px;margin-bottom:20px;'
            f'font-size:0.68rem;color:#9ca3af;">'
            f'<span>Einstieg abwarten</span>'
            f'<span>Selektiver Einstieg</span>'
            f'<span>Günstiges Einstiegssetup</span>'
            f'</div>'
            f'</div>'
        )

        st.markdown(
            entry_scale_html,
            unsafe_allow_html=True,
        )

    channel_position = data.get("Trendkanal Position")
    channel_position_normalized = data.get(
        "Trendkanal Position Normalisiert"
    )

    if (
        channel_position
        and channel_position_normalized is not None
    ):
        st.markdown(
            f"**{channel_position} · "
            f"Position {channel_position_normalized:+.2f}**"
        )

        channel_marker_position = (
            max(
                -2.0,
                min(
                    2.0,
                    float(channel_position_normalized),
                ),
            )
            + 2.0
        ) / 4.0 * 100.0

        channel_scale_html = f"""
        <div style="
            position:relative;
            height:16px;
            margin-top:10px;
            margin-bottom:2px;
        ">
            <div style="
                position:absolute;
                left:0;
                right:0;
                top:7px;
                height:2px;
                background:#6e7681;
                border-radius:2px;
            "></div>
            <div style="
                position:absolute;
                left:50%;
                top:3px;
                width:1px;
                height:10px;
                background:#9ca3af;
            "></div>
            <div style="
                position:absolute;
                left:{channel_marker_position:.1f}%;
                top:1px;
                width:14px;
                height:14px;
                border:2px solid #e6edf3;
                background:#0e1117;
                border-radius:50%;
                transform:translateX(-50%);
                box-sizing:border-box;
            "></div>
        </div>
        <div style="
            display:flex;
            justify-content:space-between;
            color:#9ca3af;
            font-size:0.72rem;
        ">
            <span>−2 untere Kanalgrenze</span>
            <span>0 Mittellinie</span>
            <span>+2 obere Kanalgrenze</span>
        </div>
        """

        st.markdown(
            channel_scale_html,
            unsafe_allow_html=True,
        )

    if v3_blocks["entry_neutral"]:
        st.caption(
            "Das Entry Setup ist derzeit nicht ausreichend "
            "bewertbar. In der Basis-Kaufchance wird der "
            "Block neutral mit 15 von 30 Punkten angesetzt."
        )

    st.divider()

    # -----------------------------------------------------
    # Datenabdeckung V3
    # -----------------------------------------------------
    coverage = round(available_maximum)

    if available_maximum == 100:
        st.markdown(
            f"**Aktuell bewertet: "
            f"{display_base_score} / 100 Punkte**"
        )
        st.caption("Datenabdeckung: 100 %")
    else:
        st.markdown(
            f"**Basis-Kaufchance: "
            f"{display_base_score} / 100 Punkte**"
        )
        st.caption(
            f"Bewertbare Datenabdeckung: {coverage} % · "
            "fehlende technische Blöcke werden nur dort "
            "neutral ersetzt, wo keine belastbare "
            "Bewertung möglich ist."
        )


def render_current_intelligence_section(data: dict) -> None:
    ticker = data.get("Ticker")
    company_name = (
        data.get("Name")
        or data.get("Unternehmen")
        or ticker
        or "Unbekannt"
    )

    preview_key = f"current_intelligence_preview_{ticker}"

    st.markdown("### ⚡ Kursrelevante News")

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
                technical_breakdown = (
                    calculate_technical_condition_v3_breakdown(data)
                )
                v3_blocks = calculate_opportunity_v3_blocks(data)

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
                    "Technische Verfassung Punkte": (
                        v3_blocks["technical_points"]
                    ),
                    "Technische Verfassung Maximum": 25,
                    "Entry Setup": v3_blocks["entry_setup"],
                    "Entry Setup Punkte": v3_blocks["entry_points"],
                    "Entry Setup Maximum": 30,
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
                    "Technische Verfassung Breakdown": (
                        technical_breakdown
                    ),
                    "Entry Setup Erklärung": data.get(
                        "Entry Setup Erklärung"
                    ),
                }

                price_history = load_price_history(
                    ticker,
                    period="1y",
                )

                significant_price_moves = (
                    detect_significant_price_moves(
                        price_history
                    )
                )

                result = research_current_intelligence_with_gemini(
                    api_key=st.secrets["GEMINI_API_KEY"],
                    tavily_api_key=st.secrets["TAVILY_API_KEY"],
                    ticker=ticker,
                    company_name=company_name,
                    sector=data.get("Sektor"),
                    industry=data.get("Branche"),
                    momentum_3m=data.get("Momentum 3M"),
                    momentum_6m=data.get("Momentum 6M"),
                    significant_price_moves=(
                        significant_price_moves
                    ),
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

    def _safe_intelligence_text(value):
        import html
        return html.escape(str(value))

    significant_moves = (
        result.get("Auffaellige_Handelstage") or []
    )

    if significant_moves:
        st.markdown("##### Auffällige Handelstage")

        for move in significant_moves:
            event_date = _format_date_de(
                move.get("Datum")
            )
            daily_return = move.get(
                "Tagesrendite_Prozent"
            )
            title = move.get(
                "Titel",
                "Auffällige Kursbewegung",
            )
            cause = move.get(
                "Ursache",
                "nicht belastbar geklärt",
            )

            if isinstance(daily_return, (int, float)):
                return_text = f"{daily_return:+.1f} %"
            else:
                return_text = "–"

            st.markdown(
                f'<div style="margin-bottom:4px;">'
                f'<strong>{event_date} · {return_text}</strong>'
                f' — {_safe_intelligence_text(title)}'
                f'</div>'
                f'<div style="'
                f'font-size:0.875rem; '
                f'color:#9ca3af; '
                f'margin-bottom:12px;">'
                f'{_safe_intelligence_text(cause)}'
                f'</div>',
                unsafe_allow_html=True,
            )

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
            title = item.get("Titel", "Entwicklung")
            event_date = item.get("Datum")
            date_html = (
                f' <span style="color:#9ca3af; '
                f'font-size:0.8rem; font-weight:400;">'
                f'· {_format_date_de(event_date)}</span>'
                if event_date
                else ""
            )

            st.markdown(
                f'<div style="font-weight:700;">'
                f'{index}. {_safe_intelligence_text(title)}'
                f'{date_html}</div>',
                unsafe_allow_html=True,
            )

            if item.get("Beschreibung"):
                st.markdown(
                    f'<div style="font-size:0.875rem; color:#9ca3af; margin-bottom:12px;">'
                    f'{_safe_intelligence_text(item["Beschreibung"])}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    with col_negative:
        st.markdown("#### 🔴 Gegenwind")

        if not negative:
            st.caption(
                "Aktuell kein wesentlicher neuer Gegenwind."
            )

        for index, item in enumerate(negative, start=1):
            title = item.get("Titel", "Entwicklung")
            event_date = item.get("Datum")
            date_html = (
                f' <span style="color:#9ca3af; '
                f'font-size:0.8rem; font-weight:400;">'
                f'· {_format_date_de(event_date)}</span>'
                if event_date
                else ""
            )

            st.markdown(
                f'<div style="font-weight:700;">'
                f'{index}. {_safe_intelligence_text(title)}'
                f'{date_html}</div>',
                unsafe_allow_html=True,
            )

            if item.get("Beschreibung"):
                st.markdown(
                    f'<div style="font-size:0.875rem; color:#9ca3af; margin-bottom:12px;">'
                    f'{_safe_intelligence_text(item["Beschreibung"])}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

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
                st.markdown(
                    f'<div style="font-size:0.875rem; color:#9ca3af; margin-bottom:12px;">'
                    f'{_safe_intelligence_text(description)}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

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
            st.markdown(
                f'<div style="font-size:0.875rem; color:#9ca3af;">'
                f'{_safe_intelligence_text(result["Event_Impact_Begruendung"])}'
                f'</div>',
                unsafe_allow_html=True,
            )

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


def _render_current_intelligence(data: dict) -> None:
    ticker = data.get("Ticker")
    saved_result = get_current_intelligence(ticker)

    event_impact = data.get("Event Impact")

    if saved_result:
        if event_impact is None:
            event_impact = 0

        if event_impact > 0:
            impact_label = f"+{event_impact}"
        else:
            impact_label = str(event_impact)

        expander_title = (
            f"Warum Event Impact = {impact_label}?"
        )
    else:
        expander_title = (
            "Warum Event Impact? · noch nicht analysiert"
        )

    st.markdown(
        """
        <div style="
            color:#8b949e;
            font-size:20px;
            font-weight:600;
            line-height:1;
            margin:-7px 0 -15px 105px;
            position:relative;
            z-index:2;
            pointer-events:none;
        ">
            +
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(expander_title):
        render_current_intelligence_section(data)


def get_opportunity_rating(data: dict) -> tuple:
    buy_score = data["Kaufchance"]
    opportunity_breakdown = calculate_opportunity_breakdown(data)

    v3_blocks = calculate_opportunity_v3_blocks(data)

    technical_context_missing = (
        v3_blocks["technical_neutral"]
        or v3_blocks["entry_neutral"]
    )

    available_maximum = v3_blocks["available_maximum"]
    coverage = round(available_maximum)

    technical_available = (
        v3_blocks["technical_available"] > 0
    )
    entry_available = (
        v3_blocks["entry_available"] > 0
    )
    fundamental_available_maximum = (
        v3_blocks["fundamental_available"]
    )

    technical_only_missing = (
        not technical_available
        and entry_available
        and fundamental_available_maximum == 45
    )

    if (
        fundamental_available_maximum < 45
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

    elif (
        coverage < 100
        and not technical_only_missing
        and not v3_blocks["entry_neutral"]
    ):
        rating = "Eingeschränkt bewertbar"
        icon = "⚪"
        border = "#8b949e"
        explanation = (
            f"Für die Kaufchance sind derzeit nur "
            f"{coverage} % der vorgesehenen Daten verfügbar."
        )

    elif buy_score >= 68:
        entry_setup = data.get("Entry Setup")

        entry_ready_setups = {
            "Lower Channel Bounce – bestätigt",
            "Pullback Recovery – bestätigt",
            "Median Support – bestätigt",
            "Median Reclaim – bestätigt",
        "30W Support/Reclaim – bestätigt",
            "Breakout – bestätigt",
            "Lower Channel Bounce",
            "Median Reclaim",
            "Widerstands-Anlauf – positiv",
        }

        entry_ready = entry_setup in entry_ready_setups

        icon = "🟢"
        border = "#2EAD7B"

        if technical_context_missing:
            rating = "Attraktiv – technische Bestätigung offen"
            explanation = (
                "Die bewertbaren Faktoren ergeben insgesamt eine "
                "attraktive Kaufkonstellation. Teile der technischen "
                "Einordnung sind wegen unzureichender Kurshistorie "
                "noch nicht belastbar bewertbar."
            )
        elif entry_ready:
            rating = "Attraktiv"
            explanation = (
                "Die aktuelle Kaufkonstellation erscheint attraktiv. "
                "Das Entry Setup unterstützt einen Einstieg."
            )
        elif entry_setup in {
            "Untere Kanalhälfte – unbestätigt",
            "Median Test – unbestätigt",
        }:
            rating = "Attraktiv – günstige Einstiegszone"
            explanation = (
                "Die Aktie weist insgesamt eine attraktive "
                "Kaufkonstellation auf und befindet sich in einer "
                "günstigen Einstiegszone. Das technische "
                "Einstiegssignal ist noch nicht bestätigt."
            )
        else:
            rating = "Attraktiv – Einstieg noch unbestätigt"
            explanation = (
                "Die Aktie weist insgesamt eine attraktive "
                "Kaufkonstellation auf. Das aktuelle Entry Setup ist "
                "jedoch noch nicht ausreichend bestätigt."
            )

    elif buy_score >= 51:
        entry_setup = data.get("Entry Setup")

        icon = "🟡"
        border = "#D9A514"

        if entry_setup in {
            "Untere Kanalhälfte – unbestätigt",
            "Median Test – unbestätigt",
        }:
            rating = "Neutral – günstige Einstiegszone"
            explanation = (
                "Die Kaufchance ist insgesamt noch gemischt. "
                "Die aktuelle Position im langfristigen Trend bietet "
                "jedoch eine günstige Einstiegszone; das technische "
                "Einstiegssignal ist noch nicht bestätigt."
            )
        else:
            rating = "Neutral"
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

    return rating, explanation, icon, border


def render_opportunity_section(
    data: dict,
) -> None:

    buy_score = data["Kaufchance"]
    rating, explanation, icon, border = get_opportunity_rating(data)
    v3_blocks = calculate_opportunity_v3_blocks(data)

    base_buy_score = data.get(
        "Kaufchance Basis",
        buy_score,
    )
    event_impact = data.get("Event Impact")
    technical_available = (
        v3_blocks["technical_available"] > 0
    )

    display_score = f"{round(buy_score)} / 100"

    entry_gate_closed = (
        data.get("Entry Setup")
        == "Extrem überdehnt – Einstieg abwarten"
    )

    if entry_gate_closed and buy_score >= 68:
        icon = "🟢"
        rating = "Attraktiv – Einstieg abwarten"
        explanation = (
            "Die Kaufkonstellation ist insgesamt attraktiv, "
            "der Einstieg ist wegen extremer Überdehnung derzeit "
            "jedoch nicht freigegeben."
        )

    entry_gate_html = ""

    if entry_gate_closed and buy_score >= 68:
        entry_gate_html = """
            <div style="
                color:#d0d7de;
                font-size:13px;
                font-weight:600;
                margin-top:5px;
            ">
                ⓧ Einstieg derzeit nicht freigegeben
            </div>
        """

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

    if not technical_available:
        overlay_html += """
    <div style="
        color:#8b949e;
        font-size:13px;
        margin-top:6px;
    ">
        Technische Verfassung noch nicht belastbar bewertbar.
        Der 25-Punkte-Block wird neutral mit 12,5 Punkten
        angesetzt.
    </div>
"""

    if base_buy_score is not None and buy_score is not None:
        if event_impact is None:
            impact_text = "noch nicht analysiert"
        elif event_impact > 0:
            impact_text = f"+{event_impact}"
        elif event_impact == 0:
            impact_text = "±0"
        else:
            impact_text = str(event_impact)

        st.markdown(
            f"""
            <div style="
                display:flex;
                align-items:center;
                justify-content:center;
                gap:12px;
                margin:4px 0 18px 0;
                color:#a8b2c1;
                font-size:0.86rem;
            ">
                <span>
                    Basis <strong style="color:#f8fafc;">
                        {round(base_buy_score)}
                    </strong>
                </span>
                <span>+</span>
                <span>
                    Event Impact
                    <strong style="color:#f8fafc;">
                        {impact_text}
                    </strong>
                </span>
                <span>→</span>
                <span>
                    Kaufchance
                    <strong style="color:#f8fafc;">
                        {round(buy_score)}
                    </strong>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                text-align:center;
                color:#718096;
                font-size:0.72rem;
                margin:-10px 0 18px 0;
            ">
                Event Impact · Analyse unter
                03 · Aktuelle Entwicklungen
            </div>
            """,
            unsafe_allow_html=True,
        )

    _render_opportunity_breakdown(
        data,
        rating,
    )
