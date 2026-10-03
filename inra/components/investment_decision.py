import textwrap

import streamlit as st

from modules.opportunity_score import (
    calculate_opportunity_v3_blocks,
    get_pe_valuation_class,
)
from utils.current_intelligence import get_current_intelligence

def get_investment_decision_color(title: str) -> str:
    """Liefert die Ampelfarbe eines Investment-Urteils."""
    title = str(title or "").strip()

    if title.startswith("Klarer Kauf"):
        return "#20C77A"

    if title.startswith("Sehr kaufenswert – Einstieg abwarten"):
        return "#239B6B"

    if title.startswith("Erste Position aufbauen"):
        return "#2EAD7B"

    if title.startswith("Kaufenswert – attraktive Einstiegszone"):
        return "#5DBE91"

    if title.startswith("Kaufenswert – Einstieg abwarten"):
        return "#86CFAE"

    if title.startswith("Trading-Chance"):
        return "#4A90E2"

    if title.startswith("Beobachten"):
        return "#D9A514"

    if title.startswith("Abwarten"):
        return "#E58A2B"

    if title.startswith("Kein Investment"):
        return "#D9534F"

    return "#8b949e"


INVESTMENT_DECISION_LEVELS = [
    (
        "Klarer Kauf",
        "Sehr starke Gesamtkonstellation · Einstieg unterstützt",
    ),
    (
        "Erste Position aufbauen",
        "Gute Gesamtkonstellation · Einstieg unterstützt",
    ),
    (
        "Sehr kaufenswert – Einstieg abwarten",
        "Sehr starke Gesamtkonstellation · Timing abwarten",
    ),
    (
        "Kaufenswert – attraktive Einstiegszone",
        "Gute Gesamtkonstellation · günstige Zone · Signal unbestätigt",
    ),
    (
        "Kaufenswert – Einstieg abwarten",
        "Gute Gesamtkonstellation · Timing abwarten",
    ),
    (
        "Trading-Chance",
        "Attraktives Timing · Qualität unter Kaufniveau",
    ),
    (
        "Beobachten",
        "Interessant · Gesamtkonstellation noch nicht stark genug",
    ),
    (
        "Abwarten",
        "Aktuelle Gesamtkonstellation nicht attraktiv genug",
    ),
    (
        "Kein Investment",
        "Fundamentale Belastung zu hoch",
    ),
]


def _is_distressed(data: dict) -> bool:
    distress_values = (
        data.get("Kapitalrendite"),
        data.get("Operative Marge"),
        data.get("Operativer Cashflow"),
        data.get("EBITDA"),
    )

    negative_signals = sum(
        value is not None and value < 0
        for value in distress_values
    )

    return negative_signals >= 3

def get_investment_decision(data: dict) -> dict:
    buy_score = data["Kaufchance"]
    quality_score = data["Unternehmensqualität"]
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

    entry_zone_setups = {
        "Untere Kanalhälfte – unbestätigt",
        "Median Test – unbestätigt",
    }
    entry_zone = entry_setup in entry_zone_setups

    v3_blocks = calculate_opportunity_v3_blocks(data)

    available_maximum = v3_blocks["available_maximum"]
    fundamental_complete = (
        v3_blocks["fundamental_available"] == 45
    )
    technical_context_missing = (
        v3_blocks["technical_neutral"]
        or v3_blocks["entry_neutral"]
    )

    opportunity_data_complete = (
        available_maximum == 100
        or (
            fundamental_complete
            and technical_context_missing
        )
    )

    if quality_score is None:
        investment_score = None
    else:
        investment_score = (
            0.60 * buy_score
            + 0.40 * quality_score
        )

    if quality_score is None:
        title = "Eingeschränkt bewertbar"
        icon = "⚪"
        background = "#F3F4F6"
        border = "#8b949e"
        text = (
            "Für diese Aktie liegt noch kein spezifisches "
            "Unternehmensqualitätsprofil vor. "
            "Die Kaufchance kann separat betrachtet werden, "
            "ein vollständiges Investment-Urteil ist derzeit "
            "nicht möglich."
        )

    elif _is_distressed(data):
        title = "Kein Investment"
        icon = "🔴"
        background = "#FDEEEE"
        border = "#D9534F"
        text = (
            "Mehrere zentrale operative Kennzahlen sind negativ. "
            "Die fundamentale Belastung ist derzeit zu hoch für "
            "ein Investment."
        )

    elif (
        not opportunity_data_complete
        and get_pe_valuation_class(data) == "SONDERFALL"
    ):
        title = "Sonderfall"
        icon = "⚪"
        background = "#F3F4F6"
        border = "#8b949e"
        text = (
            "Die KGV-basierte Kursbewertung ist für diesen "
            "Unternehmenstyp methodisch nicht anwendbar. "
            "Daher wird derzeit kein reguläres Investment-Urteil "
            "vergeben."
        )

    elif not opportunity_data_complete:
        title = "Eingeschränkt bewertbar"
        icon = "⚪"
        background = "#F3F4F6"
        border = "#8b949e"
        text = (
            "Für ein belastbares Investment-Urteil fehlen derzeit "
            "wesentliche Daten zur Kaufchance."
        )

    elif (
        investment_score >= 80
        and buy_score >= 70
        and entry_ready
    ):
        title = "Klarer Kauf"
        icon = "★"
        background = "#E4F8EE"
        border = "#20C77A"
        text = (
            "Kaufchance und Unternehmensqualität ergeben zusammen "
            "eine besonders überzeugende Investment-Konstellation. "
            "Auch das aktuelle Entry Setup unterstützt den Einstieg."
        )

    elif (
        investment_score >= 70
        and buy_score >= 60
        and entry_ready
    ):
        title = "Erste Position aufbauen"
        icon = "🟢"
        background = "#EAF7F2"
        border = "#2EAD7B"
        text = (
            "Die Kombination aus Einstiegschance und "
            "Unternehmensqualität spricht derzeit für den Aufbau "
            "einer ersten Position."
        )

    elif (
        investment_score >= 70
        and buy_score >= 60
        and entry_zone
    ):
        title = "Kaufenswert – attraktive Einstiegszone"
        icon = "🟢"
        background = "#F2FAF6"
        border = "#86CFAE"
        text = (
            "Die Aktie erscheint grundsätzlich kaufenswert und "
            "befindet sich in einer attraktiven Einstiegszone. "
            "Das technische Einstiegssignal ist jedoch noch "
            "nicht bestätigt."
        )

    elif (
        investment_score >= 80
        and buy_score >= 70
        and not entry_ready
    ):
        title = "Sehr kaufenswert – Einstieg abwarten"
        icon = "🟢"
        background = "#EAF7F2"
        border = "#2EAD7B"
        text = (
            "Kaufchance und Unternehmensqualität ergeben zusammen "
            "eine besonders überzeugende Investment-Konstellation. "
            "Das aktuelle Entry Setup spricht jedoch dafür, mit "
            "einem unmittelbaren Einstieg noch abzuwarten."
        )

    elif (
        investment_score >= 70
        and buy_score >= 60
        and not entry_ready
    ):
        title = "Kaufenswert – Einstieg abwarten"
        icon = "🟢"
        background = "#F2FAF6"
        border = "#86CFAE"
        text = (
            "Die Aktie erscheint grundsätzlich kaufenswert. "
            "Das aktuelle Entry Setup ist jedoch noch nicht "
            "ausreichend überzeugend für einen unmittelbaren "
            "Positionsaufbau."
        )

    elif buy_score >= 75 and investment_score < 70:
        title = "Trading-Chance"
        icon = "🔵"
        background = "#EEF5FF"
        border = "#4A90E2"
        text = (
            "Die aktuelle Einstiegssituation ist außergewöhnlich "
            "attraktiv, die Unternehmensqualität reicht jedoch "
            "nicht für eine reguläre Kaufempfehlung."
        )

    elif investment_score >= 55:
        title = "Beobachten"
        icon = "🟡"
        background = "#FFF8E1"
        border = "#D9A514"
        text = (
            "Die Aktie bleibt interessant, die Kombination aus "
            "Einstiegschance und Unternehmensqualität reicht derzeit "
            "aber noch nicht für eine Kaufempfehlung."
        )

    else:
        title = "Abwarten"
        icon = "🟠"
        background = "#FFF3E8"
        border = "#E58A2B"
        text = (
            "Die aktuelle Kombination aus Einstiegschance und "
            "Unternehmensqualität ist für ein Investment derzeit "
            "nicht attraktiv genug."
        )

    if technical_context_missing and title not in {
        "Kein Investment",
        "Sonderfall",
        "Eingeschränkt bewertbar",
    }:
        title = f"{title} – unter Vorbehalt"

        missing_parts = []

        if v3_blocks["technical_neutral"]:
            missing_parts.append(
                "die technische Verfassung"
            )

        if v3_blocks["entry_neutral"]:
            missing_parts.append(
                "das Entry Setup"
            )

        missing_text = " und ".join(missing_parts)

        if missing_text == "das Entry Setup":
            missing_text = "Das Entry Setup"
        else:
            missing_text = missing_text.capitalize()

        text += (
            f" {missing_text} "
            "ist wegen unzureichender Kurshistorie noch nicht "
            "belastbar bewertbar und wird in der Kaufchance "
            "neutral angesetzt."
        )

    return {
        "title": title,
        "icon": icon,
        "background": background,
        "border": border,
        "text": text,
        "investment_score": investment_score,
    }


def render_investment_decision(
    data: dict,
    report_pdf_builder=None,
    report_filename: str = None,
) -> None:
    decision = get_investment_decision(data)

    title = decision["title"]
    icon = decision["icon"]
    background = decision["background"]
    border = decision["border"]
    text = decision["text"]

    kursstand = data.get("Kursstand")
    kursstand_html = ""

    if kursstand is not None:
        try:
            kursstand_text = kursstand.strftime("%d.%m.%Y")
            kursstand_html = (
                f'<span style="'
                f'color:#8b949e;'
                f'font-size:12px;'
                f'font-weight:500;'
                f'text-transform:none;'
                f'letter-spacing:0;'
                f'">Kursstand: {kursstand_text} · Schlusskurs</span>'
            )
        except (AttributeError, ValueError):
            pass

    if title.startswith("Klarer Kauf"):
        icon_html = (
            '<span style="color:#20C77A;">★</span>'
        )
    else:
        icon_html = icon

    html = textwrap.dedent(
    f"""
<div style="
    margin:8px 0 10px 0;
">
    <div class="inra-section-header">
        <div class="inra-section-kicker">
            <span>01</span>
            INVESTMENT DECISION
        </div>
    </div>

    <div style="
        background:
            linear-gradient(
                135deg,
                rgba(31,41,55,0.98),
                rgba(17,24,39,0.96)
            );
        border:1px solid {border};
        border-left:5px solid {border};
        border-radius:16px;
        padding:30px 34px 32px 34px;
        box-shadow:
            0 18px 44px rgba(0,0,0,0.28),
            inset 0 1px 0 rgba(255,255,255,0.035);
    ">

        <div style="
            display:flex;
            justify-content:space-between;
            align-items:center;
            gap:18px;
        ">
            <div style="
                color:{border};
                font-size:11px;
                font-weight:800;
                text-transform:uppercase;
                letter-spacing:0.14em;
            ">
                Investmententscheidung
            </div>
            {kursstand_html}
        </div>

        <div style="
            color:#f8fafc;
            font-size:36px;
            line-height:1.16;
            font-weight:800;
            letter-spacing:-0.025em;
            margin-top:14px;
        ">
            {icon_html} {title}
        </div>

        <div style="
            width:64px;
            height:3px;
            border-radius:999px;
            background:{border};
            margin-top:18px;
            opacity:0.90;
        "></div>

        <div style="
            color:#cbd5e1;
            font-size:16px;
            margin-top:18px;
            line-height:1.65;
            max-width:1080px;
        ">
            {text}
        </div>

    </div>
</div>
"""
).strip()

    st.html(html)

    action_columns = st.columns(
        [1, 2.2],
        gap="small",
    )

    with action_columns[0]:
        with st.popover("ⓘ Urteilsstufen"):
            for level_title, level_text in INVESTMENT_DECISION_LEVELS:
                color = get_investment_decision_color(level_title)

                st.markdown(
                    (
                        f'<span style="color:{color}; font-weight:700;">'
                        f'{level_title}</span>'
                        f'<span style="color:#8b949e;"> — '
                        f'{level_text}</span>'
                    ),
                    unsafe_allow_html=True,
                )

            st.divider()
            st.caption(
                "Kernlogik: Investment-Score = 60 % Kaufchance + "
                "40 % Unternehmensqualität. Das Entry Setup "
                "beeinflusst zusätzlich, ob ein unmittelbarer "
                "Einstieg unterstützt wird."
            )

    if report_pdf_builder:
        with action_columns[1]:
            ticker = str(
                data.get("Ticker") or "Aktie"
            ).strip().upper()

            pdf_state_key = (
                f"analysis_pdf_{ticker}"
            )

            if st.session_state.get(pdf_state_key):
                st.download_button(
                    "🖨 Analyse als PDF herunterladen",
                    data=st.session_state[pdf_state_key],
                    file_name=(
                        report_filename
                        or "InRA_Analyse.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=False,
                    key="download_analysis_pdf",
                )
            elif st.button(
                "🖨 Analyse als PDF erstellen",
                use_container_width=False,
                key="build_analysis_pdf",
            ):
                with st.spinner(
                    "PDF-Analyse wird erstellt …"
                ):
                    st.session_state[pdf_state_key] = (
                        report_pdf_builder()
                    )

                st.rerun()



def render_inra_fazit_section(data: dict) -> None:
    ticker = str(data.get("Ticker") or "").strip().upper()

    current_intelligence = get_current_intelligence(ticker)
    inra_fazit = (
        current_intelligence.get("InRA_Fazit")
        if isinstance(current_intelligence, dict)
        else None
    )

    uses_current_intelligence = isinstance(inra_fazit, dict)

    if not uses_current_intelligence:
        decision = get_investment_decision(data)

        quality_score = data.get("Unternehmensqualität")
        buy_score = data.get("Kaufchance")
        entry_setup = str(
            data.get("Entry Setup") or "noch nicht belastbar bewertet"
        ).strip()

        if quality_score is None:
            quality_text = (
                "Die Unternehmensqualität ist noch nicht vollständig "
                "bewertbar"
            )
        elif quality_score >= 85:
            quality_text = "Sehr hohe Unternehmensqualität"
        elif quality_score >= 70:
            quality_text = "Hohe Unternehmensqualität"
        elif quality_score >= 55:
            quality_text = "Solide Unternehmensqualität"
        elif quality_score >= 40:
            quality_text = "Schwache Unternehmensqualität"
        else:
            quality_text = "Sehr schwache Unternehmensqualität"

        if buy_score is None:
            opportunity_text = (
                "die Kaufchance ist noch nicht vollständig bewertbar"
            )
        elif buy_score >= 68:
            opportunity_text = "eine attraktive Kaufkonstellation"
        elif buy_score >= 51:
            opportunity_text = "eine insgesamt gemischte Kaufkonstellation"
        else:
            opportunity_text = "eine derzeit unattraktive Kaufkonstellation"

        if entry_setup == "Extrem überdehnt – Einstieg abwarten":
            dagegen = (
                "Die Aktie ist technisch derzeit extrem überdehnt. "
                "Für einen Neueinstieg ist das Chance-Risiko-Verhältnis "
                "deshalb aktuell ungünstig."
            )
            worauf = (
                "Entscheidend ist, ob sich nach der starken "
                "Kursbeschleunigung ein günstigeres und technisch "
                "belastbares Entry Setup entwickelt."
            )
        else:
            dagegen = (
                f"Das aktuelle Entry Setup „{entry_setup}“ begrenzt "
                "derzeit die Qualität eines unmittelbaren Einstiegs."
            )
            worauf = (
                "Entscheidend ist, ob sich das technische Entry Setup "
                "verbessert oder bestätigt."
            )

        inra_fazit = {
            "Kernaussage": decision.get("text") or "",
            "Dafuer": (
                f"{quality_text} trifft auf {opportunity_text}."
            ),
            "Dagegen": dagegen,
            "Worauf_es_ankommt": worauf,
        }

    kernaussage = str(
        inra_fazit.get("Kernaussage") or ""
    ).strip()
    dafuer = str(
        inra_fazit.get("Dafuer") or ""
    ).strip()
    dagegen = str(
        inra_fazit.get("Dagegen") or ""
    ).strip()
    fazit_text = str(
        inra_fazit.get("Text") or ""
    ).strip()
    worauf = str(
        inra_fazit.get("Worauf_es_ankommt") or ""
    ).strip()

    if not (
        kernaussage
        or dafuer
        or dagegen
        or fazit_text
        or worauf
    ):
        return

    st.markdown(
        """
        <div style="
            color:#94a3b8;
            font-size:0.76rem;
            font-weight:800;
            letter-spacing:0.14em;
            text-transform:uppercase;
            margin-bottom:0.55rem;
        ">
            DAS WICHTIGSTE AUF EINEN BLICK
        </div>
        """,
        unsafe_allow_html=True,
    )

    if kernaussage:
        st.markdown(
            f"""
            <div style="
                color:#f8fafc;
                font-size:1.18rem;
                font-weight:700;
                line-height:1.55;
                margin-bottom:1.15rem;
            ">
                {kernaussage}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if dafuer or dagegen:
        pro_col, contra_col = st.columns(
            2,
            gap="medium",
        )

        with pro_col:
            if dafuer:
                st.markdown(
                    f"""
                    <div style="
                        height:100%;
                        padding:1rem 1.1rem;
                        background:rgba(31,41,55,0.48);
                        border:1px solid rgba(148,163,184,0.16);
                        border-radius:10px;
                    ">
                        <div style="
                            color:#94a3b8;
                            font-size:0.76rem;
                            font-weight:800;
                            letter-spacing:0.08em;
                            text-transform:uppercase;
                            margin-bottom:0.55rem;
                        ">
                            <span style="
                                display:inline-block;
                                width:7px;
                                height:7px;
                                border-radius:50%;
                                background:#45c995;
                                box-shadow:0 0 8px rgba(69,201,149,0.75);
                                margin-right:7px;
                                vertical-align:1px;
                            "></span>
                            Was dafür spricht
                        </div>
                        <div style="
                            color:#d7dee8;
                            font-size:0.92rem;
                            line-height:1.6;
                        ">
                            {dafuer}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with contra_col:
            if dagegen:
                st.markdown(
                    f"""
                    <div style="
                        height:100%;
                        padding:1rem 1.1rem;
                        background:rgba(31,41,55,0.48);
                        border:1px solid rgba(148,163,184,0.16);
                        border-radius:10px;
                    ">
                        <div style="
                            color:#94a3b8;
                            font-size:0.76rem;
                            font-weight:800;
                            letter-spacing:0.08em;
                            text-transform:uppercase;
                            margin-bottom:0.55rem;
                        ">
                            <span style="
                                display:inline-block;
                                width:7px;
                                height:7px;
                                border-radius:50%;
                                background:#f87171;
                                box-shadow:0 0 8px rgba(248,113,113,0.70);
                                margin-right:7px;
                                vertical-align:1px;
                            "></span>
                            Was bremst
                        </div>
                        <div style="
                            color:#d7dee8;
                            font-size:0.92rem;
                            line-height:1.6;
                        ">
                            {dagegen}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # Fallback für ältere gespeicherte Analysen.
    if fazit_text and not (dafuer or dagegen):
        st.markdown(fazit_text)

    if worauf:
        st.markdown(
            f"""
            <div style="
                margin-top:1rem;
                padding:1rem 1.1rem;
                background:rgba(15,23,42,0.52);
                border:1px solid rgba(148,163,184,0.20);
                border-radius:10px;
            ">
                <div style="
                    color:#94a3b8;
                    font-size:0.76rem;
                    font-weight:800;
                    letter-spacing:0.08em;
                    text-transform:uppercase;
                    margin-bottom:0.55rem;
                ">
                    Worauf es jetzt ankommt
                </div>
                <div style="
                    color:#f1f5f9;
                    font-size:0.94rem;
                    line-height:1.6;
                ">
                    {worauf}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


    if not uses_current_intelligence:
        st.caption(
            "Aktualität: Kursrelevante News sind noch nicht berücksichtigt. "
            "Für ein vollständigeres Gesamtbild Bereich 03 aktualisieren."
        )

