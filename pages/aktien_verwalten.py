from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf


DATA_PATH = Path("data/aktien_universum.csv")



st.title("⚙️ Aktien verwalten")
st.caption(
    "Hier verwaltest du das Research-Universum. "
    "Depotdaten wie Kaufkurs, Stückzahl oder Gewichtung werden nicht verwendet."
)


@st.cache_data
def load_universe() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame(
            columns=[
                "Name",
                "Ticker",
                "Sektor",
                "Branche",
                "Dauergewinner",
                "Dividenden",
            ]
        )

    df = pd.read_csv(
        DATA_PATH,
        sep=";",
        dtype={
            "Name": "string",
            "Ticker": "string",
        },
    )
    for column in ["Sektor", "Branche"]:
        if column not in df.columns:
            df[column] = ""

        df[column] = (
            df[column]
            .astype("string")
            .fillna("")
            .str.strip()
        )
    for column in ["Dauergewinner", "Dividenden"]:
        if column not in df.columns:
            df[column] = False

        df[column] = (
            df[column]
            .astype(str)
            .str.strip()
            .str.lower()
            .map(
                {
                    "true": True,
                    "false": False,
                    "1": True,
                    "0": False,
                    "yes": True,
                    "no": False,
                }
            )
            .fillna(False)
            .astype(bool)
        )

    return df[
        [
            "Name",
            "Ticker",
            "Sektor",
            "Branche",
            "Dauergewinner",
            "Dividenden",
        ]
    ]


def save_universe(df: pd.DataFrame) -> None:
    cleaned = df.copy()

    cleaned["Name"] = (
        cleaned["Name"]
        .astype("string")
        .fillna("")
        .str.strip()
    )

    cleaned["Ticker"] = (
        cleaned["Ticker"]
        .astype("string")
        .fillna("")
        .str.strip()
        .str.upper()
    )
    for column in ["Sektor", "Branche"]:
        cleaned[column] = (
            cleaned[column]
            .astype("string")
            .fillna("")
            .str.strip()
        )
    cleaned = cleaned[cleaned["Ticker"] != ""]

    cleaned = cleaned.drop_duplicates(
        subset=["Ticker"],
        keep="last",
    )

    cleaned = cleaned.sort_values(
        by=["Name", "Ticker"],
        na_position="last",
    ).reset_index(drop=True)

    cleaned.to_csv(
        DATA_PATH,
        sep=";",
        index=False,
    )


def lookup_company_info(ticker: str) -> dict:
    ticker_data = yf.Ticker(ticker)

    try:
        info = ticker_data.get_info()
    except Exception:
        info = {}

    return {
        "Name": (
            info.get("longName")
            or info.get("shortName")
            or ticker
        ),
        "Sektor": info.get("sector") or "",
        "Branche": info.get("industry") or "",
    }

universe_df = load_universe()
with st.container(border=True):
    st.subheader("Aktie hinzufügen")

    ticker_input = st.text_input(
        "Yahoo-Finance-Ticker",
        placeholder="z. B. MSFT, SAP.DE oder NESN.SW",
    )

    col1, col2 = st.columns(2)

    with col1:
        add_as_dauergewinner = st.checkbox(
            "Dauergewinner",
            value=True,
        )

    with col2:
        add_as_dividend = st.checkbox(
            "Dividendenaktie",
            value=False,
        )

    add_clicked = st.button(
        "➕ Aktie hinzufügen",
        type="primary",
    )

    if add_clicked:
        ticker = ticker_input.strip().upper()

        if not ticker:
            st.warning("Bitte zuerst einen Ticker eingeben.")

        elif ticker in universe_df["Ticker"].astype(str).str.upper().values:
            st.warning(f"{ticker} ist bereits im Aktienuniversum enthalten.")

        else:
            with st.spinner(f"{ticker} wird geprüft …"):
                company = lookup_company_info(ticker)

            new_row = pd.DataFrame(
                [
                    {
                        "Name": company["Name"],
                        "Ticker": ticker,
                        "Sektor": company["Sektor"],
                        "Branche": company["Branche"],
                        "Dauergewinner": add_as_dauergewinner,
                        "Dividenden": add_as_dividend,
                    }
                ]
            )

            updated_df = pd.concat(
                [universe_df, new_row],
                ignore_index=True,
            )

            save_universe(updated_df)
            st.cache_data.clear()

            st.success(f'{company["Name"]} ({ticker}) wurde hinzugefügt.')
            st.rerun()


st.subheader("Aktienuniversum")
edited_df = st.data_editor(
    universe_df,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    column_config={
        "Name": st.column_config.TextColumn(
            "Name",
            width="large",
        ),
        "Ticker": st.column_config.TextColumn(
            "Ticker",
            required=True,
            width="medium",
        ),
        "Sektor": st.column_config.TextColumn(
            "Sektor",
            width="medium",
        ),
        "Branche": st.column_config.TextColumn(
            "Branche",
            width="large",
        ),
        "Dauergewinner": st.column_config.CheckboxColumn(
            "Dauergewinner",
        ),
        "Dividenden": st.column_config.CheckboxColumn(
            "Dividendenaktie",
        ),
},
key="aktien_universum_editor_v4",
)
st.caption(
    "Zum Löschen eine Zeile markieren und über das Papierkorb-Symbol entfernen."
)

if st.button(
    "💾 Änderungen speichern",
    type="primary",
):
    try:
        save_universe(edited_df)
        st.cache_data.clear()
        st.success("Änderungen wurden gespeichert.")
        st.rerun()

    except Exception as error:
        st.error(f"Speichern fehlgeschlagen: {error}")
