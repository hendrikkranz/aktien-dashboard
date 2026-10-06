import pandas as pd
import streamlit as st

from utils.market_data import load_price_history
from utils.radar_store import load_radar, remove_from_radar


st.title("📡 Radar")
st.caption(
    "Beobachtung interessanter Aktien ab einem selbst gewählten Zeitpunkt"
)

radar = load_radar()

radar_table_state = st.session_state.get("radar_table")

if radar_table_state:
    selected_rows = radar_table_state.get("selection", {}).get("rows", [])

    if selected_rows:
        selected_row = selected_rows[0]

        if 0 <= selected_row < len(radar):
            selected_ticker = str(
                radar.iloc[selected_row]["Ticker"]
            ).strip()

            st.session_state["analyse_ticker"] = selected_ticker
            st.switch_page("pages/analyse.py")

if radar.empty:
    st.info(
        "Noch keine Aktien auf dem Radar. "
        "Aktien können direkt aus der Analyse hinzugefügt werden."
    )
    st.stop()


rows = []

with st.spinner("Radar-Kurse werden aktualisiert …"):
    for _, item in radar.iterrows():
        ticker = str(item["Ticker"]).strip()
        reference_price = pd.to_numeric(
            item["Referenzkurs"],
            errors="coerce",
        )

        history = load_price_history(
            ticker,
            period="5d",
        )

        current_price = None

        if not history.empty:
            current_price = float(
                history.iloc[-1]["Schlusskurs"]
            )

        performance = None

        if (
            current_price is not None
            and pd.notna(reference_price)
            and reference_price > 0
        ):
            performance = (
                current_price / reference_price - 1
            ) * 100

        recorded_at = pd.to_datetime(
            item["Aufgenommen am"],
            errors="coerce",
        )

        rows.append(
            {
                "Name": item["Name"],
                "Ticker": ticker,
                "Aufgenommen": (
                    recorded_at.strftime("%d.%m.%Y")
                    if pd.notna(recorded_at)
                    else "—"
                ),
                "Referenzkurs": reference_price,
                "Aktueller Kurs": current_price,
                "Seit Aufnahme": performance,
            }
        )


display = pd.DataFrame(rows)

display["Referenzkurs"] = display["Referenzkurs"].apply(
    lambda value: f"{value:.2f}"
    if pd.notna(value)
    else "—"
)

display["Aktueller Kurs"] = display["Aktueller Kurs"].apply(
    lambda value: f"{value:.2f}"
    if pd.notna(value)
    else "—"
)

display["Seit Aufnahme"] = display["Seit Aufnahme"].apply(
    lambda value: f"{value:+.1f} %"
    if pd.notna(value)
    else "—"
)

table_state = st.dataframe(
    display,
    key="radar_table",
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "Name": st.column_config.TextColumn(
            "Aktie",
            width="large",
        ),
        "Ticker": st.column_config.TextColumn(
            "Ticker",
            width="small",
        ),
        "Aufgenommen": st.column_config.TextColumn(
            "Aufgenommen",
            width="small",
        ),
        "Referenzkurs": st.column_config.TextColumn(
            "Referenzkurs",
        ),
        "Aktueller Kurs": st.column_config.TextColumn(
            "Aktueller Kurs",
        ),
        "Seit Aufnahme": st.column_config.TextColumn(
            "Seit Aufnahme",
        ),
    },
)

selected_rows = table_state.selection.rows

if selected_rows:
    selected_ticker = display.iloc[
        selected_rows[0]
    ]["Ticker"]

    st.session_state["analyse_ticker"] = selected_ticker
    st.switch_page("pages/analyse.py")

st.divider()

remove_col, button_col = st.columns(
    [3, 1],
    vertical_alignment="bottom",
)

with remove_col:
    remove_ticker = st.selectbox(
        "Aktie vom Radar entfernen",
        options=display["Ticker"].tolist(),
        format_func=lambda ticker: (
            f"{display.loc[display['Ticker'] == ticker, 'Name'].iloc[0]}"
            f" ({ticker})"
        ),
        key="radar_remove_ticker",
    )

with button_col:
    if st.button(
        "Vom Radar entfernen",
        use_container_width=True,
        key="remove_from_radar",
    ):
        if remove_from_radar(remove_ticker):
            st.rerun()

