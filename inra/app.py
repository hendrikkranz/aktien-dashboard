import streamlit as st

from config.settings import APP_NAME, APP_SUBTITLE

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📈",
    layout="wide",
)

st.title(APP_NAME)
st.caption(APP_SUBTITLE)

st.write("Version 0.1")