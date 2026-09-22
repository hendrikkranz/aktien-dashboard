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
            icon="🏠",
            default=True,
        ),
        st.Page(
            "pages/scout.py",
            title="Scout",
            icon="🔎",
        ),
        st.Page(
            "pages/analyse.py",
            title="Analyse",
            icon="📊",
        ),
        st.Page(
            "pages/research.py",
            title="Research",
            icon="📚",
        ),
        st.Page(
            "pages/systemstatus.py",
            title="Systemstatus",
            icon="🩺",
        ),
    ],
}

navigation = st.navigation(pages)

st.markdown(
    """
    <style>
    /* Kompakte InRA-Navigation */
    [data-testid="stSidebar"] {
        width: 180px !important;
        min-width: 180px !important;
        max-width: 180px !important;

        background-color: #050b14;
        background-image:
            radial-gradient(
                circle,
                rgba(32, 112, 230, 0.42) 1px,
                transparent 1.3px
            ),
            radial-gradient(
                circle,
                rgba(22, 83, 170, 0.28) 0.7px,
                transparent 1px
            );
        background-size:
            24px 24px,
            18px 18px;
        background-position:
            2px 5px,
            0 0;
    }

    [data-testid="stSidebar"] > div:first-child {
        width: 180px !important;
    }

    [data-testid="stSidebarContent"] {
        width: 180px !important;
    }

    /* Etwas kompaktere Innenabstände */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.65rem;
    }

    [data-testid="stSidebar"] .st-emotion-cache-1cypcdb {
        padding-left: 1rem;
        padding-right: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title(APP_NAME)
st.sidebar.caption(APP_SUBTITLE)
st.sidebar.caption("Version 0.1")

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