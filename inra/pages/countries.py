import streamlit as st

from components.country_germany import (
    render_canada,
    render_france,
    render_germany,
    render_japan,
    render_netherlands,
    render_nordics,
    render_spain,
    render_italy,
    render_rest_of_world,
    render_switzerland,
    render_uk,
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
# Großbritannien
# ------------------------------------------------------------------

elif country == "uk":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_uk()


# ------------------------------------------------------------------
# Japan
# ------------------------------------------------------------------

elif country == "japan":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_japan()


# ------------------------------------------------------------------
# Niederlande
# ------------------------------------------------------------------

elif country == "netherlands":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_netherlands()


# ------------------------------------------------------------------
# Skandinavien
# ------------------------------------------------------------------

elif country == "nordics":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_nordics()


# ------------------------------------------------------------------
# Kanada
# ------------------------------------------------------------------

elif country == "canada":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_canada()


# ------------------------------------------------------------------
# Spanien
# ------------------------------------------------------------------

elif country == "spain":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_spain()


# ------------------------------------------------------------------
# Italien
# ------------------------------------------------------------------

elif country == "italy":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_italy()


# ------------------------------------------------------------------
# Weitere Märkte
# ------------------------------------------------------------------

elif country == "rest_of_world":
    if st.button("← Länder & Märkte"):
        st.session_state["country_market_view"] = "overview"
        st.rerun()

    render_rest_of_world()


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
                "Öffnen",
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
                "Öffnen",
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
                "Öffnen",
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
            if st.button(
                "Öffnen",
                use_container_width=True,
                key="open_uk",
            ):
                st.session_state[
                    "country_market_view"
                ] = "uk"
                st.rerun()

    with row_2[1]:
        with st.container(border=True):
            st.markdown("### 🇨🇭 Schweiz")
            st.caption("SMI")
            if st.button(
                "Öffnen",
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
            if st.button(
                "Öffnen",
                use_container_width=True,
                key="open_japan",
            ):
                st.session_state[
                    "country_market_view"
                ] = "japan"
                st.rerun()


    row_3 = st.columns(3)

    with row_3[0]:
        with st.container(border=True):
            st.markdown("### 🇳🇱 Niederlande")
            st.caption("AEX")
            if st.button(
                "Öffnen",
                use_container_width=True,
                key="open_netherlands",
            ):
                st.session_state[
                    "country_market_view"
                ] = "netherlands"
                st.rerun()


    with row_3[1]:
        with st.container(border=True):
            st.markdown("### 🇸🇪 🇩🇰 🇫🇮 🇳🇴 Nordics")
            st.caption("NASDAQ OMX Nordic 120")
            if st.button(
                "Öffnen",
                use_container_width=True,
                key="open_nordics",
            ):
                st.session_state[
                    "country_market_view"
                ] = "nordics"
                st.rerun()


    with row_3[2]:
        with st.container(border=True):
            st.markdown("### 🇨🇦 Kanada")
            st.caption("S&P/TSX 60")
            if st.button(
                "Öffnen",
                use_container_width=True,
                key="open_canada",
            ):
                st.session_state[
                    "country_market_view"
                ] = "canada"
                st.rerun()


    row_4 = st.columns(3)

    with row_4[0]:
        with st.container(border=True):
            st.markdown("### 🇪🇸 Spanien")
            st.caption("IBEX 35")
            if st.button(
                "Öffnen",
                use_container_width=True,
                key="open_spain",
            ):
                st.session_state[
                    "country_market_view"
                ] = "spain"
                st.rerun()


    with row_4[1]:
        with st.container(border=True):
            st.markdown("### 🇮🇹 Italien")
            st.caption("FTSE MIB")
            if st.button(
                "Öffnen",
                use_container_width=True,
                key="open_italy",
            ):
                st.session_state[
                    "country_market_view"
                ] = "italy"
                st.rerun()


    with row_4[2]:
        with st.container(border=True):
            st.markdown("### 🌍 Weitere Märkte")
            st.caption("108 global relevante Unternehmen")
            if st.button(
                "Öffnen",
                use_container_width=True,
                key="open_rest_of_world",
            ):
                st.session_state[
                    "country_market_view"
                ] = "rest_of_world"
                st.rerun()
