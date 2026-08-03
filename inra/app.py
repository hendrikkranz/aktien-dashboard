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
            title="Start",
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
    ],
}

navigation = st.navigation(pages)

st.sidebar.title(APP_NAME)
st.sidebar.caption(APP_SUBTITLE)
st.sidebar.caption("Version 0.1")

navigation.run()