import streamlit as st

from config.settings import APP_NAME, APP_SUBTITLE


st.title(APP_NAME)
st.caption(APP_SUBTITLE)

st.markdown("## Willkommen bei InRA")

st.write(
    """
InRA unterstützt dich dabei, hochwertige Unternehmen zu finden,
Kaufchancen zu bewerten und Investmententscheidungen schneller
und nachvollziehbarer zu treffen.
"""
)

st.markdown("### Schnellstart")

col1, col2 = st.columns(2)

with col1:
    if st.button(
        "🔎 Scout öffnen",
        use_container_width=True,
        type="primary",
    ):
        st.switch_page("pages/scout.py")

with col2:
    if st.button(
        "📊 Analyse öffnen",
        use_container_width=True,
    ):
        st.switch_page("pages/analyse.py")

st.divider()

st.info(
    "💡 Tipp: Starte im Scout, suche eine Aktie und öffne sie anschließend direkt in der Analyse."
)