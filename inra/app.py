import streamlit as st

from config.settings import APP_NAME, APP_SUBTITLE


st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
)

pages = {
    "InRA": [
        st.Page(
            "pages/start.py",
            title="Marktlage",
            icon=":material/show_chart:",
            default=True,
        ),
        st.Page(
            "pages/scout.py",
            title="Scout",
            icon=":material/search:",
        ),
        st.Page(
            "pages/radar.py",
            title="Radar",
            icon=":material/radar:",
        ),
        st.Page(
            "pages/analyse.py",
            title="Analyse",
            icon=":material/calculate:",
        ),
        st.Page(
            "pages/countries.py",
            title="Länder",
            icon=":material/public:",
        ),
        st.Page(
            "pages/systemstatus.py",
            title="Systemstatus",
            icon=":material/settings:",
        ),
    ],
}

navigation = st.navigation(pages)

st.markdown(
    """
    <style>
    /* Kompakte InRA-Navigation */
    [data-testid="stSidebar"] {
        width: 210px !important;
        min-width: 210px !important;
        max-width: 210px !important;

        background:
            radial-gradient(
                circle at 30% 20%,
                rgba(37, 99, 235, 0.22),
                transparent 35%
            ),
            radial-gradient(
                circle at 80% 70%,
                rgba(30, 64, 175, 0.18),
                transparent 40%
            ),
            linear-gradient(
                180deg,
                #020617 0%,
                #071426 45%,
                #030712 100%
            );
    }

    [data-testid="stSidebar"] > div:first-child {
        width: 210px !important;
    }

    [data-testid="stSidebarContent"] {
        width: 210px !important;
    }

    /* Etwas kompaktere Innenabstände */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.65rem;
    }

    [data-testid="stSidebar"] .st-emotion-cache-1cypcdb {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* InRA Navigation Styling */
    [data-testid="stSidebarNav"] span {
        color: #93c5fd !important;
        font-weight: 700;
        letter-spacing: 0.18em;
        text-transform: uppercase;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #f8fafc !important;
        text-shadow:
            0 0 10px rgba(147, 197, 253, 0.9),
            0 0 22px rgba(37, 99, 235, 0.75);
    }

    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    """
    <div style="margin-bottom: 1.25rem;">
        <div style="
            font-size: 1.5rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 0.65rem;
        ">
            InRA
        </div>
        <div style="
            font-size: 0.82rem;
            line-height: 1.45;
            color: #a9b1bd;
        ">
            Investment<br>
            Research<br>
            Assistant
        </div>
        <div style="
            font-size: 0.75rem;
            line-height: 1.4;
            color: #7f8997;
            margin-top: 0.9rem;
        ">
            Version 0.1
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

from utils.data_health import (
    check_benchmark_cache_health,
    check_benchmark_core_coverage,
    check_benchmark_plausibility,
    check_market_risk_snapshot_health,
)

_health_checks = [
    check_benchmark_cache_health(),
    check_benchmark_core_coverage(),
    check_benchmark_plausibility(),
    check_market_risk_snapshot_health(),
]

_health_rank = {
    "ok": 0,
    "warning": 1,
    "error": 2,
}

_health_status = max(
    (result["status"] for result in _health_checks),
    key=lambda status: _health_rank.get(status, 2),
)

_health_labels = {
    "ok": "\U0001F7E2 Systemstatus: OK",
    "warning": "\U0001F7E1 Systemstatus: Hinweis",
    "error": "\U0001F534 Systemstatus: Fehler",
}

st.sidebar.caption(_health_labels[_health_status])

navigation.run()