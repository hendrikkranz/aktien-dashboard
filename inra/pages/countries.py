import streamlit as st

from components.country_germany import (
    render_france,
    render_germany,
    render_switzerland,
    render_usa,
)


st.title("Länder & Märkte")
st.caption(
    "Internationale Aktienmärkte, Leitindizes und Indexmitglieder"
)

country = st.session_state.get(
    "country_market_view",
    "overview",
)


# ------------------------------------------------------------------
# Deutschland
# ------------------------------------------------------------------

if country == "germany":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_germany()


# ------------------------------------------------------------------
# USA
# ------------------------------------------------------------------

elif country == "usa":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_usa()


# ------------------------------------------------------------------
# Frankreich
# ------------------------------------------------------------------

elif country == "france":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_france()


# ------------------------------------------------------------------
# Schweiz
# ------------------------------------------------------------------

elif country == "switzerland":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_switzerland()


# ------------------------------------------------------------------
# Länderübersicht
# ------------------------------------------------------------------

else:
    row_1 = st.columns(3)

    with row_1[0]:
        with st.container(border=True):
            st.markdown("### 🇩🇪 Deutschland")
            st.caption("DAX · MDAX · SDAX")

            if st.button(
                "Deutschland öffnen",
                use_container_width=True,
                key="open_germany",
            ):
                st.session_state[
                    "country_market_view"
                ] = "germany"
                st.rerun()

    with row_1[1]:
        with st.container(border=True):
            st.markdown("### 🇺🇸 USA")
            st.caption("Dow Jones · Nasdaq 100")
            if st.button(
                "USA öffnen",
                use_container_width=True,
                key="open_usa",
            ):
                st.session_state[
                    "country_market_view"
                ] = "usa"
                st.rerun()

    with row_1[2]:
        with st.container(border=True):
            st.markdown("### 🇫🇷 Frankreich")
            st.caption("CAC 40")
            if st.button(
                "Frankreich öffnen",
                use_container_width=True,
                key="open_france",
            ):
                st.session_state[
                    "country_market_view"
                ] = "france"
                st.rerun()

    row_2 = st.columns(3)

    with row_2[0]:
        with st.container(border=True):
            st.markdown("### 🇬🇧 Großbritannien")
            st.caption("FTSE 100")
            st.button(
                "Noch nicht verfügbar",
                use_container_width=True,
                disabled=True,
                key="open_uk",
            )

    with row_2[1]:
        with st.container(border=True):
            st.markdown("### 🇨🇭 Schweiz")
            st.caption("SMI")
            if st.button(
                "Schweiz öffnen",
                use_container_width=True,
                key="open_switzerland",
            ):
                st.session_state[
                    "country_market_view"
                ] = "switzerland"
                st.rerun()

    with row_2[2]:
        with st.container(border=True):
            st.markdown("### 🇯🇵 Japan")
            st.caption("Nikkei 225")
            st.button(
                "Noch nicht verfügbar",
                use_container_width=True,
                disabled=True,
                key="open_japan",
            )
