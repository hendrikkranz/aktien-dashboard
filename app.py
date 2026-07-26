import streamlit as st


st.set_page_config(
    page_title="Mein Aktien-Dashboard",
    page_icon="📈",
    layout="wide",
)


seiten = {
    "📁 Meine Listen": [
        st.Page(
            "pages/depot.py",
            title="Depotaktien",
            icon="💼",
            default=False,
        ),
        st.Page(
            "pages/dauergewinner.py",
            title="Dauergewinner",
            icon="🏆",
            default=True,
        ),
        st.Page(
            "pages/dividendenaktien.py",
            title="Dividendenaktien",
            icon="💰",
            default=False,
        ),
    ]
}

navigation = st.navigation(seiten)
navigation.run()